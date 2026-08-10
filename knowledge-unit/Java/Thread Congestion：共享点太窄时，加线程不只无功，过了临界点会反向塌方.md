---
notion_id: "3b7a2efb-b18d-81cf-b9a2-fc8f566c86a1"
notion_url: "https://app.notion.com/p/3b7a2efbb18d81cfb9a2fc8f566c86a1"
last_edited_time: "2026-08-03T03:10:00.000Z"
synced_at: "2026-08-03T03:10:00.000Z"
type: Model
status: Draft
domain: Java
source_url: https://jenkov.com/tutorials/java-concurrency/thread-congestion.html
memory: true
review_question: Thread Congestion 和 Amdahl 定律是什么关系？为什么在线锁热点上加线程不只「无功」还「有害」？
review_answer: Amdahl 是理想下界（假设加线程零开销，吞吐单调渐近 1/S 天花板）；Thread Congestion 是现实修正（算上争用开销——上下文切换、cache 失效、锁自旋——到临界点后吞吐反向下降，甚至比单线程还差）。Amdahl 教「别指望加线程突破串行瓶颈」（无功），Thread Congestion 教「在锁热点上加线程会主动制造伤害」（有害）。治本不是加线程，而是拓宽或消除共享点：细锁、隔离、无锁。
---

## Thread Congestion：共享点太窄时，加线程不只无功，过了临界点会反向塌方

**解决的问题：**

多个线程争抢同一把锁 / 同一个阻塞队列 / 同一个共享资源，为什么加线程不只「没用」，还会让总吞吐反而下降，甚至比单线程还差？

**本质模型：**

当共享资源任意时刻只允许 1 个线程干活（比如一把锁），N 个线程在争用时，N-1 个在等、1 个在跑——表面串行化。但这只是理想情况。现实里，等待的线程会被 OS 反复唤醒→检查锁→抢不到→再阻塞，这些上下文切换烧 CPU；加上 cache 频繁失效、锁自旋空转，争用开销随线程数爆炸。当争用开销增长快于有用功减少时，总吞吐到达临界点后反向下降——不只平在 1/S，而是塌方。

和 Amdahl 定律的关系：Amdahl 是理想下界（假设加线程零开销，吞吐单调上升渐近天花板 1/S）；Thread Congestion 是 Amdahl 在「争用开销不可忽略」现实下的修正（到临界点后开始比单线程还慢）。前者教「别指望加线程突破串行瓶颈」，后者教「在锁热点上加线程会主动制造伤害」。

**权衡：**

解法不在「加多少线程」，而在「拓宽或消除共享点」：减小临界区（缩短持锁时间）、细分锁、线程隔离（Same-threading）、非阻塞算法（CAS）。增加线程数是误诊，治本的是改并发结构。

**迁移：**

这是「并发单元超过共享点容量后总吞吐下降」模型的实例，跨领域普遍：
- 数据库连接池：请求数超过连接数，排队 + 连接借还开销累积 → 吞吐下降
- MySQL 8 移除 query cache：query cache 是全局共享点，所有读写都竞争同一把锁，在高并发下自己制造 Thread Congestion → 被整个移除（「消除共享点」的工程决策）
- 高速公路、收银台、Git 合并冲突：共享点容量固定时，继续加并发单元都会塌方

## 6. 最终压缩

> Amdahl 说加线程突破不了串行瓶颈（无功），Thread Congestion 说在锁热点上加线程会反向塌方（有害）——治本不是加线程，而是拓宽或消除共享点。
