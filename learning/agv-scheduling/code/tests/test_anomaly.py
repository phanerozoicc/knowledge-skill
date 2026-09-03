"""调度循环 + 异常处理:离线检测、释放、滚动重规划。"""

from __future__ import annotations

from scheduler.models import Vehicle, VehicleState
from scheduler.scheduler_loop import (
    PositionReport,
    SchedulerConfig,
    SchedulerLoop,
)
from scheduler.snapshot import Graph


def two_node_graph() -> Graph:
    return Graph(adj={"A": (("B", 2.0),), "B": (("A", 2.0),)}, nodes=("A", "B"))


class TestBasicLoop:
    def test_assign_goal_triggers_plan(self):
        loop = SchedulerLoop(two_node_graph())
        loop.add_vehicle(Vehicle(vid="V1", node="A", last_heartbeat=0.0))
        loop.assign_goal("V1", "B")
        r = loop.tick([PositionReport("V1", "A", 0.0)])
        assert "V1" in r.committed
        assert len(loop.table) > 0

    def test_goal_reached_clears_plan(self):
        loop = SchedulerLoop(two_node_graph())
        loop.add_vehicle(Vehicle(vid="V1", node="A", last_heartbeat=0.0))
        loop.assign_goal("V1", "B")
        loop.tick([PositionReport("V1", "A", 0.0)])
        # simulate arrival: report vehicle at goal node
        loop.tick([PositionReport("V1", "B", 100.0)])
        assert loop.fleet["V1"].state is VehicleState.IDLE
        assert "V1" not in loop.goals


class TestOfflineDetection:
    def test_stale_heartbeat_marks_offline_and_releases(self):
        loop = SchedulerLoop(two_node_graph(),
                             config=SchedulerConfig(heartbeat_timeout=5.0))
        loop.add_vehicle(Vehicle(vid="V1", node="A", last_heartbeat=0.0))
        loop.assign_goal("V1", "B")
        loop.tick([PositionReport("V1", "A", 0.0)])   # plans, heartbeat=0
        assert len(loop.table) > 0
        # no further reports -> heartbeat stays at 0; clock advances past timeout
        for _ in range(10):
            r = loop.tick()
            if "V1" in r.offline:
                break
        assert "V1" in r.offline
        assert loop.fleet["V1"].state is VehicleState.OFFLINE
        # reservations released
        assert len(loop.table.reservations_for("V1")) == 0

    def test_offline_vehicle_is_not_replanned(self):
        loop = SchedulerLoop(two_node_graph(),
                             config=SchedulerConfig(heartbeat_timeout=3.0))
        loop.add_vehicle(Vehicle(vid="V1", node="A", last_heartbeat=0.0))
        loop.assign_goal("V1", "B")
        loop.tick([PositionReport("V1", "A", 0.0)])
        # go silent until offline
        for _ in range(8):
            loop.tick()
        assert loop.fleet["V1"].state is VehicleState.OFFLINE
        # further ticks must not try to plan V1 (no failures attributed to it)
        r = loop.tick()
        assert "V1" not in r.replanned and "V1" not in r.plan_failures


class TestRollingReplan:
    def test_replan_after_release_frees_slot_for_another(self):
        loop = SchedulerLoop(two_node_graph())
        loop.add_vehicle(Vehicle(vid="V1", node="A", last_heartbeat=0.0, priority=2))
        loop.add_vehicle(Vehicle(vid="V2", node="A", last_heartbeat=0.0, priority=1))
        loop.assign_goal("V1", "B")
        loop.assign_goal("V2", "B")
        loop.tick([PositionReport("V1", "A", 0.0), PositionReport("V2", "A", 0.0)])
        # V1 (higher prio) gets the slot; V2 must defer
        assert "V1" in loop.active_rids
        # release V1
        loop.table.release_agent("V1")
        loop.active_rids.pop("V1", None)
        loop.fleet["V1"] = loop.fleet["V1"].with_state(state=VehicleState.OFFLINE)
        # V2 should now be able to plan on a later tick
        r = loop.tick([PositionReport("V2", "A", loop.clock)])
        assert "V2" in r.replanned
