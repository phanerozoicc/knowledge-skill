"""预留表:调度系统的单一事实源,记录「谁可以在何时占用哪个资源」。

这是热路径里唯一的可变、非快照对象,只由调度循环(唯一写者)触碰。
所有公开的变更操作对该单线程都是原子的:

- :meth:`reserve_batch` 是事务性提交。要么接纳批次里的*全部*预留,要么
  *一个都不*接纳;某个候选冲突会回滚整批,保证表绝不被部分写入污染。
- :meth:`confirm_passed` 在智能体报告「我已通过该资源」后退役该预留——
  这正是让 ``expire_stale`` 能区分「正常完成」和「智能体停滞」的关键。
- :meth:`expire_stale` 清理租约过期、或时间窗已过却未确认的预留,并报告
  受影响的智能体,供循环重新规划。
- :meth:`release_agent` 丢弃某智能体仍持有的全部预留,用于离线/故障切换。

每次变更都返回足够的信息,供循环更新指标、驱动滚动重规划。本模块不做
I/O,也不读墙钟。
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from itertools import count
from typing import Iterable

from .interval_index import IntervalIndex
from .metrics import Metrics
from .models import (
    Conflict,
    ConflictType,
    EdgeId,
    NodeId,
    Reservation,
    ResourceKind,
    Vehicle,
)


# 计算租约截止时刻时,在 t_end 上加的默认安全余量。
DEFAULT_LEASE_MARGIN = 5.0


@dataclass(frozen=True, slots=True)
class CommitResult:
    """批次提交尝试的结果。"""
    ok: bool
    committed: tuple[Reservation, ...]   # with rids assigned, if ok
    conflicts: tuple[Conflict, ...]      # non-empty if not ok
    # When ok, the rids that were assigned — used by release/rollback.
    rids: tuple[int, ...] = ()


class ReservationTable:
    """单写者预留存储。

    ``lease_margin`` 是计算租约截止时刻时,加到预留结束时刻上的默认余量
    (秒),除非调用方显式指定。
    """

    def __init__(self, lease_margin: float = DEFAULT_LEASE_MARGIN) -> None:
        self._index = IntervalIndex()
        self._by_rid: dict[int, Reservation] = {}
        self._rid_seq = count(1)
        self._lease_margin = lease_margin
        self.metrics = Metrics()

    # ------------------------------------------------------------------ #
    # 内省(查询)
    # ------------------------------------------------------------------ #
    def __len__(self) -> int:
        return len(self._index)

    def active_count(self) -> int:
        return len(self._index)

    def all_reservations(self) -> list[Reservation]:
        return self._index.all_reservations()

    def reservations_for(self, agent_id: str) -> list[Reservation]:
        return [r for r in self._index.all_reservations() if r.agent_id == agent_id]

    def conflicts_for(self, candidate: Reservation) -> list[Conflict]:
        """如果现在尝试插入 ``candidate`` 会怎样?纯查询,不改状态。规划器
        用它把候选轨迹对着当前表检查一遍。"""
        return self._index.overlaps(candidate)

    # ------------------------------------------------------------------ #
    # 事务性提交
    # ------------------------------------------------------------------ #
    def reserve_batch(
        self,
        reservations: Iterable[Reservation],
        *,
        now: float,
    ) -> CommitResult:
        """原子地接纳一批预留。

        算法(在单写者契约下安全):
        1. 物化批次,填入租约截止时刻。
        2. 把每个候选对着索引检查,*同时*对着批次里更早的已接受候选检查
           (批内自冲突也算)。
        3. 遇到任何冲突:累加失败指标,直接返回,不写入。
        4. 全部通过:分配 rid,全部插入,累加成功指标。

        「对着批次里更早的已接受候选检查」这一步,是让批次即使在自身两
        个预留本就会冲突时也能保持原子的关键。
        """
        batch = list(reservations)
        self.metrics.reserve_attempts += 1

        # 💡 学习点(对应课程 L2-02):一条轨迹会生成多个预留(每个节点 +
        # 每条边各一个),它们必须"要么全进表,要么一个都不进"——否则部分
        # 写入会污染表,后面所有冲突检测都不可信。这就是事务原子性。
        # 后端类比:这就是数据库事务的 all-or-nothing;不允许多步操作留半截。

        # Fill leases on copies (Reservations are frozen).
        # 🔑 Reservations 是冻结对象,改字段必须用 replace 生成新实例,
        # 不能原地改(否则快照里共享的同一对象会被偷偷改掉,COW 失效)。
        prepared: list[Reservation] = []
        for r in batch:
            lease = r.lease_deadline if r.lease_deadline else r.t_end + self._lease_margin
            prepared.append(replace(r, lease_deadline=lease))

        # Validate against committed state + already-accepted batch members.
        # 💡 两阶段检查:① 和表里已提交的比;② 和本批已接受的比。
        # 第二步不可少——否则同一条轨迹的两个预留(比如同一个节点的两段
        # 占用)会"各自都通过检查"却互相冲突,导致自相矛盾的数据进表。
        accepted: list[Reservation] = []
        recorded_conflicts: list[Conflict] = []
        for cand in prepared:
            conflicts = list(self._index.overlaps(cand))
            # Also check against earlier accepted members of this batch — a
            # batch is atomic, so intra-batch self-collisions must reject it.
            for acc in accepted:
                same_res = acc.resource_key == cand.resource_key
                rev_edge = (
                    cand.kind is ResourceKind.EDGE
                    and acc.kind is ResourceKind.EDGE
                    and cand.edge is not None
                    and acc.edge is not None
                    and cand.edge.reversed == acc.edge
                )
                if same_res and acc.overlaps_time(cand.t_start, cand.t_end):
                    ctype = (
                        ConflictType.FOLLOWING
                        if cand.t_start >= acc.t_start
                        and cand.agent_id != acc.agent_id
                        else ConflictType.EDGE
                    )
                    conflicts.append(Conflict(ctype, cand, acc))
                elif rev_edge and acc.overlaps_time(cand.t_start, cand.t_end):
                    conflicts.append(Conflict(ConflictType.SWAPPING, cand, acc))
            if conflicts:
                recorded_conflicts.extend(conflicts)
                break            # 💡 遇到第一个冲突就停:fail-fast,不必检查剩余
            accepted.append(cand)

        if recorded_conflicts:
            self.metrics.reserve_failed += 1
            self._bump_conflict_metrics(recorded_conflicts)
            # 💡 注意:这里直接返回,什么都没写进表。这就是"整批回滚"——
            # 因为检查阶段只往 accepted 这个临时列表放,从没碰过 self._index。
            # 后端类比:乐观事务的 prepare 阶段失败,commit 阶段不执行。
            return CommitResult(
                ok=False,
                committed=(),
                conflicts=tuple(recorded_conflicts),
            )

        # 提交:分配 rid 并插入。因为对合法区间 index.add 不会失败,所以
        # 不需要「失败时反向 remove」的回滚路径。
        # 💡 这里才真正写表(检查已全部通过)。rid 是预留的唯一身份号,
        # 后面 rollback/release 靠它精确删除,避免误删碰巧同时间段的其他预留。
        committed: list[Reservation] = []
        rids: list[int] = []
        for r in accepted:
            rid = next(self._rid_seq)
            r = replace(r, rid=rid)
            self._index.add(r)
            self._by_rid[rid] = r
            committed.append(r)
            rids.append(rid)
        self.metrics.reserve_success += 1
        self.metrics.tx_committed += 1
        return CommitResult(ok=True, committed=tuple(committed), conflicts=(), rids=tuple(rids))

    # ------------------------------------------------------------------ #
    # 退役:确认 / 过期 / 释放
    # ------------------------------------------------------------------ #
    def confirm_passed(self, agent_id: str, resource_key: str, *, now: float) -> int:
        """智能体报告「我已离开 ``resource_key``」。退役它的预留。

        这是由心跳派生出的确认信号,让我们能区分「正常完成的预留」和
        「停滞的智能体」。返回退役的数量。

        💡 学习点(对应课程 L3-02/L3-04):这是预留表能正确区分"正常完成"
        和"异常停滞"的唯一可靠信号。没有它,调度无法知道某段路是真的
        走完了、还是车卡住了——光看时间判断不出来(这正是开发时踩过的坑)。
        后端类比:这就是消息队列的 ack——消费者处理完要回 ack,否则只能
        靠超时(租约)判断它挂了。
        """
        retired = 0
        for r in list(self._index.members_on(resource_key)):
            if r.agent_id == agent_id:
                self._remove(r)
                retired += 1
        return retired

    def expire_stale(self, *, now: float) -> list[str]:
        """清理**租约**已过期却未确认的预留。

        返回受影响的(去重后的)智能体 id 列表。

        ⚠️ 关键设计(开发时踩过坑,务必理解):只按 ``lease_deadline`` 判失效,
        **绝不**按 ``t_end`` 判。``t_end`` 只是"预期离开时间",车可能因为
        comms 滞后还没上报 confirm。如果按 t_end 判,正常行驶的车会被误清
        → 每 tick 被标 dirty → 每 tick 重规划 → 车永远停在起点不动。
        租约(= t_end + 安全余量)才是真正可靠的"车出问题了"信号。

        为什么 t_end<=now 的残留预留不会误阻未来规划?因为未来候选的时间
        窗 t_start >= now >= 残留的 t_end,半开区间不可能重叠。所以留着它们
        等 confirm 来清是安全的;万一车真挂了,租约兜底清理。
        """
        affected: list[str] = []
        seen: set[str] = set()
        for r in self._index.all_reservations():
            if r.lease_deadline <= now:
                self._remove(r)
                self.metrics.stale_reaped += 1
                if r.agent_id not in seen:
                    seen.add(r.agent_id)
                    affected.append(r.agent_id)
        return affected

    def release_agent(self, agent_id: str) -> int:
        """丢弃 ``agent_id`` 持有的全部预留(离线/故障时用)。返回释放数量。"""
        released = 0
        for r in self.reservations_for(agent_id):
            self._remove(r)
            released += 1
        return released

    def rollback(self, rids: Iterable[int]) -> int:
        """按 rid 撤销一个之前已提交的批次。用于已提交计划被取代(滚动重
        规划)或必须回退的情形。"""
        n = 0
        for rid in rids:
            r = self._by_rid.get(rid)
            if r is not None:
                self._remove(r)
                n += 1
        if n:
            self.metrics.tx_rolled_back += 1
        return n

    # ------------------------------------------------------------------ #
    # 快照支持
    # ------------------------------------------------------------------ #
    def snapshot_index(self) -> IntervalIndex:
        """一个规划线程可读的、近乎冻结的副本;循环可同时变更 live 表。
        payload(Reservation)是冻结的,可安全共享。"""
        return self._index.copy()

    # ------------------------------------------------------------------ #
    # 内部实现
    # ------------------------------------------------------------------ #
    def _remove(self, res: Reservation) -> None:
        self._index.remove(res)
        self._by_rid.pop(res.rid, None)

    def _bump_conflict_metrics(self, conflicts: list[Conflict]) -> None:
        for c in conflicts:
            if c.type is ConflictType.VERTEX:
                self.metrics.conflicts_vertex += 1
            elif c.type is ConflictType.SWAPPING:
                self.metrics.conflicts_swapping += 1
            elif c.type is ConflictType.FOLLOWING:
                self.metrics.conflicts_following += 1
