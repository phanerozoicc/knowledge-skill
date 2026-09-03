"""单写者调度循环。

这是唯一会变更预留表和车队状态的组件。其他一切(规划器、观察者)都只读
不可变快照。循环一次跑一个 :meth:`tick`;每个 tick 是一条简短、确定性的
流水线:

1. 时钟推进 ``dt``。
2. 摄入自上次 tick 以来排队积累的车辆上报(位置 + 心跳)和确认通知
   (「我已离开资源 R」)。
3. 检测离线智能体(心跳比 ``heartbeat_timeout`` 更旧),释放它们的预留。
4. 清理过期预留(超时未确认或租约过期);计划被部分清理的智能体被标记为
   需要重规划。
5. 对每个需要(重新)规划的智能体——新分配、落后于计划、或之前失败——按
   优先级顺序重规划,**每个智能体拍一张新快照**,使每个低优先级搜索都能
   看到刚刚落地的高优先级提交。接纳的计划先回滚该智能体的旧计划再提交。

「每个智能体重拍快照」这一步,正是让优先级规划在单写者模型下保持正确的
关键:规划读的是冻结视图,提交落在 live 表上,下一个智能体的快照能看到它。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .metrics import MetricsSnapshot
from .models import Reservation, Vehicle, VehicleState
from .planner import Planner, PlanResult
from .reservation_table import ReservationTable
from .snapshot import Graph, Snapshot


# --------------------------------------------------------------------------- #
# 上报(由仿真/真实通信层产生,由循环消费)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class PositionReport:
    """车辆说:「时刻 t 我在节点 X」。"""
    vid: str
    node: str
    t: float


@dataclass(frozen=True, slots=True)
class Confirmation:
    """车辆说:「我已离开资源 R」(节点或边键)。"""
    vid: str
    resource_key: str


@dataclass(frozen=True, slots=True)
class TickResult:
    clock: float
    metrics: MetricsSnapshot
    offline: tuple[str, ...]
    reaped_agents: tuple[str, ...]
    replanned: tuple[str, ...]
    plan_failures: tuple[str, ...]
    committed: tuple[str, ...]


# --------------------------------------------------------------------------- #
# 循环
# --------------------------------------------------------------------------- #
@dataclass
class SchedulerConfig:
    dt: float = 1.0
    plan_horizon: float = 60.0
    heartbeat_timeout: float = 6.0
    time_step: float = 1.0          # 规划器 wait 动作的粒度
    node_dwell: float = 1.0         # 到达后节点被视为占用的时长
    slip_threshold: float = 3.0     # 落后于计划多少秒后触发重规划


class SchedulerLoop:
    def __init__(
        self,
        graph: Graph,
        table: ReservationTable | None = None,
        config: SchedulerConfig | None = None,
    ) -> None:
        self.graph = graph
        self.table = table or ReservationTable()
        self.config = config or SchedulerConfig()
        self.clock: float = 0.0
        self.fleet: dict[str, Vehicle] = {}
        # 每个智能体当前已提交的 rid(重规划时用来回滚)
        self.active_rids: dict[str, list[int]] = {}
        # 每个智能体当前正在奔赴的目标
        self.goals: dict[str, str] = {}

    # ------------------------------------------------------------------ #
    # 车队管理
    # ------------------------------------------------------------------ #
    def add_vehicle(self, v: Vehicle) -> None:
        self.fleet[v.vid] = v
        if v.goal is not None:
            self.goals[v.vid] = v.goal

    def assign_goal(self, vid: str, goal: str) -> None:
        self.goals[vid] = goal
        # 标记下个 tick 需要规划
        self.fleet[vid] = self.fleet[vid].with_state(state=VehicleState.IDLE)

    # ------------------------------------------------------------------ #
    # tick
    # ------------------------------------------------------------------ #
    def tick(
        self,
        position_reports: Iterable[PositionReport] = (),
        confirmations: Iterable[Confirmation] = (),
    ) -> TickResult:
        cfg = self.config
        self.clock += cfg.dt

        # 2. 摄入上报 + 确认。
        reported_nodes: dict[str, str] = {}
        for rep in position_reports:
            v = self.fleet.get(rep.vid)
            if v is None:
                continue
            self.fleet[rep.vid] = v.with_state(
                node=rep.node, last_heartbeat=rep.t,
                state=VehicleState.EXECUTING if self.goals.get(rep.vid) else VehicleState.IDLE,
            )
            reported_nodes[rep.vid] = rep.node
        for conf in confirmations:
            self.table.confirm_passed(conf.vid, conf.resource_key, now=self.clock)

        # 3. 离线检测。
        offline: list[str] = []
        for vid, v in self.fleet.items():
            if v.state is VehicleState.OFFLINE:
                continue
            if v.last_heartbeat >= 0 and self.clock - v.last_heartbeat > cfg.heartbeat_timeout:
                self.table.release_agent(vid)
                self.fleet[vid] = v.with_state(state=VehicleState.OFFLINE)
                self.active_rids.pop(vid, None)
                offline.append(vid)

        # 4. 清理过期预留。
        reaped = self.table.expire_stale(now=self.clock)
        reaped_set = set(reaped)

        # 5. 决定谁需要(重新)规划。
        # 💡 学习点(对应课程 L3-02 滚动重规划):不是每 tick 全员重算,
        # 只重算"dirty"的车——这样把昂贵的规划成本控制住。dirty 触发条件:
        #   ① 预留被租约清理过(出问题)→ 必须重算
        #   ② 有目标但当前没有有效计划(新任务 / 计划失效)→ 必须算
        # 其余正常执行的车不动它们的计划(稳定性)。
        dirty: list[str] = []
        for vid, v in self.fleet.items():
            if v.state is VehicleState.OFFLINE:
                continue
            if vid in reaped_set:
                dirty.append(vid)
                continue
            if vid in self.goals and vid not in self.active_rids:
                dirty.append(vid)
        # 💡 优先级排序是 prioritized planning 的关键:高优先级先规划、先
        # commit,低优先级规划时就会"看到"高优先级的预留而主动避让。
        # 后端类比:这就是 QoS——VIP 请求先调度,普通请求让路。
        dirty.sort(key=lambda vid: (-self.fleet[vid].priority, vid))

        replanned: list[str] = []
        plan_failures: list[str] = []
        committed: list[str] = []
        for vid in dirty:
            v = self.fleet[vid]
            goal = self.goals.get(vid)
            if goal is None:
                continue
            # 重规划前先回滚该智能体之前的计划。
            # 💡 重规划前先撤销旧计划:否则新旧两份预留会同时占着时空,既
            # 浪费又会让自己的新轨迹"和自己的旧轨迹冲突"。
            if vid in self.active_rids:
                self.table.rollback(self.active_rids.pop(vid))
            # 拍新快照,让这次搜索能看到更高优先级的提交。
            # 🔑 关键:每辆车规划前重新拍快照。因为上一辆(更高优先级)刚
            # commit 了它的预留,这辆车必须看到那个新状态才能正确避让。
            # 如果所有车共用一个旧快照,它们会"各自以为某时空空闲"而撞车。
            snap = self._snapshot()
            planner = Planner(snap, time_step=cfg.time_step, node_dwell=cfg.node_dwell)
            self.fleet[vid] = v.with_state(state=VehicleState.PLANNING)
            result: PlanResult = planner.plan(self.fleet[vid], goal)
            if result.trajectory is None:
                # 💡 规划失败通常意味着"暂时被堵死"——标 WAITING,下 tick 再试。
                # 不要无限重试消耗 CPU(demo 里低优先级车就是这样等待的)。
                plan_failures.append(vid)
                self.fleet[vid] = self.fleet[vid].with_state(state=VehicleState.WAITING)
                continue
            commit = self.table.reserve_batch(result.proposed, now=self.clock)
            if not commit.ok:
                # 💡 理论上规划时已查冲突,commit 不该再失败——这里是个安全网:
                # 极少数情况下(浮点边界、并发)规划阶段和 commit 之间状态变了。
                plan_failures.append(vid)
                self.fleet[vid] = self.fleet[vid].with_state(state=VehicleState.WAITING)
                continue
            self.active_rids[vid] = list(commit.rids)
            self.fleet[vid] = self.fleet[vid].with_state(state=VehicleState.EXECUTING)
            self.table.metrics.replans_triggered += 1
            replanned.append(vid)
            committed.append(vid)

        # 到达目标了?丢掉目标,释放该智能体。
        for vid in list(self.goals):
            v = self.fleet[vid]
            if v.node == self.goals[vid] and vid not in dirty:
                self.goals.pop(vid, None)
                self.table.rollback(self.active_rids.pop(vid, []))
                self.fleet[vid] = v.with_state(state=VehicleState.IDLE, goal=None)

        return TickResult(
            clock=self.clock,
            metrics=self.table.metrics.snapshot(self.table.active_count()),
            offline=tuple(offline),
            reaped_agents=tuple(reaped),
            replanned=tuple(replanned),
            plan_failures=tuple(plan_failures),
            committed=tuple(committed),
        )

    # ------------------------------------------------------------------ #
    def _snapshot(self) -> Snapshot:
        return Snapshot(
            clock=self.clock,
            graph=self.graph,
            fleet=dict(self.fleet),
            reservations=self.table.snapshot_index(),
            metrics=self.table.metrics.snapshot(self.table.active_count()),
            plan_horizon=self.config.plan_horizon,
        )

    def snapshot(self) -> Snapshot:
        """给观察者/测试用的公开只读快照。"""
        return self._snapshot()
