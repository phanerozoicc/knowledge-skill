---
notion_id: "3b1a2efb-b18d-81ff-bd94-cb4d4ffecc33"
notion_url: "https://app.notion.com/p/3b1a2efbb18d81ffbd94cb4d4ffecc33"
last_edited_time: "2026-08-03T02:18:57.099Z"
synced_at: "2026-08-03T02:18:57.099Z"
type: Model
status: Draft
domain: Java
source_url: https://jenkov.com/tutorials/java-concurrency/nested-monitor-lockout.html
memory: true
review_question: 嵌套监视器死锁和普通死锁的根本区别是什么？锁序策略为何对它无效？
review_answer: 普通死锁是锁等待环，锁序打破环即可；嵌套监视器死锁没有环——等待方在 wait() 等信号（不等任何锁），通知方在等外层锁，是单向依赖。wait() 只释放内层锁、不释放外层锁，通知方需要外层锁才能走到 notify，于是永远进不来。锁序对单向依赖无效。JUC 解法：把 await/signal 收进同一把 ReentrantLock 的临界区，通知方只需这一把锁。
---

## 嵌套监视器死锁：wait只放内层锁，外层锁把通知方挡死在门外

**解决的问题：**

持外层锁进入内层锁的临界区后在内层锁上 wait()，会发生什么？为什么这种结构会导致两个线程永久阻塞，而且和普通死锁长得像、根因却不同？

**本质模型：**

wait() 只释放调用它的那把监视器（内层锁），绝不释放外层持有的锁。通知方要走到 notify()，代码结构上必须先拿到外层锁（嵌套 synchronized 的进入条件），但外层锁被等待方死死攥着 → 通知永远发不出 → 等待方永远等不到信号 → 双双永久阻塞。

最小病灶：

```java
synchronized(lockA) {
    synchronized(lockB) {
        lockB.wait();   // 只释放 B，A 还攥着
    }
}
// 通知方需要 lockA 才能走到 lockB.notify()，但 lockA 永远拿不到
```

和普通死锁的根本差别：

- 普通死锁是「锁等待环」：A 等 B 的锁，B 等 A 的锁 → 锁序策略打破环即可
- 嵌套监视器死锁是「混合等待」：等待方在 wait() 里等信号（不在等任何锁），通知方在等外层锁，是单向依赖 → 根本没有环可打破 → 锁序策略完全无效

JUC 的根治方式：ReentrantLock + Condition 把 await/signal 收进同一把锁的临界区，通知方拿到这一把锁就能 signal，不再依赖任何「外层锁」：

```java
lock.lock();
try { while(!cond) condition.await(); }
finally { lock.unlock(); }
// unlock 时同样只需这一把锁 → 通知方从不被额外的锁挡死
```

**权衡：**

牺牲嵌套锁内做条件等待的便利，换取「通知方不会被等待方攥着的锁挡死」。自己用 synchronized 嵌套 wait/notify 必然踩这个坑；JUC 把 wait/notify 从「每对象一个监视器」的散点结构，统一收敛进「一把锁 + N 个 Condition」的框架，从结构上消除嵌套监视器死锁的可能。

**迁移：**

通用规则：wait() 时手里攥着的所有锁，通知方都必须能不依赖这些锁走到 notify()。等价说法：不要在嵌套锁的内层做 wait()，除非通知方完全不依赖外层锁。这条规则不只适用于 Java——C++ 的 condition_variable 同样要求 await 时只持一把锁并释放它，POSIX 条件变量要求持锁者为通知方留路，原理一致。凡是「等待方放开通知方要走的门、却没放它真正需要的那道门」的结构都中招。

## 6. 最终压缩

> wait() 只释放内层锁，外层锁把通知方挡死在门外——这不是锁等待环，锁序策略治不了；治它要靠把 wait/notify 收进同一把锁的临界区。
