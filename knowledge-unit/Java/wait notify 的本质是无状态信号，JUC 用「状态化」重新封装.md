---
notion_id: 3aea2efbb18d8104818ed0263a2f2807
notion_url: https://app.notion.com/p/3aea2efbb18d8104818ed0263a2f2807
last_edited_time: 2026-07-31T10:32:11.417Z
synced_at: 2026-07-31T15:59:39.457Z
type: Model
status: Active
domain: Java
source_url: https://jenkov.com/tutorials/java-concurrency/thread-signaling.html
memory: false
review_question: ""
review_answer: ""
---

## 底层链条
Java 的 `wait()/notify()` 直接映射到 POSIX 的 `pthread_cond_wait/pthread_cond_signal`，连"被唤醒后要重新抢锁才能返回"这个细节都一样。`wait()` 内部三步原子操作——入等待队列、释放 mutex、挂起——要求调用者**已持有 mutex**，这就是 Java 要求 wait/notify 必须在 synchronized 块里的根因。违反则抛 `IllegalMonitorStateException`，不是 Java 刁难，是底层转不起来。
## wait/notify 的根问题：无状态
`notify()` 不排队，信号发出时没人等就丢。这是设计，不是 bug——pthread 条件变量天生无状态。四个使用惯例的本质都是给无状态机制**补状态**：
- `boolean wasSignalled`：给信号加一块记忆，变无状态为有状态
- `while` 循环：醒来后重新检查条件。真正高频防住的不是 POSIX 严格意义的 spurious wakeup（现代平台极少），而是"唤醒后条件被并发线程消费"——多个等待方/唤醒方的真实系统里天天发生。Jenkov 把它挂靠在"虚假唤醒"名下，其实工程价值在并发消费
- synchronized 块：底层 pthread 要求，三步原子操作的前提
- 专用监视器对象：避免字符串常量被 JVM 合并导致跨实例共享
## JUC 的统一招数
给信号加持久化的共享状态存储，丢失信号问题自动消失：
- `Semaphore`：`int permits` 计数，信号被计数器记住
- `BlockingQueue`：队列本身是状态，生产者放进去的东西不会因消费者没来就消失
- `CountDownLatch`：`int count`，`countDown()` 减一
**只要给信号加状态存储，丢失信号就消失**。`boolean` 是最简版，JUC 是完整版。自己用 wait/notify 写，很容易忘加状态、忘 while、忘同步块；JUC 把这些封装掉了。
## 虚拟线程时代叠加
`synchronized` 会 pin 住虚拟线程，`ReentrantLock` 不会。wait/notify + synchronized 这套老组合在虚拟线程时代主动拖后腿。
