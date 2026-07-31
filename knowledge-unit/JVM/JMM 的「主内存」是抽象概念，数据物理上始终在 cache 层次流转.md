---
notion_id: 36ba2efbb18d8111a81eeaf423a69b8d
notion_url: https://app.notion.com/p/36ba2efbb18d8111a81eeaf423a69b8d
last_edited_time: 2026-05-25T15:56:15.068Z
synced_at: 2026-07-31T15:59:39.457Z
type: Update
status: Active
domain: JVM
source_url: 
memory: false
review_question: ""
review_answer: ""
---

## 1. 它解决了什么问题？
JMM 文档和很多教程说「volatile 从主内存读取」「线程工作内存刷新到主内存」，容易误导为数据物理上在 RAM 和 CPU cache 之间搬运。
## 2. 它的核心矛盾是什么？
JMM 规范为了平台无关性创造了「主内存」和「工作内存」的抽象，但这个抽象不对应物理硬件。实际数据流完全在 cache 层次内。
## 3. 它的本质模型是什么？
- **JMM 的「主内存」** = 规范层面的抽象概念，表示「对所有线程可见的统一状态」
- **物理现实**：数据始终在 L1 → L2 → L3 → RAM 的层次结构中流转。CPU 几乎不直接读写 RAM。
- **MESI 的角色**：在 cache 层次内保证各 CPU 的 cache line 一致性
- **「从主内存读取」的实际含义**：如果当前 CPU 的 cache line 不是最新有效状态（Modified/Exclusive/Shared），需要从其他 CPU 的 cache 或 L3 获取最新副本
## 4. 它还能解释什么？
- 为什么说「volatile 写入后刷新到主内存」是不准确的（写入的对象是 store buffer → cache line，不是 RAM）
- 为什么 CPU 设计者用 cache hierarchy 而不是直接操作 RAM（速度差距 100x+）
## 5. 认知变化
**以前我以为：** volatile 写会把数据刷新到物理 RAM，volatile 读会从物理 RAM 重新加载。
**现在我认为：** JMM 的「主内存」是抽象概念。物理上数据始终在 cache 层次流转，通过 MESI 协议保持一致性。CPU 几乎不直接读写 RAM。
## 6. 最终压缩
> JMM 的「主内存」是规范层面的抽象，不对应物理 RAM。数据物理上始终在 cache 层次内流转。
