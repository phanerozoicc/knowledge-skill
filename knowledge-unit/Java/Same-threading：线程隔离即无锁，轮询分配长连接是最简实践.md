---
notion_id: 377a2efbb18d81df8fa3d3bfdbb89536
notion_url: https://app.notion.com/p/377a2efbb18d81df8fa3d3bfdbb89536
last_edited_time: 2026-06-06T00:20:11.279Z
synced_at: 2026-07-31T15:59:39.457Z
type: Insight
status: Active
domain: Java
source_url: https://jenkov.com/tutorials/java-concurrency/same-threading.html
memory: true
review_question: "Same-threading的核心思想是什么？Netty中如何实践？"
review_answer: "复制N份单线程系统每核一个不共享状态。实践：Netty EventLoopGroup.next()轮询分配连接，稳定长连接下轮询即均衡，连接间天然独立无共享数据，线程隔离即无锁。不需要sharding或消息传递。"
---

## 1. 它解决了什么问题？
如何用单线程设计享受多核性能？线程隔离如何实现无锁？
## 2. 它的核心矛盾是什么？
单线程简单但不能利用多核，多线程利用多核但引入共享状态复杂性。Same-threading是折中：多核并行，但每个线程独立运行不共享状态。
## 3. 它的本质模型是什么？
Same-threading = 复制N份单线程系统，每核一个，不共享状态，通信靠消息传递。
实践中的典型模式：
- Netty EventLoopGroup.next()轮询分配连接
- 稳定长连接场景下，轮询即可保证负载均衡
- 连接之间天然独立，无共享数据，线程隔离即无锁
## 4. 它还能解释什么？
- Redis单线程模型：单线程处理请求，避免锁，多实例分片扩展
- Nginx worker进程：每个worker独立，靠进程隔离实现无锁
## 5. 认知变化
**以前我以为：** 多线程一定要共享状态加锁
**现在我认为：** 线程隔离（same-threading）是更优解——每个线程独立处理自己的连接/数据，根本不需要锁。轮询分配在长连接场景下就是最简单有效的负载均衡。
## 6. 最终压缩
> Same-threading的本质是线程隔离=无共享状态=无锁。Netty的EventLoop轮询分配长连接就是典型实践：连接间天然独立，轮询即均衡，线程隔离即无锁。
