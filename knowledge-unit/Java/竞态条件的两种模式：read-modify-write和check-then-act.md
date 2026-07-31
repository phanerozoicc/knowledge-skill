---
notion_id: 379a2efbb18d81ddbeb8d2c4ca770d86
notion_url: https://app.notion.com/p/379a2efbb18d81ddbeb8d2c4ca770d86
last_edited_time: 2026-06-08T00:15:09.457Z
synced_at: 2026-07-31T15:59:39.457Z
type: Insight
status: Active
domain: Java
source_url: https://jenkov.com/tutorials/java-concurrency/race-conditions-and-critical-sections.html
memory: true
review_question: "竞态条件的两种经典模式是什么？各自的根因是什么？"
review_answer: "两种模式：1)Read-Modify-Write：读、改、写三步非原子，两个线程读同值各自改后写回会覆盖（如count+=value）；2)Check-Then-Act：检查和动作之间状态被其他线程修改（如先检查containsKey再remove）。本质都是读和写之间存在时间窗口。解法：synchronized/Lock/Atomic变量让临界区原子化。"
---

## 1. 它解决了什么问题？
多线程访问共享数据时，结果为什么会出错？根本原因是什么？
## 2. 它的核心矛盾是什么？
多线程需要共享数据，但"读取"和"写入/动作"之间存在时间窗口，其他线程可以趁虚而入。
## 3. 它的本质模型是什么？
竞态条件有两种经典模式：
**Read-Modify-Write**：读、改、写三步不是原子的
- 例子：count += value
- 根因：两个线程都读到旧值，各自修改后写回，后写者覆盖前者
- 不只是Java：Redis INCR、数据库 UPDATE count=count+1 都是同样问题
**Check-Then-Act**：检查和动作之间状态被改了
- 例子：if(map.containsKey("key")) map.remove("key")
- 根因：两个线程同时检查通过，但只有一个能成功执行动作
共同本质：**"读取"和"写入/动作"不是原子操作，中间窗口被其他线程趁虚而入。**
解法：让临界区变成原子操作（synchronized、Lock、Atomic变量）。
## 4. 它还能解释什么？
- 数据库的脏读/丢失更新本质也是read-modify-write竞态
- 分布式场景下Redis INCR、数据库乐观锁解决的是同一问题
- 单线程模型（如Redis、Node.js）通过消除并发彻底避免竞态
## 5. 认知变化
**以前我以为：** 竞态条件是Java特有的问题
**现在我认为：** 竞态条件出现在任何"状态可被并发修改"的地方，本质是读和写之间存在时间窗口
## 6. 最终压缩
> 竞态条件本质是读和写之间存在时间窗口。两种模式：read-modify-write（读改写非原子）和check-then-act（检查和动作之间状态被改）。解法是让临界区原子化。
