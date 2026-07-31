---
notion_id: 379a2efbb18d81ffab49f322adef5f35
notion_url: https://app.notion.com/p/379a2efbb18d81ffab49f322adef5f35
last_edited_time: 2026-06-08T00:15:09.485Z
synced_at: 2026-07-31T15:59:39.457Z
type: Model
status: Active
domain: Java
source_url: https://jenkov.com/tutorials/java-concurrency/race-conditions-and-critical-sections.html
memory: true
review_question: "拆临界区的决策框架是什么？ConcurrentHashMap从Java7到Java8锁粒度怎么演进的？"
review_answer: "粗锁安全但吞吐差，细锁吞吐高但易死锁。分段锁用少量锁覆盖大量资源（哈希映射）。ConcurrentHashMap演进：Java7用Segment（16个固定并行度），Java8用桶头节点锁（并行度随扩容自动提升），空桶CAS无锁，读完全无锁。通用原则：锁粒度应随数据规模动态调整。防死锁：统一锁获取顺序。"
---

## 1. 它解决了什么问题？
共享状态不可避免时，如何在安全性和吞吐量之间找平衡？
## 2. 它的核心矛盾是什么？
粗锁安全但吞吐差（所有线程串行），细锁吞吐高但容易死锁且实现复杂。
## 3. 它的本质模型是什么？
**拆临界区决策框架：**
1. 识别所有共享数据的操作
2. 按数据独立性分组（有不变量关联的必须同组）
3. 每组一把锁
4. 确保所有线程按统一顺序拿锁（防死锁）
5. 某组争用依然严重→更细粒度拆分或换无锁方案
**分段锁（Striped Lock）：**
- 用少量锁覆盖大量资源，通过哈希映射决定资源归哪把锁
- 并行度=锁数量，内存开销=锁数量
- 折中方案：不是每资源一把锁（内存浪费），也不是全局一把锁（并行度差）
**ConcurrentHashMap演进体现了锁粒度动态化的趋势：**
- Java 7：Segment数组（默认16个），固定并行度，扩容不增加Segment
- Java 8：桶头节点锁，并行度随table扩容自动提升
  - 空桶：CAS无锁写入
  - 非空桶：synchronized(头节点)
  - 读操作：完全无锁（volatile保证可见性）
**通用原则：锁粒度不是设计时固定的，应随数据规模动态调整。**
## 4. 它还能解释什么？
- 数据库行锁vs表锁是同样的tradeoff
- Netty线程隔离是另一种解法：直接消灭共享状态，就不需要考虑锁粒度
- 文件系统范围锁vs全局锁同理
## 5. 认知变化
**以前我以为：** 加锁就是synchronized(this)一把大锁
**现在我认为：** 锁粒度是安全性和吞吐量之间的动态平衡。粗锁安全但慢，细锁快但容易死锁。ConcurrentHashMap从Java7的固定Segment到Java8的动态桶头锁，体现了锁粒度应随数据规模调整的原则。
## 6. 最终压缩
> 锁粒度的本质是安全性和吞吐量的平衡。粗锁安全但串行，细锁并行但易死锁。分段锁是折中，ConcurrentHashMap从固定Segment到动态桶头锁体现了锁粒度应随数据规模调整的原则。
