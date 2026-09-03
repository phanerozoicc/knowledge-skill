# scheduler-core — 工业级 AGV / 人形调度核心

单写者调度核心:预留表(事务/租约/确认)+ 调度循环(滚动重规划/异常清理)
+ 时间扩展 A* 优先级规划 + 多车仿真 demo + 完整测试。

对应课程 L2-02(预留表)、L2-04(规划)、L3-02(实时性)、L3-04(容错)。

## 运行

```bash
cd code
uv sync --extra test   # 创建 .venv,安装依赖(以 uv.lock 锁定版本)

uv run python -m sim.demo     # 端到端多车 demo(避让 + 掉线重规划)
uv run pytest -q              # 36 个测试
```

依赖以 `pyproject.toml` 声明、`uv.lock` 锁定;`uv sync` 幂等,改动依赖后
重新执行即可。测试依赖在 `[project.optional-dependencies]` 的 `test` 组,
所以带 `--extra test`。

## 架构:单写者主循环 + 不可变快照(COW)

```
        ┌─────────────────────────────────────┐
每 tick │  SchedulerLoop (唯一写者,无锁)       │
 1.推进时钟                              │
 2.收上报/确认   持有: ReservationTable │
 3.离线检测              FleetState(可变)│
 4.清租约过期        ┌── snapshot() ───┐│
 5.标 dirty 车      │  (COW 深拷贝)   ││
 6.优先级规划 ──────┼─▶ 给 Planner    ││
   (每车重 snapshot)│   (纯函数,读快照)││
 7.commit/回滚 ◀───┘                  ││
        └─────────────────────────────────────┘
```

**为什么这样**:状态变更只在单线程主循环发生 → 天然无竞态;规划(重
计算)读不可变快照 → 高吞吐且一致。这是 actor 模型的工业简化
(ROS2 nav2 / 多数 fleet manager 都是这套)。

## 模块

| 文件 | 职责 |
|------|------|
| `scheduler/models.py` | 冻结 dataclass:Reservation/Vehicle/Task/Trajectory/Conflict |
| `scheduler/interval_index.py` | intervaltree 封装:节点/边区间索引 + 对向(swapping)检测 |
| `scheduler/reservation_table.py` | 核心:事务原子性、确认、租约失效、撤销回滚、metrics |
| `scheduler/snapshot.py` | 不可变快照 + Graph 拓扑 |
| `scheduler/planner.py` | 时间扩展 A* + 优先级规划 |
| `scheduler/scheduler_loop.py` | 主循环:tick/滚动重规划/异常清理 |
| `scheduler/metrics.py` | 计数器(单写者)+ 不可变快照副本 |
| `sim/world.py` | 课程 7 节点地图 + 确定性车辆推进器 |
| `sim/scenarios.py` | demo 场景:汇合避让 + 掉线重规划 |

## 关键工程决策

1. **事务原子性** `reserve_batch`:先全检查(含批内自冲突),全过才批量
   写入;任一冲突 → 整批回滚,绝不部分写入污染表。
2. **租约而非 t_end 判失效**:预留带 `lease_deadline`(t_end + 余量)。
   `expire_stale` **只** reap 租约过期的;t_end 过期但未 confirm 的保留
   (车辆可能正在离开,comms 滞后)。这避免了 demo 中暴露的 bug(把正
   常行驶的车误判为掉线)。
3. **确认机制** `confirm_passed`:车通过节点上报后删除该占用。这是区分
   "正常完成"和"异常停滞"的唯一可靠信号。
4. **COW 快照**:规划线程读 IntervalTree 的 copy(payload 冻结,可共享),
   主循环同时可变 live 表。test_snapshot 钉死隔离性。
5. **优先级规划**:按优先级顺序,每车 re-snapshot 规划,低优先级自然
   避让高优先级的已提交预留。

## 诚实的边界(不是商业产品)

- ✅ **工业级正确性**:并发安全、事务原子、边/节点/swapping 冲突、
  确认/租约/撤销、滚动重规划、可观测 metrics、36 测试
- ⚖️ **合理简化**:
  - 规划用 **prioritized planning**(次优,工业常用),非 L2-04 的最优 CBS
  - 启发函数 h=0(退化为 Dijkstra);正确但不追求速度
  - demo 单线程验证;架构支持规划线程池但 demo 未实际并发
- ❌ **不做**:持久化/重启恢复、VDA5050 真实通信、分布式多实例、GUI

## 设计要点对应的课程

| 代码概念 | 课程 |
|---------|------|
| 预留表 = 4D 行锁 | L2-02 |
| swapping/following 冲突 | L2-02 |
| prioritized planning | L2-04 的简化版(完整 CBS 见课程) |
| 确认/租约/失效 | L3-04 容错 |
| 滚动重规划、快照 | L3-02 实时性 |
| 时间扩展 A* | L1-04 A* 的时空扩展 |
