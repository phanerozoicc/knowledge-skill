---
notion_id: 372a2efbb18d8199af51d9ca7e7251eb
notion_url: https://app.notion.com/p/372a2efbb18d8199af51d9ca7e7251eb
last_edited_time: 2026-06-01T10:37:48.020Z
synced_at: 2026-07-31T15:59:39.457Z
type: Insight
status: Draft
domain: JVM
source_url: https://rockthejvm.com/articles/the-ultimate-guide-to-java-virtual-threads
memory: true
review_question: "为什么 synchronized 会钉住（pin）虚拟线程，而 ReentrantLock 不会？如何检测 pinning？"
review_answer: "synchronized 编译为字节码 monitorenter/monitorexit，涉及 native 方法帧。虚拟线程的 Continuation 在做 yield 时无法跨越 native 帧边界。所以 synchronized 内部的阻塞操作无法触发 unmount，虚拟线程被钉在 carrier 上。ReentrantLock 基于 AQS，使用 CAS + LockSupport.park()，park() 是纯 Java 层面的阻塞调用，JVM 可以在此处安全地 unmount 虚拟线程。检测 pinning：-Djdk.tracePinnedThreads=short|full。"
---

## 1. 它解决了什么问题？
在虚拟线程的 synchronized 块或方法内部发生阻塞操作时，虚拟线程无法从 carrier 上 unmount——这个现象叫 pinning（钉住）。当 carrier 池有限时，被钉住的 carrier 无法服务其他虚拟线程，导致整个系统的虚拟线程调度退化为串行执行。
## 2. 它的核心矛盾是什么？
**Java 向后兼容的承诺 vs 虚拟线程调度正确性的需要。**
`synchronized` 从 Java 1.0 就存在。如果让 synchronized 在虚拟线程下行为不同，会破坏语义兼容性。JDK 团队的选择是：保持 synchronized 语义不变，通过工具帮助开发者发现和修复 pinning。
## 3. 它的本质模型是什么？
synchronized 使用 JVM 字节码 monitorenter/monitorexit，涉及 native 帧，虚拟线程的 Continuation 无法在 native 帧边界做 yield；ReentrantLock 基于 AQS 的 CAS + LockSupport.park()，全程在 JVM 内存模型内执行，park() 是可被虚拟线程拦截并 unmount 的阻塞点。
技术栈层次：
- 可以被 yield：Java 方法帧（JVM 管理栈）—— ReentrantLock 的 park() 可 yield ✓
- 不能 yield：Native 方法帧（C 编译器管理栈）—— synchronized 的 monitorenter → native → yield ✗
## 4. 它还能解释什么？
- **Rust async 中的 std::Mutex vs tokio::Mutex**：同一类问题。
- **Kotlin 协程中不能用 synchronized**：在 suspend 函数里用 synchronized，锁等待会阻塞底层线程而非挂起协程。
- **Go 没有这个问题**：因为 Go runtime 完全控制 goroutine 的栈，没有 Java 的 native 帧问题。
## 5. 认知变化
**以前我以为**：synchronized 和 ReentrantLock 只是语法糖的差异，功能等价，选择哪个是代码风格问题。
**现在我认为**：在虚拟线程时代，synchronized 和 ReentrantLock 有本质区别——synchronized 阻止虚拟线程的协作式调度，ReentrantLock 不阻止。这不是风格问题，是调度正确性问题。
## 6. 最终压缩
> synchronized 的 monitorenter/monitorexit 穿过 JVM native 帧，虚拟线程的 Continuation 无法在 native 帧上做 yield——所以 synchronized 内部的阻塞操作会 pin 住 carrier。ReentrantLock 基于纯 Java 的 CAS + LockSupport.park()，park() 是安全的 unmount 点。
