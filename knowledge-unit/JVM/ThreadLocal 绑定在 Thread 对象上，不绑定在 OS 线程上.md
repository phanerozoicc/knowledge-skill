---
notion_id: 372a2efbb18d81d4acf1d9f5e949eba9
notion_url: https://app.notion.com/p/372a2efbb18d81d4acf1d9f5e949eba9
last_edited_time: 2026-06-01T10:37:48.089Z
synced_at: 2026-07-31T15:59:39.457Z
type: Update
status: Draft
domain: JVM
source_url: https://rockthejvm.com/articles/the-ultimate-guide-to-java-virtual-threads
memory: true
review_question: "在虚拟线程环境下，ThreadLocal 的值到底绑定在哪里？虚拟线程在不同 carrier 线程之间 mount/unmount 会导致 ThreadLocal 数据串扰吗？"
review_answer: "ThreadLocal 的值存在 Thread 对象的 threadLocals 字段中（堆内存 ThreadLocalMap），从 Java 1.2 起就这样。虚拟线程也是 Thread，有自己的 threadLocals。mount/unmount 换的是 carrier，但 Thread 对象不变，ThreadLocal.get() 读的是虚拟线程的 threadLocals，不是 carrier 的。所以不串扰。真正的风险是百万虚拟线程各存一份 ThreadLocal 副本导致的内存膨胀。"
---

## 1. 它解决了什么问题？
这是一个认知纠偏。在虚拟线程出现之前，Java 开发者习惯说"ThreadLocal 绑定到当前线程"，而"当前线程"又恰好等于 OS 线程。这个等式在虚拟线程出现后被打破了：如果 ThreadLocal 真的绑在 OS 线程上，那 carrier 复用时就会出现严重的数据串扰。但事实并非如此。
## 2. 它的核心矛盾是什么？
**正确性没问题，但内存效率变差了。**
ThreadLocal 的设计从 Java 1.2 起就没变过——值存储在 Thread 对象的 threadLocals 字段中。这个设计在虚拟线程下仍然正确工作，没有任何串扰。但虚拟线程让 Thread 对象数量从千级膨胀到百万级，即使每个 ThreadLocal 值只有几 KB，乘上百万也变成 GB 级。
## 3. 它的本质模型是什么？
ThreadLocal 的值存在 Thread.threadLocals 字段——一个堆内的 ThreadLocalMap。虚拟线程 mount/unmount 换的是底层的 carrier 线程，但执行的 Thread 对象（虚拟线程实例）不变，所以 ThreadLocal 值始终跟着虚拟线程走。挂载到不同 carrier 不会混淆数据。
## 4. 它还能解释什么？
- **Go 的 context.Context**：Go 没有 ThreadLocal，所有请求级数据通过 context 显式传递，避免了内存膨胀。
- **Kotlin 协程的 CoroutineContext**：context 跟着协程走，数据不会丢也不会串扰。
- **Scoped Value（Java 21+）**：值绑定在代码块而非线程上，代码块结束值立即不可达。
## 5. 认知变化
**以前我以为**：ThreadLocal 绑定到操作系统线程，虚拟线程在不同 carrier 之间 mount/unmount 可能会读到彼此的 ThreadLocal 数据。
**现在我认为**：ThreadLocal 从 Java 1.2 起就一直存储在 Thread 对象的 threadLocals 字段。虚拟线程也是 Thread，有自己的 threadLocals。不同虚拟线程先后被同一个 carrier 执行，各自的数据完全隔离。真正的风险不是数据串扰，而是百万虚拟线程各存一份 ThreadLocal 副本导致的内存膨胀。
## 6. 最终压缩
> ThreadLocal 的值存在 Thread.threadLocals（堆内存 Map），从 Java 1.2 起就这样。虚拟线程也是 Thread，有自己的 threadLocals，mount/unmount 换 carrier 不改变 Thread 对象，所以数据不串扰。真正的问题是百万虚拟线程同时持有 ThreadLocal 副本导致的内存膨胀。
