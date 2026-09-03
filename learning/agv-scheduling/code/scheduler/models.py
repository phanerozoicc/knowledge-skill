"""调度核心的领域模型。

这里的所有值对象都是不可变的(frozen dataclass),因此可以安全地在
单写者调度循环和只读规划线程之间通过快照共享。

设计要点
--------
- 时间是从循环自选起点算起的浮点「秒」。调度拥有时钟;本模块不读墙钟。
- :class:`Reservation` 是「智能体 X 在 [t_start, t_end) 占用资源 R」的原子
  单位,是预留表的基本元素,即课程 L2-02 讲的 4D 锁。
- 资源有两种:节点(一个点,如路口)和有向边(从 A 到 B 的通道)。边的
  身份是「有序」的——A->B 和 B->A 是不同资源,正是这一点让我们能检测
  对向(交换/迎面)冲突。
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Iterator


# --------------------------------------------------------------------------- #
# 资源
# --------------------------------------------------------------------------- #
class ResourceKind(str, Enum):
    NODE = "node"
    EDGE = "edge"


@dataclass(frozen=True, slots=True)
class NodeId:
    """节点资源的身份。"""
    name: str

    def __str__(self) -> str:
        return self.name


@dataclass(frozen=True, slots=True)
class EdgeId:
    """有向边资源的身份:src -> dst。

    顺序很重要:``EdgeId("A", "B")`` 和 ``EdgeId("B", "A")`` 是不同的资源,
    它们被同时占用就是对向(swapping/迎面)冲突——见
    :mod:`scheduler.reservation_table`。
    """
    src: str
    dst: str

    @property
    def reversed(self) -> "EdgeId":
        return EdgeId(self.dst, self.src)

    def __str__(self) -> str:
        return f"{self.src}->{self.dst}"


# --------------------------------------------------------------------------- #
# 预留
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class Reservation:
    """智能体对某资源在半开时间段内的占用声明。

    时间段是 ``[t_start, t_end)``。两个预留冲突,当且仅当它们在同一资源
    上的时间段重叠(或在反向边上重叠)。

    ``lease_deadline`` 是该预留「在没有显式确认的情况下,仍被视为有效」的
    最晚时刻。若智能体过了 ``lease_deadline`` 仍未确认进度,该预留会被当
    过期清理。这是租约/TTL 机制,防止崩溃的智能体永远占着锁(见 L3-04)。
    """
    agent_id: str
    kind: ResourceKind
    # node / edge 二者之一有意义,由 kind 决定。
    node: NodeId | None = None
    edge: EdgeId | None = None
    t_start: float = 0.0
    t_end: float = 0.0
    lease_deadline: float = 0.0
    # 由预留表在 commit 时分配的单调递增 id。用于精确删除和事务簿记。
    # 0 表示「尚未提交」。
    rid: int = 0

    def __post_init__(self) -> None:
        if self.t_end <= self.t_start:
            raise ValueError(
                f"Reservation t_end ({self.t_end}) 必须 > t_start ({self.t_start})"
            )
        if self.kind is ResourceKind.NODE and self.node is None:
            raise ValueError("NODE 预留必须设置 .node")
        if self.kind is ResourceKind.EDGE and self.edge is None:
            raise ValueError("EDGE 预留必须设置 .edge")
        if self.kind is ResourceKind.NODE and self.edge is not None:
            raise ValueError("NODE 预留不应设置 .edge")
        if self.kind is ResourceKind.EDGE and self.node is not None:
            raise ValueError("EDGE 预留不应设置 .node")
        # 自动租约:结束时刻 + 安全余量,除非调用方已显式指定。
        # 实际的 lease 字段填充在调用方的 commit 步骤里完成。

    @property
    def resource_key(self) -> str:
        """区间索引分桶用的稳定字符串键。"""
        if self.kind is ResourceKind.NODE:
            return f"node:{self.node}"          # type: ignore[str-format]
        return f"edge:{self.edge}"               # type: ignore[str-format]

    def overlaps_time(self, t_start: float, t_end: float) -> bool:
        """半开区间重叠判断。这是用得最多的谓词。"""
        return t_start < self.t_end and self.t_start < t_end


# --------------------------------------------------------------------------- #
# 冲突报告
# --------------------------------------------------------------------------- #
class ConflictType(str, Enum):
    VERTEX = "vertex"          # 两个智能体同一时刻在同一节点
    SWAPPING = "swapping"      # 两个智能体在反向边上(迎面)
    FOLLOWING = "following"    # 同向边,后车追上前车
    EDGE = "edge"              # 同边重叠的通称(涵盖跟随)


@dataclass(frozen=True, slots=True)
class Conflict:
    """候选预留与已有预留之间检测到的重叠。"""
    type: ConflictType
    candidate: Reservation
    blocking: Reservation

    def __str__(self) -> str:
        return (
            f"<{self.type.value}: {self.candidate.agent_id} vs "
            f"{self.blocking.agent_id} on {self.candidate.resource_key} "
            f"[{self.candidate.t_start:.2f},{self.candidate.t_end:.2f})>"
        )


# --------------------------------------------------------------------------- #
# 轨迹(规划器输出)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class TimedPoint:
    """航点:在时刻 ``t`` 之前到达 ``node``。"""
    node: str
    t: float


@dataclass(frozen=True, slots=True)
class Trajectory:
    """带时间戳的节点序列,由规划器产出。

    这是课程 L2-02 讲的「时空轨迹」——粗粒度(节点级 + 时间),足够生成
    预留,区别于车辆端产出的、运动学平滑后的可执行轨迹。
    """
    agent_id: str
    points: tuple[TimedPoint, ...]

    def __post_init__(self) -> None:
        if len(self.points) == 0:
            raise ValueError("Trajectory 至少要有 1 个点")
        ts = [p.t for p in self.points]
        for a, b in zip(ts, ts[1:]):
            if b < a:
                raise ValueError(f"Trajectory 的时间必须非递减:{ts}")

    @property
    def start(self) -> TimedPoint:
        return self.points[0]

    @property
    def goal(self) -> TimedPoint:
        return self.points[-1]

    def __iter__(self) -> Iterator[TimedPoint]:
        return iter(self.points)


# --------------------------------------------------------------------------- #
# 车队 / 任务状态
# --------------------------------------------------------------------------- #
class VehicleState(str, Enum):
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    WAITING = "waiting"        # 为让更高优先级的智能体通过而暂停
    OFFLINE = "offline"        # 心跳丢失 / 故障


@dataclass(frozen=True, slots=True)
class Vehicle:
    """某快照时刻车辆状态的不可变视图。"""
    vid: str
    node: str                  # 最近已知节点
    state: VehicleState = VehicleState.IDLE
    priority: int = 0          # 在优先级规划中,数值越大路权越高
    last_heartbeat: float = -1.0   # -1 哨兵:尚未收到过任何上报
    # 异常检测用:智能体落后于计划进度多少秒后,会被标 dirty 重新规划。
    slip_threshold: float = 2.0
    goal: str | None = None

    def with_state(self, **changes) -> "Vehicle":
        return replace(self, **changes)


@dataclass(frozen=True, slots=True)
class Task:
    """一个工作单元:把智能体从 ``src`` 移到 ``dst``。"""
    task_id: str
    agent_id: str
    src: str
    dst: str
    created_at: float = 0.0
    priority: int = 0
