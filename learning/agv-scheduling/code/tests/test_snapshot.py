"""快照 copy-on-write:规划线程读冻结视图,同时循环继续变更 live 表。"""

from __future__ import annotations

from scheduler.models import NodeId, Reservation, ResourceKind
from scheduler.reservation_table import ReservationTable
from scheduler.snapshot import Graph


def _graph() -> Graph:
    return Graph(adj={"A": (("B", 1.0),), "B": (("A", 1.0),)}, nodes=("A", "B"))


def node(agent, name, ts, te):
    return Reservation(agent, ResourceKind.NODE, node=NodeId(name), t_start=ts, t_end=te)


class TestSnapshotIsolation:
    def test_snapshot_independent_of_subsequent_mutations(self):
        rt = ReservationTable()
        rt.reserve_batch([node("V1", "K", 1.0, 2.0)], now=0)
        snap = rt.snapshot_index()
        # mutate live table after snapshot taken
        rt.reserve_batch([node("V2", "J", 1.0, 2.0)], now=0)
        # snapshot still sees only the original reservation
        assert len(snap.all_reservations()) == 1
        assert snap.all_reservations()[0].agent_id == "V1"

    def test_snapshot_survives_release_on_live_table(self):
        rt = ReservationTable()
        rt.reserve_batch([node("V1", "K", 1.0, 2.0)], now=0)
        snap = rt.snapshot_index()
        rt.release_agent("V1")
        assert len(snap.all_reservations()) == 1  # snapshot unchanged

    def test_snapshot_overlap_queries_are_correct(self):
        rt = ReservationTable()
        rt.reserve_batch([node("V1", "K", 1.0, 2.0)], now=0)
        snap = rt.snapshot_index()
        cand = node("V2", "K", 1.5, 1.8)
        conflicts = snap.overlaps(cand)
        assert len(conflicts) == 1
        assert conflicts[0].type.value == "vertex"
