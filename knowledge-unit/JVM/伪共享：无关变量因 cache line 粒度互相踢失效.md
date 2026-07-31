---
notion_id: 36ba2efbb18d81eca8a1fa0abfadf008
notion_url: https://app.notion.com/p/36ba2efbb18d81eca8a1fa0abfadf008
last_edited_time: 2026-05-25T15:56:15.042Z
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
多线程各自修改独立变量，看似无竞争，性能却差。原因不在逻辑层面而在物理层面。
## 2. 它的核心矛盾是什么？
逻辑上独立的变量，物理上可能共享同一个 cache line。
## 3. 它的本质模型是什么？
CPU 缓存一致性协议以 cache line（通常 64 字节）为粒度。两个不相关变量若在同一 cache line：
1. CPU-A 修改变量 A，整个 cache line 被标记为 Modified
2. MESI 使 CPU-B 的整个 cache line 失效（Invalidate）
3. CPU-B 要读变量 B，必须重新获取整个 cache line
4. 即使 B 没有被任何人修改，也被迫做了一次 cache miss
解决方案：
- **Padding**：在变量前后填充无用字段，确保独占 cache line
- **@Contended**（JDK 8+）：JVM 自动填充（需启用 -XX:-RestrictContended）
## 4. 它还能解释什么？
- 为什么高并发队列（如 Disruptor）特别关注 cache line 对齐
- 为什么 LongAdder 比 AtomicLong 在高竞争下性能更好（每个 Cell 独占 cache line）
- 为什么有时候加「无用」字段反而提升性能
## 5. 认知变化
**以前我以为：** 只要不操作同一个变量就不会有缓存竞争。
**现在我认为：** 缓存一致性以 cache line 为粒度，逻辑无关但物理相邻的变量也会互相影响。
## 6. 最终压缩
> 无关变量若在同一 cache line，一个 CPU 修改会导致另一个 CPU 的整个 cache line 失效，包括未被修改的变量。
