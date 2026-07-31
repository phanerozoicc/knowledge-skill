---
notion_id: 3aca2efbb18d815f8284f427ee901f4a
notion_url: https://app.notion.com/p/3aca2efbb18d815f8284f427ee901f4a
last_edited_time: 2026-07-29T09:29:35.755Z
synced_at: 2026-07-31T15:59:39.457Z
type: Insight
status: Active
domain: Java
source_url: https://jenkov.com/tutorials/java-concurrency/non-blocking-algorithms.html
memory: false
review_question: ""
review_answer: ""
---

## 非阻塞算法的核心是「不阻塞，只尝试」——CAS、ABA 和意图提交

**解决的问题：**

锁会导致线程挂起→上下文切换→重新调度，代价高。能否在并发访问共享数据时完全不阻塞线程？

**本质模型：**

非阻塞算法的核心原则：一个线程被挂起不应导致其他线程也被挂起。实现方式不是「阻塞等待条件满足」而是「尝试操作→失败返回→调用者决定下一步」。

关键技术：
1) CAS (Compare-and-Swap)：CPU 级原子指令，乐观假设没有人并发修改，如果假设成立就成功写入，失败则重试。AtomicLong/AtomicReference 基于此实现。低到中争用下性能远超锁。
2) ABA 问题：变量从 A→B→A，CAS 检测不到中间发生过变化。解法：AtomicStampedReference 将引用和版本号绑在一起原子替换。
3) 不可交换数据结构：对队列/Map 等大结构，不能整体复制。解法是提交「修改意图」→用 CAS 挂在数据结构上→执行修改→移除意图引用。关键：意图对象必须包含足够信息让其他线程完成修改——如果提交线程被挂起，其他线程不会因此阻塞。
4) 单写者模式：只有一个线程写 volatile 变量时天然无竞态，不需要 CAS。最简单有效的非阻塞模式。

**权衡：**

非阻塞算法避免了线程挂起开销，无死锁风险，但实现难度远高于锁方案。CAS 重试循环在高争用下可能退化（CPU 空转），此时阻塞方案反而更高效。工程原则：优先用 J.U.C 现成的非阻塞结构（ConcurrentLinkedQueue、Atomic*），不要自己写。

**迁移：**

非阻塞思想是乐观并发控制的根基：数据库的 MVCC、Git 的无锁提交模型、Redis 的 INCR 原子操作都是同一种哲学——乐观尝试，冲突则重试。适用于任何「争用不严重但不想为锁开销买单」的场景。核心权衡：单次操作成本（CAS 更低）vs 冲突重试时的浪费。


> 注：此页面在 Notion 中正文为空，结构化内容（Problem/Essence/Tradeoff/Transfer/Boundary）存储于 properties 字段，本地文件由 properties 重建。推回 Notion 时这些字段会同步。
