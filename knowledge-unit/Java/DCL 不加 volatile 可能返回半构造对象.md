---
notion_id: 36ba2efbb18d81d2b565cd743681393f
notion_url: https://app.notion.com/p/36ba2efbb18d81d2b565cd743681393f
last_edited_time: 2026-05-25T15:56:15.056Z
synced_at: 2026-07-31T15:59:39.457Z
type: Insight
status: Active
domain: Java
source_url: 
memory: true
review_question: "为什么 DCL 中的单例引用必须加 volatile？"
review_answer: "因为构造函数的写可能重排序到引用赋值之后。不加 volatile，另一个线程可能看到非 null 引用但对象未完全构造。"
---

## 1. 它解决了什么问题？
Double-Checked Locking 看似正确：先检查 null，再加锁，再检查 null，再创建。但在没有 volatile 的情况下可能返回半构造的对象。
## 2. 它的核心矛盾是什么？
构造函数的写操作和引用赋值之间没有 happens-before 关系，编译器/CPU 可能重排序。
## 3. 它的本质模型是什么？
```java
// 看似安全的 DCL
if (instance == null) {           // ① 第一次检查
    synchronized (Singleton.class) {
        if (instance == null) {    // ② 第二次检查
            instance = new Singleton(); // ③ 构造+赋值
        }
    }
}
return instance;
```
步骤 ③ 实际包含：
1. 分配内存空间
2. 调用构造函数（初始化字段）
3. 将引用指向内存空间
其中 2 和 3 可能被重排序（变成 1→3→2）。线程 A 执行到 3（引用非 null），线程 B 在 ① 看到 instance != null，直接返回了一个未完全构造的对象。
**volatile 解决**：volatile 写操作前的所有写不会被重排序到 volatile 写之后。保证了 2 happens-before 3。
## 4. 它还能解释什么？
- 任何 lazy initialization 模式都需要考虑重排序
- 为什么 Java 5 之前的 DCL 即使加 volatile 也不一定安全（旧 JMM 语义不够强）
- 为什么推荐用静态内部类或 enum 实现单例（类加载机制天然保证线程安全）
## 5. 认知变化
**以前我以为：** DCL 加不加 volatile 无所谓，因为 synchronized 已经保证同步了。
**现在我认为：** synchronized 保证的是进入同步块时的互斥，但第一次检查在同步块外面。引用赋值和构造函数的写可以被重排序，需要 volatile 防止。
## 6. 最终压缩
> 构造函数的写可能重排序到引用赋值之后。不加 volatile，另一个线程可能看到非 null 引用但对象未完全构造。
