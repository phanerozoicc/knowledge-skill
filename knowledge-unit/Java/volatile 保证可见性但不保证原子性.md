---
notion_id: 36ba2efbb18d81f4a48aff1deb6e9bc9
notion_url: https://app.notion.com/p/36ba2efbb18d81f4a48aff1deb6e9bc9
last_edited_time: 2026-05-25T15:56:15.013Z
synced_at: 2026-07-31T15:59:39.457Z
type: Insight
status: Active
domain: Java
source_url: 
memory: true
review_question: "volatile 能保证 count++ 的线程安全吗？为什么？"
review_answer: "不能。volatile 只保证可见性（happens-before），不保证原子性。count++ 是 read-modify-write，中间可以被其他线程插入。需要 synchronized 或 AtomicInteger。"
---

## 1. 它解决了什么问题？
开发者容易误认为 volatile 变量可以安全地做 count++，因为「volatile 保证可见性」。
## 2. 它的核心矛盾是什么？
可见性和原子性是两个独立的保证。volatile 只建立了 happens-before 关系（可见性），但 count++ 是 read-modify-write 三步操作，中间可以被其他线程插入。
## 3. 它的本质模型是什么？
- **volatile 保证**：一个线程的写对另一个线程的读可见（happens-before）
- **volatile 不保证**：read-modify-write 操作的原子性
- **典型反例**：count++ 实际是 read → modify → write 三步，线程 A 读到 0，线程 B 也读到 0，各写回 1，结果是 1 而非 2
- **正确做法**：synchronized 或 AtomicInteger / LongAdder
volatile 的正确使用场景：
- stop flag（boolean）
- readiness marker
- 单值发布（one-time publication）
## 4. 它还能解释什么？
- 为什么 volatile boolean flag 做停止标志是安全的（单写多读，非复合操作）
- 为什么 DCL 需要 volatile（引用发布，不是复合更新）
- Atomic 类的 CAS 如何在可见性基础上提供原子性
## 5. 认知变化
**以前我以为：** volatile 就是轻量级锁，能用 volatile 的地方就不需要 synchronized。
**现在我认为：** volatile 和 synchronized 解决不同问题。volatile 解决可见性，synchronized 解决原子性+可见性。两者不可替代。
## 6. 最终压缩
> volatile 保证 happens-before（可见性），不保证 read-modify-write 原子性。count++ 需要 synchronized 或 Atomic 类。
