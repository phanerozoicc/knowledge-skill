---
notion_id: 3aca2efbb18d8156b65ed9bcd670fa03
notion_url: https://app.notion.com/p/3aca2efbb18d8156b65ed9bcd670fa03
last_edited_time: 2026-07-29T09:29:35.755Z
synced_at: 2026-07-31T15:59:39.457Z
type: Insight
status: Active
domain: Java
source_url: https://jenkov.com/tutorials/java-concurrency/amdahls-law.html
memory: false
review_question: ""
review_answer: ""
---

## Amdahl 定律：不可并行部分是加速比的天花板

**解决的问题：**

加更多 CPU 核就一定能快吗？如果可以，最多能快多少？什么时候加核不再有效？

**本质模型：**

Amdahl 定律计算并行化的理论加速上限：T(N) = B + (1-B)/N。其中 B 是不可并行的比例，N 是 CPU 数。核心洞察：不可并行部分是加速比的天花板——即使 N→∞，加速比最多到 1/B。

例子：如果 40% 不可并行(B=0.4)，无论多少核，最多加速 2.5x。把 B 从 0.4 优化到 0.2，理论上限就提升到 5x。

实践警示（Jenkov 强调）：理论公式不包含内存带宽、缓存一致性协议开销、线程协调成本。串行版本可能因为零协调开销比多线程版本还快。Amdahl 定律用于「指导优化方向」而非「精确预测性能」。

**权衡：**

Amdahl 定律揭示了一个残酷事实：即使 5% 的代码不可并行，加速上限也只有 20x。但这也指明了优化优先级——与其花时间让已并行的部分更并行，不如找出并消除那 5% 的串行瓶颈。注意区分「算法层面的串行比例」和「实测中的串行瓶颈」——缓存行为和线程协调可能引入额外的隐性串行化。

**迁移：**

这个定律超越了并发编程：数据库查询优化的 Amdahl 类比是「瓶颈算子占总时间比决定了优化上限」，分布式系统的类比是「串行操作（如全局锁/共识）限制了水平扩展」。适用于任何「部分可并行化」的系统设计。


> 注：此页面在 Notion 中正文为空，结构化内容（Problem/Essence/Tradeoff/Transfer/Boundary）存储于 properties 字段，本地文件由 properties 重建。推回 Notion 时这些字段会同步。
