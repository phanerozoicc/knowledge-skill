---
notion_id: 36ba2efbb18d81eca8a1fa0abfadf008
notion_url: https://app.notion.com/p/36ba2efbb18d81eca8a1fa0abfadf008
last_edited_time: 2026-08-03T02:30:00.000Z
synced_at: 2026-08-03T02:30:00.000Z
type: Model
status: Active
domain: JVM
source_url: https://jenkov.com/tutorials/java-concurrency/false-sharing.html
memory: true
review_question: False Sharing 为什么在单核不存在、只发生在多核？它的根因是软件 bug 还是硬件 bug？
review_answer: 单核只有一个 L1，没有 MESI 一致性协议运作的空间，乒乓无从发生。False Sharing 是多核 + L1 独享架构的必然副作用。它不是单纯软件或硬件 bug，而是「软件字段布局假设」和「硬件缓存粒度（cache line）」的错配：硬件按契约正确工作，JVM 无法自动判断字段相关性，修复责任在软件——用 padding 或 @Contended 让独立字段物理隔开一个 cache line。
---

## 伪共享：无关变量因 cache line 粒度互相踢失效

**解决的问题：**

两个逻辑上完全无关的 volatile 字段，各自被不同线程独立写入，代码绝对正确、没有数据竞争——为什么多核下性能反而比单线程还差？原因不在逻辑层面，而在物理层面。

**本质模型：**

CPU 缓存以 cache line（通常 64 字节）而非单个变量为粒度，L1/L2 每核独享，L3 跨核共享。两个相邻的 volatile long（各 8 字节）会被装进同一条 cache line。线程1（core 1）写字段 A → MESI 协议发现这条 line 在 core 2 也有副本 → 把 core 2 的整条 line 失效（包括 B）→ 线程2 下次碰 B 要整个重新加载 → 写 B 又失效 core 1 的 line（包括 A）→ 乒乓。

关键判断：这是软件与硬件的「粒度错配」——软件假设字段独立，硬件以 cache line 为一致性粒度。硬件按契约工作没错，JVM 也无法自动判断哪些字段该隔离（相关性是语义，不是布局能看出来），修复责任在软件的字段布局决策上。

**单核为何无此问题：** 单核只有一个 L1，没有 MESI 一致性协议运作的空间，乒乓无从发生。False Sharing 是多核 + L1 独享架构的必然副作用。

**证据：**

解法一（手工 padding）：在变量前后填充无用字段，确保独占 cache line
```java
public volatile long A = 0;
public long p1,p2,p3,p4,p5,p6;   // 48 字节填充
public volatile long B = 0;        // B 被挤到下一条 cache line
```

解法二（@Contended，JDK 8+）：JVM 自动填充（需启用 -XX:-RestrictContended）
```java
@Contended public volatile long B = 0;
```

**权衡：**

Padding/@Contended 增加内存消耗但消除伪共享。它是隐藏杀手：代码看起来绝对正确，profiling 只显示 cache miss 高，不告诉你是哪两个字段在乒乓——只有懂硬件缓存层的人能定位。

**迁移：**

- 为什么高并发队列（如 Disruptor）特别关注 cache line 对齐
- 为什么 LongAdder 比 AtomicLong 在高竞争下性能更好（每个 Cell 独占 cache line）
- 为什么有时候加「无用」字段反而提升性能
- 这是「粒度错配」上位模型的实例之一：数据库以页为读写最小单元，两条逻辑无关的记录落在同页会共享锁、版本链、WAL；凡有「软件以为独立、底层粒度更粗」的结构，都要问无关单元会不会在底层被强行耦合。

## 5. 认知变化

**以前我以为：** 只要不操作同一个变量就不会有缓存竞争。
**现在我认为：** 缓存一致性以 cache line 为粒度，逻辑无关但物理相邻的变量也会互相影响；这不是软件或硬件单方面的 bug，而是两层粒度假设的错配，修复责任在软件。

## 6. 最终压缩

> 软件以为字段独立，硬件以 64 字节 cache line 做一致性——两层粒度错配让逻辑无关的字段在多核间乒乓失效，修复责任永远在软件：padding 或 @Contended 主动隔开。
