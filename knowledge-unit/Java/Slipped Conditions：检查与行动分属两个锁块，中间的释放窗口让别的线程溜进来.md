---
notion_id: "3b1a2efb-b18d-818e-a270-c402ba3dd053"
notion_url: "https://app.notion.com/p/3b1a2efbb18d818ea270c402ba3dd053"
last_edited_time: "2026-08-03T02:18:57.849Z"
synced_at: "2026-08-03T02:18:57.849Z"
type: Model
status: Draft
domain: Java
source_url: https://jenkov.com/tutorials/java-concurrency/slipped-conditions.html
memory: true
review_question: Slipped Conditions 的根因是什么？它和 Nested Monitor Lockout、Missed Signal 为何说是同一根因的三个面？JUC 如何一次性根治？
review_answer: 根因是 synchronized 只能保证单块内原子，而「检查/修改/等待/通知」四动作一旦跨块就有释放窗口：检查与修改分离 → Slipped；等待与通知分属嵌套锁 → Nested Monitor Lockout；通知早于等待 → Missed Signal。三者在 synchronized 原语下治一个冒一个。JUC 用 ReentrantLock + Condition 把整个状态机收进一把锁，并用 while+await 的强制范式让「检查-等待-重检」不可分割，从 API 层一次性消除所有窗口。
---

## Slipped Conditions：检查与行动分属两个锁块，中间的释放窗口让别的线程溜进来

**解决的问题：**

一个锁的 lock() 把「检查是否已锁」和「标记为已锁」写在两个相邻 synchronized 块里，为何两个线程能同时进门、互斥被击穿？

**本质模型：**

synchronized 只能保证单个块内原子，不能保证多个块之间的原子。把「检查条件」和「设置条件」分在两个块里，块之间锁会释放，别的线程能挤进这个窗口、读到还没被修改的旧状态、也通过检查。于是多个线程同时拿到锁，互斥击穿。

最小病灶：

```java
synchronized(this){ while(isLocked) wait(); }   // 块1 只检查
synchronized(this){ isLocked = true; }          // 块2 才设置，两块间锁已释放
```

→ A 出块1 被抢占，B 进块1 也看到 false，两人都进块2 都设 true。

这只是「检查-修改-等待-通知」四动作跨 synchronized 块失原子性的一族问题之一。同一根因还长出另外两个面孔：

- 检查与修改分离 → 本单元（Slipped Conditions）
- 等待与通知分属嵌套锁 → Nested Monitor Lockout（wait 只放内层锁，通知方被外层锁挡死）
- 通知早于等待 → Missed Signal（信号飘进虚空）

三者在 synchronized 原语下治一个必冒一个。JUC 的根治方式：ReentrantLock + Condition 用 while+await 把「检查-等待-被唤醒重检」打包成一次不可分割的持锁，从 API 层不给你留窗口：

```java
lock.lock();
try { while(!cond) condition.await(); /* 动作 */ }
finally { lock.unlock(); }
```

**权衡：**

牺牲编排自由度（检查和修改必须收进同一把锁的同一次持锁），换取状态一致。自己用 synchronized 拼接这四个动作，必然在某一端漏风；用 JUC 现成抽象，坑已经被焊死。

**迁移：**

「检查与行动之间不能有可见性窗口」是所有并发协调的通则。数据库的 SELECT FOR UPDATE 把「读到 + 上锁」原子化，正是为了消灭 SQL 层的 slipped conditions；Redis 的 SETNX / Lua 脚本把「判断 key 不存在 + 写入」压成一次原子调用，同一思路。凡是要「先看一眼再动手」的并发场景，都要问：看和动之间，锁松过没？

## 6. 最终压缩

> synchronized 只能保证单块内原子，检查与行动一旦分块，中间的释放窗口就让别的线程溜进来——这是和 Nested Monitor Lockout / Missed Signal 同根的三个面孔之一，治它要靠 JUC 的 while+await 把「检查-等待-重检」焊成一次不可分割的持锁。
