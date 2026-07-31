---
notion_id: 36ba2efbb18d81b0a48af04376917f52
notion_url: https://app.notion.com/p/36ba2efbb18d81b0a48af04376917f52
last_edited_time: 2026-05-25T15:56:14.979Z
synced_at: 2026-07-31T15:59:39.457Z
type: Model
status: Active
domain: JVM
source_url: 
memory: true
review_question: "JMM 的核心抽象是什么？volatile/synchronized/final 和它的关系是什么？"
review_answer: "happens-before 是 JMM 唯一的核心抽象。volatile/synchronized/final 只是建立 happens-before 关系的手段。"
---

## 1. 它解决了什么问题？
JMM 规则繁多，volatile/synchronized/final 各有说法，开发者容易迷失在具体 API 语义中，缺乏统一的理解框架。
## 2. 它的核心矛盾是什么？
语言层需要一个平台无关的抽象来定义线程间可见性保证，而底层硬件（x86、ARM）的内存模型差异巨大。happens-before 就是这个中间抽象层。
## 3. 它的本质模型是什么？
happens-before 是 JMM 唯一的核心抽象。它定义了一种偏序关系：如果 A happens-before B，那么 A 的结果对 B 可见。volatile、synchronized、final 只是建立 happens-before 关系的手段。
8 条 happens-before 规则可压缩为：
- **程序顺序规则**：单线程内，前面的操作 happens-before 后面的操作
- **volatile 规则**：volatile 写 happens-before 后续对同一变量的 volatile 读
- **锁规则**：unlock happens-before 后续对同一把锁的 lock
- **线程生命周期**：start() happens-before 线程内任意操作；线程所有操作 happens-before join() 返回
- **传递性**：如果 A → B 且 B → C，则 A → C
## 4. 它还能解释什么？
- 任何需要推理并发正确性的场景，都以 happens-before 为推理工具
- DCL 的正确性分析：volatile 写 happens-before volatile 读，保证构造函数的写在引用赋值之前对其他线程可见
- final 语义：构造函数中对 final 字段的写 happens-before 其他线程读到该对象的引用
## 5. 认知变化
**以前我以为：** volatile 是 JMM 的核心机制，各种同步原语各有各的保证。
**现在我认为：** happens-before 才是 JMM 唯一的核心抽象。volatile/synchronized/final 只是建立 happens-before 关系的手段。理解 JMM 就是理解 happens-before。
## 6. 最终压缩
> happens-before 是 JMM 唯一的核心抽象，volatile/synchronized/final 只是建立 happens-before 关系的手段。
