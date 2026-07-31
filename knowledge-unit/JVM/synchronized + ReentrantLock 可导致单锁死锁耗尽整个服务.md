---
notion_id: 372a2efbb18d81218c33c4a3f58d2448
notion_url: https://app.notion.com/p/372a2efbb18d81218c33c4a3f58d2448
last_edited_time: 2026-06-01T10:57:29.245Z
synced_at: 2026-07-31T15:59:39.457Z
type: Insight
status: Draft
domain: JVM
source_url: https://netflixtechblog.com/java-21-virtual-threads-dude-wheres-my-lock-3052540e231d
memory: true
review_question: "Netflix 的 Java 21 虚拟线程生产事故中，为什么一把 ReentrantLock 就能导致整台机器死锁？死锁的三步链路是什么？"
review_answer: "这不是经典的两锁死锁，而是一把锁 + ForkJoinPool carrier 线程池之间的资源死锁。三步链路：1)Pinning：虚拟线程在 synchronized 块内部等待 ReentrantLock 时被钉在 carrier 上；2)Carrier 耗尽：4 核=4 carrier，全部被 pinned 线程占满；3)死锁：锁释放后 AQS FIFO 唤醒的队首线程没有 carrier，有 carrier 的线程排在队尾拿不到锁。"
---

## 1. 它解决了什么问题？
这是个反面案例——它不是"解决了什么问题"，而是"暴露了什么问题"。Netflix 的 JVM 生态团队在将微服务迁移到 Java 21 + 虚拟线程后，遭遇了间歇性服务假死。最终定位到一个极其隐蔽的死锁变种。理解这个案例可以避免在自己的服务中踩同样的坑。
## 2. 它的核心矛盾是什么？
**Pinned 虚拟线程对 carrier 的不可抢占占用 vs AQS 的 FIFO 公平唤醒顺序。**
- pinned 线程占了 carrier 但排在 AQS 队列后面
- AQS 唤醒的队首线程不是 pinned 的，但没有 carrier 可用
- carrier 占用者无法主动让出（因为是 pinned 状态）
- 形成了："该执行的没资源，有资源的没资格执行"
## 3. 它的本质模型是什么？
**一把 ReentrantLock + N 个 carrier 线程 = 一个 N+1 资源的死锁。**
死锁的三步因果链：
1. **Pinning 发生**：`synchronized (this) { lock.lock() }` —— 在同步块内等锁，虚拟线程无法 unmount
2. **Carrier 池耗尽**：4 核 = 4 carrier，全部被 pinned 线程占满
3. **AQS FIFO 导致死锁**：释放锁唤醒队首，但队首没 carrier；有 carrier 的线程不在队首
**为什么诊断困难：**
- `jstack` 不显示虚拟线程调用栈
- 最终靠**堆转储 + Eclipse MAT** 分析 `AbstractQueuedSynchronizer` 内部状态，发现 `exclusiveOwnerThread == null`——锁是空闲的！
## 4. 它还能解释什么？
- **类似模式可发生在任何"固定 worker 数 + 有序等待队列"的系统**。例如：HikariCP 连接池只有 10 个连接，应用代码在 synchronized 内获取连接，连接耗尽时可能触发类似死锁。
- **Go 不会有这个问题**：goroutine 没有 Java synchronized 的 native 帧问题。
- **Java 24 JEP 491** 的根本修复：将 synchronized 的实现改为类似 ReentrantLock 的机制。
## 5. 认知变化
**看这篇文章前我以为**：Pinning 只是性能问题——偶尔 pin 一下影响吞吐量但不影响正确性。
**看这篇文章后我认为**：Pinning 在高并发 + 有限 carrier 的组合下，可以导致**正确性问题**——整个服务死锁。这不是"慢一点"的问题，是"完全不可用"的问题。
## 6. 最终压缩
> Netflix 案例揭示了一种新型死锁：synchronized 内等 ReentrantLock → 虚拟线程 pin 满全部 carrier → 锁释放后 AQS FIFO 唤醒的线程没 carrier 可用、有 carrier 的线程排在队尾拿不到锁 → 锁空闲但无人能获取，整个服务假死。
