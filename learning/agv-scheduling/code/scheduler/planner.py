"""时间扩展 A* + 优先级规划。

这是 demo 级规划器(课程 L2 策略):按优先级顺序逐个规划智能体;每个
智能体在一个*时间扩展*图上搜索,状态是 ``(节点, 时间)``,动作要么是
「过边到邻居(到达时刻 t + 通行时间)」,要么是「在当前节点原地等一拍」。
快照里的预留索引充当障碍集:会让某个已预留的(节点/边, 时间)格被占的
动作会被拒绝。

它**不是**全局最优(那是 CBS,课程 L2-04),但它是工业主力:简单、快、
对绝大多数车队「够用」。低优先级智能体会自然让位给高优先级,因为高优先
级的预留已经在快照里了,低优先级规划时就会看到并避开。

正确性要点
----------
- 节点占用持续 ``node_dwell`` 秒(车不是质点;它在路口会占用非零时长)。
  边占用就是该边的通行时间。
- 搜索受 ``horizon`` 约束以保证终止:即使窗口内不存在无冲突路径也只会
  返回 None(→ 调用方可稍后重规划或升级处理)。
- 属于*同一个*智能体的预留被忽略(智能体不会和自己已有的预留冲突)。
"""

from __future__ import annotations

import heapq
import itertools
from dataclasses import dataclass
from typing import Iterable

from .models import (
    EdgeId,
    NodeId,
    Reservation,
    ResourceKind,
    TimedPoint,
    Trajectory,
    Vehicle,
)
from .snapshot import Snapshot


@dataclass(frozen=True, slots=True)
class PlanFailure:
    agent_id: str
    reason: str


@dataclass(frozen=True, slots=True)
class PlanResult:
    """规划单个智能体的结果。trajectory/failure 二者恰有一个被设置。"""
    agent_id: str
    trajectory: Trajectory | None
    failure: PlanFailure | None = None
    # 若该轨迹被提交,*将会*新增的预留。
    proposed: tuple[Reservation, ...] = ()


