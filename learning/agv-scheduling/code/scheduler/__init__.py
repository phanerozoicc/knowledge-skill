"""工业级 AGV / 人形调度核心。

公开接口:
    models            — 冻结的领域对象
    IntervalIndex     — intervaltree 支撑的重叠索引
    ReservationTable  — 单写者预留存储(事务、租约)
    Snapshot          — 给规划线程的不可变某一时刻视图
    Planner           — 时间扩展 A* + 优先级规划
    SchedulerLoop     — 单写者的 tick 循环
"""

from . import models
from .interval_index import IntervalIndex
from .metrics import Metrics, MetricsSnapshot
from .models import (
    Conflict,
    ConflictType,
    EdgeId,
    NodeId,
    Reservation,
    ResourceKind,
    Task,
    TimedPoint,
    Trajectory,
    Vehicle,
    VehicleState,
)
from .reservation_table import CommitResult, ReservationTable

__all__ = [
    "models",
    "IntervalIndex",
    "Metrics",
    "MetricsSnapshot",
    "CommitResult",
    "ReservationTable",
    "Reservation",
    "ResourceKind",
    "NodeId",
    "EdgeId",
    "Conflict",
    "ConflictType",
    "TimedPoint",
    "Trajectory",
    "Vehicle",
    "VehicleState",
    "Task",
]
