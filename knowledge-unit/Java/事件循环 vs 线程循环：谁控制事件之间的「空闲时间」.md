---
notion_id: 3aca2efbb18d8189ad8af4a5a9beb5ca
notion_url: https://app.notion.com/p/3aca2efbb18d8189ad8af4a5a9beb5ca
last_edited_time: 2026-07-29T09:28:00.515Z
synced_at: 2026-07-31T15:59:39.457Z
type: Insight
status: Active
domain: Java
source_url: https://jenkov.com/tutorials/java-concurrency/single-threaded-concurrency.html
memory: false
review_question: ""
review_answer: ""
---

## 事件循环 vs 线程循环：谁控制事件之间的「空闲时间」

**解决的问题：**

单线程并发设计中，用一个线程处理多个任务的 I/O 和计算——如何协调 I/O 事件和后台任务的执行？传统事件循环框架（Netty/Node.js）把控制权交给了库，应用只能在回调中被动响应

**本质模型：**

事件循环和责任在库端，线程循环责任在应用端。关键差异不在于谁调用谁，而在于「事件之间的时间归谁控制」。

事件循环(Event Loop)：线程调用事件循环库 → 库在有事件时回调你的代码。没有事件时，这段时间归库控制，应用无法利用它做任何事。

线程循环(Thread Loop)：线程首先调用你的应用代码 → 你的代码检查 IO 工具的待处理事件。没有事件时，你可以利用这段时间推进其他任务的进度（单线程任务切换）。你还可以选择不检查新连接——这本身就是一种背压机制。

这是单线程并发设计的核心：应用完全控制何时处理 IO、何时推进后台任务、何时响应新连接。代价是需要更多代码。

**权衡：**

线程循环给应用提供了完整的调度控制力（背压、任务优先级、增量大小），但要求应用自己实现任务切换逻辑。事件循环更简单——只需注册回调——但放弃了事件间时间的控制权和背压能力。Netty/Vert.x 选择了事件循环并获得了极简的编程模型，但它们的成功也说明：大多数应用并不需要线程循环的极致控制力。

**迁移：**

这个选择在其他领域以不同形式出现：async/await (事件循环) vs 显式调度器(线程循环)、Kubernetes controller reconcile loop（事件驱动）vs 自定义调度器、消息队列的 push 模式 vs pull 模式。核心分歧：是你告诉框架什么时候干活，还是框架告诉你什么时候干活？


> 注：此页面在 Notion 中正文为空，结构化内容（Problem/Essence/Tradeoff/Transfer/Boundary）存储于 properties 字段，本地文件由 properties 重建。推回 Notion 时这些字段会同步。
