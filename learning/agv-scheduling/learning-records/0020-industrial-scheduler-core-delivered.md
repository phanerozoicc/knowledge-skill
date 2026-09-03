# 工业级调度核心库交付(code/)

## 交付物
学习者明确要求"工业级完整代码,不是玩具"。经过 plan mode 对齐(并发模型=单写者+快照、范围=预留表+调度循环demo、区间结构=intervaltree),交付:

```
code/  (~1900 行,36 测试全绿)
  scheduler/   核心库(8 模块)
  sim/         demo(7 节点地图 + 多车推进器 + 2 场景)
  tests/       5 测试文件,36 测试
  README.md    架构/运行/诚实边界
```

## 工业级正确性已实现(非玩具)
- 单写者主循环 + 不可变 COW 快照(无锁无竞态)
- 预留表事务原子性(reserve_batch:含批内自冲突检测,整批回滚)
- 节点/边/swapping/following 冲突分类检测
- 确认(confirm_passed)/租约(lease)/失效(expire_stale)/撤销(rollback)/释放(release_agent)
- 滚动重规划 + 离线检测 + 释放重分配
- 可观测 metrics + 不可变快照副本

## 开发过程中端到端 demo 暴露并修复的真实 bug(价值高)
1. **expire_stale 误判**:最初把 t_end<=now 且未 confirm 当异常 → demo 里正常行驶的车每 tick 被误清→每 tick 重规划→车不动。修正为**只按 lease 判失效**(t_end 只是预期离开时间,车可能 comms 滞后)。这正是回答学习者"异常怎么处理预留表"问题的核心。
2. **离线检测不触发**:last_heartbeat>0 永远为假(首报 t=0.0)。改用 -1 哨兵 + >=0 判定。

## 诚实声明(写进 README,不过头)
- 规划用 prioritized planning(次优工业常用),非 L2-04 最优 CBS
- 启发 h=0(退化为 Dijkstra),正确但不追速度
- demo 单线程验证;架构支持规划线程池但未实际并发
- 不含持久化/VDA5050 真实通信/分布式/GUI

## 自我审查(新规范)已执行
- prioritize_and_plan 函数加了强警告(固定快照不跨 agent 一致,不能直接 commit)
- 审查 h=0、过期预留堆积、线程声明,均诚实记录

## 对课程/学习者的影响
- 这是 L2-02 预留表的"工业级代码版",学习者可直接读、改、跑
- L2-04 CBS 可在此代码上扩展(把 prioritized planning 换成 CBS)
- 学习者(后端工程师)对"工业级"的标准已明确:并发安全+事务+异常+测试,后续课程代码沿用此标准
- 建立了"先 plan mode 对齐再写"的流程,对大工程任务有效
