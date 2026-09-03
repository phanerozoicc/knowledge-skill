"""轻量级指标。

只有调度循环会变更这些(单写者),所以用普通 int 是安全的。快照带一份冻结
副本,让规划线程/观察者读到一致的某一时刻视图。这和别处的 COW 准则一致。
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace


@dataclass(frozen=True, slots=True)
class MetricsSnapshot:
    """计数器的不可变某一时刻副本。"""
    reserve_attempts: int = 0
    reserve_success: int = 0
    reserve_failed: int = 0
    conflicts_vertex: int = 0
    conflicts_swapping: int = 0
    conflicts_following: int = 0
    stale_reaped: int = 0
    tx_committed: int = 0
    tx_rolled_back: int = 0
    active_reservations: int = 0
    replans_triggered: int = 0


@dataclass(slots=True)
class Metrics:
    """可变计数器;只由调度循环触碰。"""
    reserve_attempts: int = 0
    reserve_success: int = 0
    reserve_failed: int = 0
    conflicts_vertex: int = 0
    conflicts_swapping: int = 0
    conflicts_following: int = 0
    stale_reaped: int = 0
    tx_committed: int = 0
    tx_rolled_back: int = 0
    replans_triggered: int = 0

    def snapshot(self, active_reservations: int) -> MetricsSnapshot:
        return MetricsSnapshot(
            reserve_attempts=self.reserve_attempts,
            reserve_success=self.reserve_success,
            reserve_failed=self.reserve_failed,
            conflicts_vertex=self.conflicts_vertex,
            conflicts_swapping=self.conflicts_swapping,
            conflicts_following=self.conflicts_following,
            stale_reaped=self.stale_reaped,
            tx_committed=self.tx_committed,
            tx_rolled_back=self.tx_rolled_back,
            active_reservations=active_reservations,
            replans_triggered=self.replans_triggered,
        )