class Planner:
    """在不可变快照上做时间扩展 A* 的规划器。

    每次规划pass构造一个;持有它要搜索的快照。
    ``time_step`` 是 wait 动作的粒度;``node_dwell`` 是到达后节点被视为占用
    的时长。
    """

    def __init__(
        self,
        snapshot: Snapshot,
        *,
        time_step: float = 1.0,
        node_dwell: float = 1.0,
    ) -> None:
        self.snap = snapshot
        self.time_step = time_step
        self.node_dwell = node_dwell

    # ------------------------------------------------------------------ #
    def plan(self, vehicle: Vehicle, goal: str) -> PlanResult:
        """为 ``vehicle`` 规划一条到 ``goal`` 的无冲突轨迹。"""
        vid = vehicle.vid
        start = vehicle.node
        t0 = self.snap.clock
        horizon = self.snap.plan_horizon

        if not self.snap.graph.has_node(start):
            return PlanResult(vid, None, PlanFailure(vid, f"未知起点 {start}"))
        if not self.snap.graph.has_node(goal):
            return PlanResult(vid, None, PlanFailure(vid, f"未知目标 {goal}"))

        # 💡 学习点(对应课程 L1-04 A* + L2-02 预留表):
        # 这是把 L1-04 的 A* 升级成"时间扩展 A*"——搜索状态从 (节点) 变成
        # (节点, 时间)。每个状态表示"在时刻 t 处于节点 node"。
        # 关键差别:普通 A* 在空间图上找最短路;时间扩展 A* 在"时空图"上找,
        # 避开预留表里已被别人占用的时空格子。这就是单车如何"避让"多车。
        # 后端类比:普通 A* 像静态路由;时间扩展 A* 像带"未来时段占用表"的
        # 路由——会主动避开未来会拥堵的链路。
        start_state = (start, t0)
        counter = itertools.count()   # 让堆在 f 相同时稳定排序,避免比较 tuple 报错
        open_heap: list[tuple[float, int, str, float, tuple[str, float] | None]] = [
            (self._h(start, goal, t0), next(counter), start, t0, None)
        ]
        best_g: dict[tuple[str, float], float] = {start_state: 0.0}
        came_from: dict[tuple[str, float], tuple[tuple[str, float], str | None]] = {}

        goal_state: tuple[str, float] | None = None
        while open_heap:
            f, _, node, t, _ = heapq.heappop(open_heap)
            state = (node, t)
            if best_g.get(state, float("inf")) < f - self._h(node, goal, t):
                continue  # stale heap entry(已有更优路径到达此状态,跳过旧堆项)
            if node == goal:
                goal_state = state
                break
            if t > horizon:
                continue    # 💡 horizon 兜底:保证搜索终止(即使无解也不会无限搜)
            for nxt, travel in self.snap.graph.neighbors(node):
                arrive = t + travel
                if arrive > horizon:
                    continue
                # 💡 核心避让逻辑:为这一步生成候选预留(边 + 到达节点),
                # 查预留表——如果和"别的车"的预留冲突,这条路就走不了。
                # 注意"别的车"这四个字:自己的预留不挡自己(见 _conflicts_others)。
                # Build the candidate reservations for this transition and
                # reject the move if any conflicts an existing reservation
                # that belongs to a *different* agent.
                edge_res = Reservation(
                    vid, ResourceKind.EDGE, edge=EdgeId(node, nxt),
                    t_start=t, t_end=arrive,
                )
                node_res = Reservation(
                    vid, ResourceKind.NODE, node=NodeId(nxt),
                    t_start=arrive, t_end=arrive + self.node_dwell,
                )
                if self._conflicts_others(edge_res, vid):
                    continue
                if self._conflicts_others(node_res, vid):
                    continue
                nstate = (nxt, arrive)
                g = (best_g[state]) + travel
                if g < best_g.get(nstate, float("inf")):
                    best_g[nstate] = g
                    came_from[nstate] = (state, None)
                    heapq.heappush(
                        open_heap,
                        (g + self._h(nxt, goal, arrive), next(counter),
                         nxt, arrive, None),
                    )
            # 💡 Wait 动作(对应课程 L2 优先级避让):原地等一个 time_step。
            # 这是低优先级车"让"高优先级车的机制——当前节点/边被高优先级车
            # 占着,就 wait 到它过去再走。没有 wait,优先级规划就无法避让。
            # Wait 也是"占用当前节点",所以也要查冲突(避免在别人要进的节点死等)。
            # Wait 动作:原地等待,推进时间。
            wait_state = (node, t + self.time_step)
            if wait_state[1] <= horizon:
                wait_res = Reservation(
                    vid, ResourceKind.NODE, node=NodeId(node),
                    t_start=t, t_end=wait_state[1],
                )
                if not self._conflicts_others(wait_res, vid):
                    g = best_g[state] + self.time_step
                    if g < best_g.get(wait_state, float("inf")):
                        best_g[wait_state] = g
                        came_from[wait_state] = (state, "wait")
                        heapq.heappush(
                            open_heap,
                            (g + self._h(node, goal, wait_state[1]), next(counter),
                             node, wait_state[1], None),
                        )

        if goal_state is None:
            return PlanResult(vid, None, PlanFailure(vid, "no path within horizon"))

        trajectory, proposed = self._reconstruct(goal_state, came_from, vid)
        return PlanResult(vid, trajectory, None, proposed)

    # ------------------------------------------------------------------ #
    def _conflicts_others(self, candidate: Reservation, self_id: str) -> bool:
        """若 ``candidate`` 和*别的*智能体持有的预留冲突则返回 True。
        自己的预留被忽略。

        💡 学习点:为什么忽略自己的预留?因为重规划时,新车速轨迹会覆盖
        旧轨迹的时空(主循环会先 rollback 旧的)。如果把自己也当冲突,
        重规划就永远卡在"和自己的旧预留冲突"上,无法生成新轨迹。
        后端类比:一个事务改自己的未提交数据不算冲突,只和别人冲突才算。
        """
        for c in self.snap.reservations.overlaps(candidate):
            if c.blocking.agent_id != self_id:
                return True
        return False

    def _h(self, node: str, goal: str, t: float) -> float:
        """可采纳启发函数:图上最短边权 × 乐观跳数下界。我们用最便宜的单边
        权作为每跳下限——可采纳(不高估)且极便宜。"""
        cheapest = self._cheapest_edge()
        # 💡 诚实声明:这里 hops 取 0,所以 _h 恒为 0 → 退化成 Dijkstra
        # (f=g,没有方向感)。正确性不受影响(仍能找到解),只是搜索慢一些。
        # 工业版会预算"每个节点到目标的最少跳数"(一次反向 BFS),让 h>0
        # 变成真 A*,大幅减少扩展节点数(对应课程 L1-04 的启发函数设计)。
        # 粗略跳数下界取 0(无法在每次 pop 时廉价算 BFS 距离);用 0 退化为
        # Dijkstra,仍然正确且可采纳。
        hops = 0
        return cheapest * hops

    def _cheapest_edge(self) -> float:
        cache = getattr(self, "_cheapest", None)
        if cache is not None:
            return cache
        best = 0.0
        for nbrs in self.snap.graph.adj.values():
            for _, w in nbrs:
                if best == 0.0 or w < best:
                    best = w
        self._cheapest = best  # type: ignore[attr-defined]
        return best

    def _reconstruct(self, goal_state, came_from, vid):
        # 回溯收集 (节点, 时间)。合并连续的 wait,让轨迹成为干净的、不重复
        # 到达点的序列。
        chain: list[tuple[str, float]] = []
        s = goal_state
        while True:
            chain.append(s)
            parent = came_from.get(s)
            if parent is None:
                break
            s = parent[0]
        chain.reverse()
        # 构建 TimedPoints;丢弃 wait 造成的连续重复节点。
        points: list[TimedPoint] = []
        for node, t in chain:
            if points and points[-1].node == node:
                continue
            points.append(TimedPoint(node, t))
        # 保证至少有起点 + 目标。
        if len(points) == 1:
            points.append(TimedPoint(points[0].node, goal_state[1]))
        trajectory = Trajectory(vid, tuple(points))
        proposed = self._build_reservations(trajectory, vid)
        return trajectory, proposed

    def _build_reservations(self, traj: Trajectory, vid: str) -> tuple[Reservation, ...]:
        """物化一条已提交轨迹会新增的预留:每一跳一条 EDGE,每个到访节点一个
        NODE dwell。"""
        out: list[Reservation] = []
        pts = traj.points
        # 起点的节点 dwell
        out.append(Reservation(
            vid, ResourceKind.NODE, node=NodeId(pts[0].node),
            t_start=pts[0].t, t_end=pts[0].t + self.node_dwell,
        ))
        for a, b in zip(pts, pts[1:]):
            out.append(Reservation(
                vid, ResourceKind.EDGE, edge=EdgeId(a.node, b.node),
                t_start=a.t, t_end=b.t,
            ))
            out.append(Reservation(
                vid, ResourceKind.NODE, node=NodeId(b.node),
                t_start=b.t, t_end=b.t + self.node_dwell,
            ))
        return tuple(out)


