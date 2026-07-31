---
notion_id: 3aca2efbb18d817c9f86fe529c79cb7a
notion_url: https://app.notion.com/p/3aca2efbb18d817c9f86fe529c79cb7a
last_edited_time: 2026-07-29T09:27:31.512Z
synced_at: 2026-07-31T15:59:39.457Z
type: Insight
status: Active
domain: Java
source_url: https://jenkov.com/tutorials/java-concurrency/thread-signaling.html
memory: false
review_question: ""
review_answer: ""
---

## wait/notify 的三个陷阱：丢失信号、虚假唤醒、共享监视器

**解决的问题：**

线程间通过 wait()/notify() 通信时，有三个非显而易见的失败模式：通知在 wait() 之前到达导致永久等待、线程无缘无故被唤醒、多个实例共享同一个字符串监视器导致交叉干扰

**本质模型：**

1) 丢失信号(Missed Signal)：notify() 不排队——如果通知到达时没有线程在 wait()，信号就永远丢失。解：用 boolean 变量存储信号状态，doNotify() 先设标志再 notify()，doWait() 看到标志已设就不再 wait()。
2) 虚假唤醒(Spurious Wakeup)：即使没有 notify()/notifyAll() 调用，线程也可能从 wait() 中醒来。这是 JVM/OS 层面的现象，无法消除只能防御。解：将 if(!wasSignalled) 替换为 while(!wasSignalled)，被虚假唤醒后重新检查条件，条件不满足则继续 wait()。while 循环同时解决了 notifyAll() 唤醒多个线程但只有一个能继续的问题。
3) 共享监视器对象：用常量字符串如 "" 或全局对象做监视器时，JVM 编译器会将相同内容的字符串常量合并为同一对象——两个不相关的 MyWaitNotify 实例会共享同一把锁。一个实例的 notify() 可能唤醒另一个实例的等待线程，该线程醒来后发现信号不匹配又睡回去，而真正的目标线程永远收不到信号。

**权衡：**

这些保护模式加了少量代码（boolean 标志 + while 循环 + 专用监视器对象），代价近乎为零，但缺了任何一个都可能在生产环境出现难以复现的偶发 hang。

**迁移：**

任何基于条件变量的线程间通知机制都有这三个问题，不只是 Java——C++ 的 condition_variable 同样需要 while 循环防虚假唤醒，Go 的 channel 通过内置缓冲避免了丢失信号但仍有自己的陷阱。跨语言的通用原则是：永远在循环中等待条件，永远用显式状态变量存储信号。


> 注：此页面在 Notion 中正文为空，结构化内容（Problem/Essence/Tradeoff/Transfer/Boundary）存储于 properties 字段，本地文件由 properties 重建。推回 Notion 时这些字段会同步。
