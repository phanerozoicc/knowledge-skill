---
notion_id: 376a2efbb18d81e3ba0ff48ccf7cd26b
notion_url: https://app.notion.com/p/376a2efbb18d81e3ba0ff48ccf7cd26b
last_edited_time: 2026-06-05T23:53:05.750Z
synced_at: 2026-07-31T15:59:39.457Z
type: Model
status: Active
domain: Java
source_url: https://jenkov.com/tutorials/java-concurrency/concurrency-models.html
memory: true
review_question: "五种并发模型分别是什么？核心分歧是什么？Reactor和Virtual Thread是什么关系？"
review_answer: "核心分歧：共享状态vs分离状态。五种模型：1)Parallel Workers—委派者分任务给独立worker(Java线程池)；2)Assembly Line/Reactor—流水线无共享状态(Netty/Vert.x)；3)Actor—独立状态+异步消息点对点(Erlang/Akka)；4)CSP—Channel通信发布订阅(Go)；5)Functional Parallelism—函数调用参数全拷贝(ForkJoinPool)。Reactor解决IO复用+线程复用，Virtual Thread简化编程模型，二者互补可组合。"
---

## 1. 它解决了什么问题？
并发有哪些根本不同的组织方式？每种模型的核心假设和代价是什么？
## 2. 它的核心矛盾是什么？
并发模型的核心分歧是：共享状态 vs 分离状态。共享状态简单直觉但bug丛生，分离状态更安全但设计更难。
## 3. 它的本质模型是什么？
**核心分法：** 共享状态 vs 分离状态
- 共享状态：线程共享内存，需要锁、同步，容易出竞态/死锁
- 分离状态：线程不共享数据，通过不可变对象或数据副本通信
**五种具体模型：**
1. Parallel Workers（委派者分任务给独立worker）— 代表：Java线程池、Tomcat
2. Assembly Line / Reactor（流水线，每个worker只做一部分）— 代表：Vert.x、Akka、Netty EventLoop
3. Actor Model（每个Actor独立状态，异步消息通信，点对点）— 代表：Erlang、Akka
4. CSP（通过Channel通信，发布-订阅解耦）— 代表：Go goroutine + channel
5. Functional Parallelism（函数调用即消息，参数全拷贝，天然无共享）— 代表：Java ForkJoinPool
**Reactor vs Virtual Thread 不是替代关系：**
- Reactor：IO多路复用+线程复用，零创建成本，缓存友好，适合网络密集型
- Virtual Thread：简化编程模型，适合业务逻辑重的场景
- 两者可组合：EventLoop处理IO，业务逻辑丢给Virtual Thread
## 4. 它还能解释什么？
- 并发模型与分布式系统架构惊人相似：线程间通信≈进程间通信，共享状态≈共享数据库微服务，流水线≈消息队列解耦
- STM（软件事务内存）= 数据库乐观锁思路应用于内存
## 5. 认知变化
**以前我以为：** 并发就是多线程加锁
**现在我认为：** 并发模型的本质选择是共享状态 vs 分离状态。分离状态（Actor/CSP/Reactor+线程绑定）才是更安全的主流方向。Reactor和Virtual Thread解决不同层面的问题，可以组合。
## 6. 最终压缩
> 并发模型的核心分歧是共享状态vs分离状态。Actor/CSP/Reactor+线程绑定走分离路线，更安全。Reactor解决IO复用+线程复用，Virtual Thread简化编程模型，二者互补而非替代。
