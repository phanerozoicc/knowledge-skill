"""demo 场景 + 运行器。

运行:python -m sim.demo
"""

from __future__ import annotations

import sys

from scheduler.models import Vehicle, VehicleState
from scheduler.scheduler_loop import SchedulerLoop
from sim.world import VehicleMover, build_loop


def _print_header(title: str) -> None:
    print("\n" + "═" * 64)
    print(f"  {title}")
    print("═" * 64)


# 车辆状态的中文对照:枚举值保留英文,便于和代码里的 VehicleState 对上。
STATE_CN = {
    "idle": "待命",
    "planning": "规划中",
    "executing": "执行中",
    "waiting": "等待让路",
    "offline": "离线",
}


def _print_fleet(loop: SchedulerLoop) -> None:
    for vid, v in loop.fleet.items():
        goal = loop.goals.get(vid, "-")
        state_cn = STATE_CN.get(v.state.value, v.state.value)
        print(f"    {vid}: 位置={v.node:6} 状态={state_cn}({v.state.value}) 目标={goal}")


def run(steps: int = 14) -> None:
    loop = build_loop()
    mover = VehicleMover(loop)

    # ---- 场景 1:三车汇合,优先级避让 ---------
    _print_header("场景 1:三车汇合,优先级避让")
    loop.add_vehicle(Vehicle(vid="V1", node="entry", priority=3, last_heartbeat=0.0))
    loop.add_vehicle(Vehicle(vid="V2", node="sh1", priority=2, last_heartbeat=0.0))
    loop.add_vehicle(Vehicle(vid="V3", node="sh3", priority=1, last_heartbeat=0.0))
    loop.assign_goal("V1", "sh3")
    loop.assign_goal("V2", "entry")
    loop.assign_goal("V3", "sh1")

    for _ in range(steps):
        positions, confirms = mover.reports_for(loop.clock)
        # V1 先种一个心跳,免得首次规划前被当成离线
        r = loop.tick(positions, confirms)
        print(
            f"  t={r.clock:5.1f} | 活跃预留={r.metrics.active_reservations:2d} "
            f"重规划={list(r.replanned)} 失败={list(r.plan_failures)} "
            f"离线={list(r.offline)} 过期清理={list(r.reaped_agents)} "
            f"冲突(节点/对向/跟随)={r.metrics.conflicts_vertex}/"
            f"{r.metrics.conflicts_swapping}/{r.metrics.conflicts_following}"
        )
        _print_fleet(loop)
        if not loop.goals and all(
            v.state in (VehicleState.IDLE, VehicleState.OFFLINE) for v in loop.fleet.values()
        ):
            print("  -- 全部目标已到达 --")
            break

    # ---- 场景 2:一辆车任务中途掉线 -------------------
    _print_header("场景 2:V2 掉线 → 释放预留 + 其他人重规划")
    loop.fleet["V2"] = loop.fleet["V2"].with_state(state=VehicleState.OFFLINE)
    loop.table.release_agent("V2")
    loop.active_rids.pop("V2", None)
    loop.assign_goal("V3", "sh2")   # 给 V3 一个曾被 V2 挡住的新目标
    for _ in range(8):
        positions, confirms = mover.reports_for(loop.clock)
        r = loop.tick(positions, confirms)
        print(
            f"  t={r.clock:5.1f} | 活跃预留={r.metrics.active_reservations:2d} "
            f"重规划={list(r.replanned)} 离线={list(r.offline)} "
            f"过期清理(累计)={r.metrics.stale_reaped}"
        )
        _print_fleet(loop)
        if not loop.goals:
            print("  -- 全部目标已到达 --")
            break

    _print_header("最终指标(metrics)")
    m = loop.table.metrics.snapshot(loop.table.active_count())
    print(
        f"  预留提交:尝试={m.reserve_attempts} 成功={m.reserve_success} "
        f"失败={m.reserve_failed}\n"
        f"  事务:提交={m.tx_committed} 回滚={m.tx_rolled_back}\n"
        f"  冲突(节点/对向/跟随) = "
        f"{m.conflicts_vertex}/{m.conflicts_swapping}/{m.conflicts_following}\n"
        f"  过期清理={m.stale_reaped} 重规划次数={m.replans_triggered}"
    )


if __name__ == "__main__":
    sys.exit(run())
