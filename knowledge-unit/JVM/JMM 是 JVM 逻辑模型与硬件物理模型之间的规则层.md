---
notion_id: 36ca2efbb18d81ce8e4fc294d856c41e
notion_url: https://app.notion.com/p/36ca2efbb18d81ce8e4fc294d856c41e
last_edited_time: 2026-05-26T00:00:57.297Z
synced_at: 2026-07-31T15:59:39.457Z
type: Insight
status: Inbox
domain: JVM
source_url: https://jenkov.com/tutorials/java-concurrency/java-memory-model.html
memory: true
review_question: "JMM 是物理结构还是规则层？它填补的是什么之间的鸿沟？"
review_answer: "规则层。填补 JVM 栈/堆逻辑抽象与硬件寄存器/缓存/主内存之间的鸿沟，定义线程在什么条件下能看到彼此的写入。"
---

## 1. 它解决了什么问题？
为什么多线程程序会出现可见性和竞态问题？JMM 到底在管什么？
## 2. 它的核心矛盾是什么？
JVM 的栈/堆是逻辑抽象（线程私有 vs 共享），硬件的寄存器/缓存/主内存是物理现实（一切都在主内存和缓存中流转）。两者的模型不一致，直接导致线程之间无法可靠地看到彼此的写入。
## 3. 它的本质模型是什么？
JMM 不是物理结构，而是**规则层**——填补 JVM 逻辑模型与硬件物理模型之间的鸿沟。它定义了一组契约：程序员遵守规则（用 volatile、synchronized 等），JMM 就给可见性和有序性保证；不遵守，就不保证。
## 4. 它还能解释什么？
所有需要桥接逻辑抽象和物理实现的场景：
- 数据库的隔离级别定义（逻辑上一致性 vs 物理上并发执行）
- 分布式系统的一致性模型（客户端视角 vs 多副本物理状态）
## 5. 认知变化
**以前我以为：** JMM 是 JVM 内部的某种物理内存结构
**现在我认为：** JMM 是逻辑模型与物理模型之间的规则层/契约层
## 6. 最终压缩
> JMM 是 JVM 栈/堆逻辑抽象与硬件寄存器/缓存/主内存物理现实之间的契约层，定义线程在什么条件下能看到彼此的写入。
