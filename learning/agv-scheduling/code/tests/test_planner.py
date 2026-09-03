"""规划器:时间扩展 A* 产出无冲突轨迹。"""

from __future__ import annotations

from scheduler.models import Vehicle
from scheduler.planner import Planner
from scheduler.reservation_table import ReservationTable
from scheduler.snapshot import Graph, Snapshot
from scheduler.metrics import MetricsSnapshot


def line_graph() -> Graph:
    # A -2- B -2- C -2- D
    return Graph(
        adj={"A": (("B", 2.0),), "B": (("A", 2.0), ("C", 2.0)),
             "C": (("B", 2.0), ("D", 2.0)), "D": (("C", 2.0),)},
        nodes=("A", "B", "C", "D"),
    )


def make_snap(table, graph, clock=0.0) -> Snapshot:
    return Snapshot(
        clock=clock, graph=graph, fleet={},
        reservations=table.snapshot_index(),
        metrics=MetricsSnapshot(),
        plan_horizon=60.0,
    )


class TestSingleAgentPlan:
    def test_plans_simple_path(self):
        table = ReservationTable()
        g = line_graph()
        snap = make_snap(table, g)
        v = Vehicle(vid="V1", node="A")
        result = Planner(snap).plan(v, "D")
        assert result.trajectory is not None
        nodes = [p.node for p in result.trajectory]
        assert nodes[0] == "A" and nodes[-1] == "D"
        assert "B" in nodes and "C" in nodes

    def test_proposed_reservations_match_hops(self):
        table = ReservationTable()
        g = line_graph()
        snap = make_snap(table, g)
        result = Planner(snap).plan(Vehicle(vid="V1", node="A"), "D")
        # A->B->C->D = 3 edges; each hop yields 1 edge + 1 node dwell + start node dwell
        edges = [r for r in result.proposed if r.kind.value == "edge"]
        assert len(edges) == 3

    def test_unknown_start_fails(self):
        table = ReservationTable()
        snap = make_snap(table, line_graph())
        result = Planner(snap).plan(Vehicle(vid="V1", node="Z"), "D")
        assert result.trajectory is None
        assert result.failure is not None

    def test_blocked_by_other_agent_finds_wait_or_fail(self):
        """更高优先级的智能体挡住唯一通路;规划器要么在 horizon 内等到它过去
        再走,要么优雅失败——但绝不产出冲突轨迹。"""
        table = ReservationTable()
        g = line_graph()
        # V0 occupies B for a long window, blocking V1 A->D.
        from scheduler.models import NodeId, Reservation, ResourceKind
        table.reserve_batch([
            Reservation("V0", ResourceKind.NODE, node=NodeId("B"), t_start=0.0, t_end=50.0),
        ], now=0)
        snap = make_snap(table, g)
        result = Planner(snap).plan(Vehicle(vid="V1", node="A"), "D")
        if result.trajectory is not None:
            # If it found a path (waiting until t>50 then crossing B), the
            # proposed reservations must not overlap V0's block before t=50.
            for r in result.proposed:
                if r.node and r.node.name == "B":
                    assert r.t_start >= 50.0
