---
notion_id: 36ba2efbb18d814194eff57aadb2b663
notion_url: https://app.notion.com/p/36ba2efbb18d814194eff57aadb2b663
last_edited_time: 2026-05-25T15:56:15.027Z
synced_at: 2026-07-31T15:59:39.457Z
type: Insight
status: Active
domain: JVM
source_url: 
memory: false
review_question: ""
review_answer: ""
---

## 1. 它解决了什么问题？
理解为什么 MESI 协议不能即时保证缓存一致性——中间有两个异步缓冲区在「捣乱」。
## 2. 它的核心矛盾是什么？
CPU 性能优化（异步化）与缓存一致性（同步要求）之间的矛盾。
## 3. 它的本质模型是什么？
- **Store buffer**：CPU 写入时不等 MESI 的 Invalidate ACK，先写到 store buffer 就继续执行。其他 CPU 短暂看不到这次写入。
- **Invalid queue**：CPU 收到 Invalidate 消息后立即 ACK 但不立即处理，排入 invalid queue。该 CPU 短暂还在用旧数据。
- **Store forwarding**：CPU 自己可以从 store buffer 读到最新值，但其他 CPU 看不到。
两者都是 MESI 内部的性能优化，代价是引入了暂时的可见性延迟。
## 4. 它还能解释什么？
- 异步优化与一致性之间的经典权衡（类似 TCP 的流量控制 vs 延迟）
- 为什么需要内存屏障（强制排空这两个缓冲区）
- 为什么即使有 MESI，不加 volatile 的共享变量仍可能有可见性问题
## 5. 认知变化
**以前我以为：** store buffer 和 invalid queue 是 MESI 之外的问题，是「另一个层面」。
**现在我认为：** 它们是 MESI 内部的性能优化。不是两个不同的问题，而是同一个机制（MESI）的不同方面。
## 6. 最终压缩
> Store buffer 和 invalid queue 是 MESI 的性能优化，代价是延迟可见。内存屏障通过强制排空它们来恢复即时一致性。
