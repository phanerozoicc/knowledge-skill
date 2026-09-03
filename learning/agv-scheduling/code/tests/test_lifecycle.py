"""预留生命周期:确认 / 租约过期 / 释放 / 回滚。

这些测试钉死我们在 demo 中踩过的那个 bug:t_end 已过却未确认的预留绝不能
被清理;只有租约过期才是异常信号。
"""

from __future__ import annotations

from scheduler.models import EdgeId, NodeId, Reservation, ResourceKind
from scheduler.reservation_table import ReservationTable


def node(agent, name, ts, te, lease=0.0):
    return Reservation(agent, ResourceKind.NODE, node=NodeId(name),
                       t_start=ts, t_end=te, lease_deadline=lease)


class TestConfirm:
    def test_confirm_retires_reservation(self):
        rt = ReservationTable()
        rt.reserve_batch([node("V1", "K", 1.0, 2.0)], now=0)
        n = rt.confirm_passed("V1", "node:K", now=3.0)
        assert n == 1
        assert len(rt) == 0

    def test_confirm_only_touches_named_agent(self):
        rt = ReservationTable()
        rt.reserve_batch([node("V1", "K", 1.0, 2.0)], now=0)
        rt.reserve_batch([node("V2", "K", 2.0, 3.0)], now=0)
        rt.confirm_passed("V1", "node:K", now=2.5)
        ids = {r.agent_id for r in rt.all_reservations()}
        assert ids == {"V2"}


class TestExpireStale:
    def test_t_end_past_but_lease_live_is_NOT_reaped(self):
        """回归测试(demo 踩过的 bug):时间窗已结束但租约仍有效的预留必须
        保留——车辆可能只是还没来得及发确认。"""
        rt = ReservationTable(lease_margin=10.0)
        rt.reserve_batch([node("V1", "K", 1.0, 2.0)], now=0)  # lease = 2 + 10 = 12
        affected = rt.expire_stale(now=5.0)   # t_end=2 < 5 but lease=12 > 5
        assert affected == []
        assert len(rt) == 1

    def test_lease_lapse_is_reaped(self):
        rt = ReservationTable(lease_margin=1.0)
        rt.reserve_batch([node("V1", "K", 1.0, 2.0)], now=0)  # lease = 2 + 1 = 3
        affected = rt.expire_stale(now=4.0)
        assert affected == ["V1"]
        assert len(rt) == 0
        assert rt.metrics.stale_reaped == 1

    def test_explicit_lease_deadline_respected(self):
        rt = ReservationTable(lease_margin=100.0)
        rt.reserve_batch([node("V1", "K", 1.0, 2.0, lease=3.0)], now=0)
        affected = rt.expire_stale(now=4.0)
        assert affected == ["V1"]

    def test_distinct_agents_returned_once(self):
        rt = ReservationTable(lease_margin=0.5)
        rt.reserve_batch([node("V1", "K", 1.0, 2.0), node("V1", "J", 3.0, 4.0)], now=0)
        rt.reserve_batch([node("V2", "L", 1.0, 2.0)], now=0)
        affected = rt.expire_stale(now=10.0)
        assert sorted(affected) == ["V1", "V2"]


class TestReleaseAndRollback:
    def test_release_agent_drops_all_its_reservations(self):
        rt = ReservationTable()
        rt.reserve_batch([node("V1", "K", 1.0, 2.0), node("V1", "J", 3.0, 4.0)], now=0)
        rt.reserve_batch([node("V2", "L", 1.0, 2.0)], now=0)
        n = rt.release_agent("V1")
        assert n == 2
        assert {r.agent_id for r in rt.all_reservations()} == {"V2"}

    def test_rollback_undoes_a_committed_batch(self):
        rt = ReservationTable()
        r = rt.reserve_batch([node("V1", "K", 1.0, 2.0), node("V1", "J", 3.0, 4.0)], now=0)
        n = rt.rollback(r.rids)
        assert n == 2
        assert len(rt) == 0
        assert rt.metrics.tx_rolled_back == 1

    def test_release_keeps_others(self):
        rt = ReservationTable()
        rt.reserve_batch([node("V1", "K", 1.0, 2.0)], now=0)
        rt.reserve_batch([node("V2", "K", 2.0, 3.0)], now=0)
        rt.release_agent("V1")
        # V1's freed slot [1,2) is now reusable; V2's [2,3) is still held.
        assert rt.reserve_batch([node("V3", "K", 1.0, 2.0)], now=0).ok
        assert not rt.reserve_batch([node("V4", "K", 2.0, 3.0)], now=0).ok  # V2 still there
