"""交给规划线程的、不可变的某一时刻快照。

调度循环是唯一写者。在派发规划工作前,它构建一个 :class:`Snapshot`,
里面打包:

- 车队状态的冻结副本,
- 预留索引的冻结副本(IntervalTree 的 copy;payload 是冻结的 Reservation,
  可安全共享),
- 规划器需要的图拓扑,
- 当前时钟值。

规划线程只读快照,绝不碰 live 表。这就是 COW(copy-on-write)准则,让
「多读者、一写者」无锁且无竞态:规划线程最坏只是读到略陈旧的数据,绝不
会是撕裂(半更新)的数据。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .interval_index import IntervalIndex
from .metrics import MetricsSnapshot
from .models import Vehicle


@dataclass(frozen=True, slots=True)
class Graph:
    """规划器要推理的拓扑。冻结、可共享。

    ``adj`` 把节点映射到 (邻居, 通行时间) 列表。通行时间是时间扩展 A* 的
    边权;课程 L1 讲的「距离」在这里被编码成时间,这样预留直接以秒为单位。
    """
    adj: Mapping[str, tuple[tuple[str, float], ...]]
    nodes: tuple[str, ...]

    def neighbors(self, node: str) -> tuple[tuple[str, float], ...]:
        return self.adj.get(node, ())

    def has_node(self, node: str) -> bool:
        return node in self.adj


@dataclass(frozen=True, slots=True)
class Snapshot:
    """规划线程产出无冲突轨迹所需的全部信息。

    由 :meth:`SchedulerLoop.snapshot` 构建。所有消费者都把它当作只读;字段
    都是不可变的(frozen dataclass + tuple/frozen 值)。
    """
    clock: float
    graph: Graph
    fleet: Mapping[str, Vehicle]
    reservations: IntervalIndex          # 一份私有副本;查询安全
    metrics: MetricsSnapshot
    plan_horizon: float                  # 不要规划超过此时刻的到达
