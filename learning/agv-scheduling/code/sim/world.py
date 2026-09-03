"""demo 世界:课程里的 7 节点仓库地图 + 确定性车辆推进器。

推进器按车辆已提交的轨迹推进:当时钟到达某个规划好的节点到达时刻,车辆
就上报该节点,并确认它已离开上一个资源。这让调度循环在没有真实通信层的
情况下也能「看到」进度。

地图复用课程 L1-02..L1-04 的拓扑:

        入口
         │ 5
        主道 ────────┐
        3│       6│
      岔口A     岔口B
        │4       2│   7│
      货架1    货架2─3─货架3
"""

from __future__ import annotations

from scheduler.models import Reservation, ResourceKind, Vehicle, VehicleState
from scheduler.scheduler_loop import Confirmation, PositionReport, SchedulerLoop
from scheduler.snapshot import Graph

# 节点名(ascii,便于代码)与通行时间(秒)。
MAP_ADJ = {
    "entry": (("main", 5.0),),
    "main": (("entry", 5.0), ("jA", 3.0), ("jB", 6.0)),
    "jA": (("main", 3.0), ("sh1", 4.0)),
    "jB": (("main", 6.0), ("sh2", 2.0), ("sh3", 7.0)),
    "sh1": (("jA", 4.0),),
    "sh2": (("jB", 2.0), ("sh3", 3.0)),
    "sh3": (("jB", 7.0), ("sh2", 3.0)),
}
MAP_NODES = tuple(MAP_ADJ.keys())


def build_graph() -> Graph:
    return Graph(adj=MAP_ADJ, nodes=MAP_NODES)


def build_loop() -> SchedulerLoop:
    return SchedulerLoop(build_graph())


# --------------------------------------------------------------------------- #
# 确定性车辆推进器
# --------------------------------------------------------------------------- #
class VehicleMover:
    """把已提交的预留翻译成位置上报 + 确认。

    对每辆正在执行的车辆,找到时间窗包含 ``clock`` 的最早预留;该车辆被视
    为处于该资源的节点上。当时钟跨过一个节点 dwell 预留的结束时刻,就发一
    个「该车辆已离开该节点」的确认。
    """

    def __init__(self, loop: SchedulerLoop) -> None:
        self.loop = loop
        # 记录我们已经确认过哪些预留,按 rid 去重。
        self._confirmed: set[int] = set()
        self._last_node: dict[str, str] = {}

    def reports_for(self, clock: float) -> tuple[list[PositionReport], list[Confirmation]]:
        positions: list[PositionReport] = []
        confirmations: list[Confirmation] = []
        for vid, v in loop_fleet(self.loop).items():
            if v.state in (VehicleState.OFFLINE, VehicleState.IDLE):
                continue
            own = [r for r in self.loop.table.reservations_for(vid)]
            # 当前节点 = 包含 clock 的节点预留对应的节点。
            cur_node = v.node
            for r in own:
                if r.kind is ResourceKind.NODE and r.t_start <= clock < r.t_end:
                    cur_node = r.node.name  # type: ignore[union-attr]
                    break
            if cur_node != self._last_node.get(vid):
                positions.append(PositionReport(vid, cur_node, clock))
                self._last_node[vid] = cur_node
            else:
                # 仅心跳上报,让循环看到我们还活着
                positions.append(PositionReport(vid, cur_node, clock))
            # 确认任何时间窗刚刚结束的节点预留。
            for r in own:
                if (
                    r.kind is ResourceKind.NODE
                    and r.t_end <= clock
                    and r.rid not in self._confirmed
                ):
                    confirmations.append(Confirmation(vid, r.resource_key))
                    self._confirmed.add(r.rid)
        return positions, confirmations


def loop_fleet(loop: SchedulerLoop) -> dict[str, Vehicle]:
    return loop.fleet
