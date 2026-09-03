"""已提交预留的区间索引,每个资源一棵区间树。

封装 :mod:`intervaltree`,使上层代码不直接碰该库。两个职责:

1. **快速重叠查询** —— O(log n + k),取代玩具版的 O(n) 扫描。
2. **反向(对向)检测** —— 查询边 A->B 时,额外查反向桶 B->A,因为反向边
   的同时占用是迎面冲突,即便它们名义上是「不同资源」。

索引把已提交的 :class:`~scheduler.models.Reservation` 对象作为区间负载存储。
删除时按 ``rid``(预留 id)精确删除,避免误删碰巧同边界的无关区间。
"""

from __future__ import annotations

from intervaltree import IntervalTree

from .models import Conflict, ConflictType, EdgeId, Reservation, ResourceKind


class IntervalIndex:
    """按资源字符串键分桶的区间树集合。"""

    def __init__(self) -> None:
        self._buckets: dict[str, IntervalTree] = {}

    # ------------------------------------------------------------------ #
    # 变更(只由 ReservationTable 这个唯一写者调用)
    # ------------------------------------------------------------------ #
    def add(self, res: Reservation) -> None:
        tree = self._buckets.setdefault(res.resource_key, IntervalTree())
        # intervaltree 的区间是半开 [begin, end),与我们的模型一致。
        tree.addi(res.t_start, res.t_end, res)

    def remove(self, res: Reservation) -> None:
        tree = self._buckets.get(res.resource_key)
        if tree is None:
            return
        # 精确删除 payload 的 rid 相同的那个区间。
        for iv in tree.copy():
            if iv.data.rid == res.rid:
                tree.discard(iv)
                break

    def copy(self) -> "IntervalIndex":
        """深拷贝(每棵 IntervalTree 都 copy;payload 是冻结的 Reservation,
        可安全共享)。用于快照。"""
        clone = IntervalIndex()
        for key, tree in self._buckets.items():
            clone._buckets[key] = tree.copy()
        return clone

    def clear(self) -> None:
        self._buckets.clear()

    # ------------------------------------------------------------------ #
    # 查询
    # ------------------------------------------------------------------ #
    def overlaps(self, res: Reservation) -> list[Conflict]:
        """返回候选预留 ``res`` 会造成的所有冲突。

        冲突规则:
        - NODE:同节点桶上的任何重叠都是 VERTEX(顶点)冲突。
        - EDGE(同向):同边桶上的重叠是 EDGE 冲突。若重叠的已有预留属于
          不同智能体、且候选区间起始更晚,则报告为 FOLLOWING(候选会追上)。
        - EDGE(反向):反向边桶上的重叠是 SWAPPING(迎面)冲突。
        """
        conflicts: list[Conflict] = []
        # 💡 学习点(对应课程 L2-02):冲突检测分三类,对应三种"撞车方式"。
        # 关键认知:边是"有向"的——A->B 和 B->A 是两个不同资源。
        # 这正是能检测对向冲突的关键:如果边是无向的,就分不出相向还是同向。

        if res.kind is ResourceKind.NODE:
            # 节点冲突最简单:同一节点同一时间段被占 = VERTEX(顶点冲突)。
            # 后端类比:两个事务同时写同一行。
            for existing in self._members(res.resource_key):
                if existing.overlaps_time(res.t_start, res.t_end):
                    conflicts.append(
                        Conflict(ConflictType.VERTEX, res, existing)
                    )
            return conflicts

        # EDGE —— 同向边
        assert res.edge is not None
        same_dir_key = res.resource_key
        for existing in self._members(same_dir_key):
            if not existing.overlaps_time(res.t_start, res.t_end):
                continue
            if existing.edge is None:
                continue
            # 同向边重叠。分类:候选追赶更早出发的智能体则是 FOLLOWING;
            # 否则是普通 EDGE 重叠。
            # 💡 FOLLOWING(跟随冲突):同方向,候选车晚出发但时间窗重叠
            # → 后车会追上前车。判断线索:t_start 更晚。
            if (
                existing.agent_id != res.agent_id
                and res.t_start >= existing.t_start
            ):
                conflicts.append(
                    Conflict(ConflictType.FOLLOWING, res, existing)
                )
            else:
                conflicts.append(
                    Conflict(ConflictType.EDGE, res, existing)
                )
        # 反向 → 迎面 / 对向。
        # 💡 SWAPPING(对向/交换冲突):查"反向边"的桶。如果 A->B 和 B->A
        # 同时被占,两车会在边中间迎面相撞或卡死。这是 L2-02 讲的"边冲突"
        # 的核心,也是为什么工业上常用单行道设计来根治这类冲突。
        rev_key = f"edge:{res.edge.reversed}"
        for existing in self._members(rev_key):
            if existing.overlaps_time(res.t_start, res.t_end):
                conflicts.append(
                    Conflict(ConflictType.SWAPPING, res, existing)
                )
        return conflicts

    def members_on(self, resource_key: str) -> list[Reservation]:
        return list(self._members(resource_key))

    def all_reservations(self) -> list[Reservation]:
        out: list[Reservation] = []
        for tree in self._buckets.values():
            out.extend(iv.data for iv in tree)
        return out

    def __len__(self) -> int:
        return sum(len(tree) for tree in self._buckets.values())

    # ------------------------------------------------------------------ #
    def _members(self, key: str):
        tree = self._buckets.get(key)
        return (iv.data for iv in tree) if tree else ()
