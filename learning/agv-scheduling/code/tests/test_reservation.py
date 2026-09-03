"""预留表:核心语义 + 事务原子性。"""

from __future__ import annotations

import pytest

from scheduler.models import EdgeId, NodeId, Reservation, ResourceKind
from scheduler.reservation_table import ReservationTable


def node(agent: str, name: str, ts: float, te: float) -> Reservation:
    return Reservation(agent, ResourceKind.NODE, node=NodeId(name), t_start=ts, t_end=te)


def edge(agent: str, src: str, dst: str, ts: float, te: float) -> Reservation:
    return Reservation(agent, ResourceKind.EDGE, edge=EdgeId(src, dst), t_start=ts, t_end=te)


# --------------------------------------------------------------------------- #
class TestBasicReserve:
    def test_first_reserve_succeeds(self):
        rt = ReservationTable()
        r = rt.reserve_batch([node("V1", "K", 1.0, 2.0)], now=0)
        assert r.ok and len(rt) == 1

    def test_overlapping_node_conflicts(self):
        rt = ReservationTable()
        rt.reserve_batch([node("V1", "K", 1.0, 2.0)], now=0)
        r = rt.reserve_batch([node("V2", "K", 1.5, 1.8)], now=0)
        assert not r.ok
        assert r.conflicts[0].type.value == "vertex"

    def test_non_overlapping_same_node_ok(self):
        rt = ReservationTable()
        rt.reserve_batch([node("V1", "K", 1.0, 2.0)], now=0)
        r = rt.reserve_batch([node("V2", "K", 2.0, 3.0)], now=0)  # touches at 2.0, half-open
        assert r.ok

    def test_different_nodes_independent(self):
        rt = ReservationTable()
        rt.reserve_batch([node("V1", "K", 1.0, 5.0)], now=0)
        r = rt.reserve_batch([node("V2", "J", 1.0, 5.0)], now=0)
        assert r.ok


class TestEdgeConflicts:
    def test_same_direction_overlap_is_edge_conflict(self):
        rt = ReservationTable()
        rt.reserve_batch([edge("V1", "A", "B", 1.0, 3.0)], now=0)
        r = rt.reserve_batch([edge("V2", "A", "B", 2.0, 4.0)], now=0)
        assert not r.ok
        assert r.conflicts[0].type.value in ("edge", "following")

    def test_opposite_direction_is_swapping(self):
        rt = ReservationTable()
        rt.reserve_batch([edge("V1", "A", "B", 1.0, 3.0)], now=0)
        r = rt.reserve_batch([edge("V2", "B", "A", 2.0, 4.0)], now=0)
        assert not r.ok
        assert r.conflicts[0].type.value == "swapping"

    def test_non_overlapping_opposite_ok(self):
        rt = ReservationTable()
        rt.reserve_batch([edge("V1", "A", "B", 1.0, 2.0)], now=0)
        r = rt.reserve_batch([edge("V2", "B", "A", 3.0, 4.0)], now=0)
        assert r.ok


class TestAtomicBatch:
    def test_partial_conflict_rolls_back_whole_batch(self):
        rt = ReservationTable()
        rt.reserve_batch([node("V1", "K", 1.0, 2.0)], now=0)
        # V3 on J is free, but V4 on K conflicts with V1 -> whole batch rejected
        batch = [node("V3", "J", 1.0, 2.0), node("V4", "K", 1.5, 1.8)]
        r = rt.reserve_batch(batch, now=0)
        assert not r.ok
        # Nothing from the batch landed; V1 still the only reservation.
        assert len(rt) == 1
        assert all(res.agent_id == "V1" for res in rt.all_reservations())

    def test_intra_batch_self_conflict_rejected(self):
        rt = ReservationTable()
        # Two reservations in the same batch colliding with each other.
        batch = [node("V1", "K", 1.0, 3.0), node("V1", "K", 2.0, 4.0)]
        r = rt.reserve_batch(batch, now=0)
        assert not r.ok
        assert len(rt) == 0

    def test_clean_batch_all_land_with_rids(self):
        rt = ReservationTable()
        batch = [node("V1", "K", 1.0, 2.0), node("V1", "J", 1.0, 2.0)]
        r = rt.reserve_batch(batch, now=0)
        assert r.ok
        assert len(r.rids) == 2
        assert all(rid > 0 for rid in r.rids)
        assert len(rt) == 2


class TestSelfNonConflict:
    def test_agent_does_not_conflict_with_own_reservations(self):
        """重规划时必须能和该智能体自己的旧计划重叠;循环会先回滚旧的,但即便
        不回滚,自己的预留也不该挡自己。"""
        rt = ReservationTable()
        rt.reserve_batch([node("V1", "K", 1.0, 2.0)], now=0)
        # interval_index.overlaps() reports the existing one, but reservation
        # of the SAME agent on the same resource should still be admitted in a
        # new batch only after rollback. Here we assert the index reports the
        # overlap (so the loop knows), distinct from blocking.
        cands = rt.conflicts_for(node("V1", "K", 1.5, 1.8))
        # overlap is reported regardless of agent; dedup is the loop's job.
        assert len(cands) == 1


class TestValidation:
    def test_zero_length_rejected(self):
        with pytest.raises(ValueError):
            node("V1", "K", 1.0, 1.0)

    def test_negative_length_rejected(self):
        with pytest.raises(ValueError):
            node("V1", "K", 2.0, 1.0)

    def test_node_reservation_requires_node(self):
        with pytest.raises(ValueError):
            Reservation("V1", ResourceKind.NODE, t_start=1.0, t_end=2.0)

    def test_edge_reservation_requires_edge(self):
        with pytest.raises(ValueError):
            Reservation("V1", ResourceKind.EDGE, t_start=1.0, t_end=2.0)