# --------------------------------------------------------------------------- #
# Prioritized planning driver
# --------------------------------------------------------------------------- #
def prioritize_and_plan(
    snapshot: Snapshot,
    vehicles: Iterable[Vehicle],
    *,
    time_step: float = 1.0,
    node_dwell: float = 1.0,
) -> list[PlanResult]:
    """⚠️ 不保证跨智能体一致——使用前务必读这条警告。

    针对*单个固定*快照,按优先级顺序规划一组车辆。因为快照不可变,每个
    规划器看到的是同一条基线,它们**看不到彼此的候选计划**。于是两个智能体
    可能都规划进同一个空闲格——同时提交就会重复占位。

    这个辅助函数是为教学/诊断存在的(比如「每个智能体各自独立会怎么做?」)。
    要做相互一致的优先级规划,你要么 (a) 每接纳一个计划就提交进表、再为下一
    个智能体重拍快照——这正是 :class:`SchedulerLoop` 的做法;要么 (b) 收集
    所有候选,由中心解决冲突(CBS,课程 L2-04)。不要把这个函数的输出直接
    喂给 commit。
    """
    planner = Planner(snapshot, time_step=time_step, node_dwell=node_dwell)
    ordered = sorted(vehicles, key=lambda v: (-v.priority, v.vid))
    return [planner.plan(v, v.goal) for v in ordered if v.goal is not None]
