---
notion_id: 37fa2efbb18d816fa58edec42a47afff
notion_url: https://app.notion.com/p/37fa2efbb18d816fa58edec42a47afff
last_edited_time: 2026-06-14T13:22:36.431Z
synced_at: 2026-07-31T15:59:39.457Z
type: Insight
status: Active
domain: Java
source_url: https://jenkov.com/tutorials/java-collections/set.html
memory: true
review_question: "为什么把可变对象放进 HashSet 会导致不重复的不变量破裂?Java 里哪些类型的对象放 Set 最安全,为什么?"
review_answer: "HashSet 靠 equals/hashCode 判断重复。可变值对象放入后被修改 → hashCode 漂移 → Set 找不到它 → 能塞进\"重复\"元素,不变量静默破裂。最安全的是不可变值类型(String/Integer/record),因为不可变保证 hash 在生命周期内稳定,值相等契约不会被违反。"
---

## 1. 它解决了什么问题？
Set 不允许重复,这个不变量到底是谁维护的?什么情况下会坏?
## 2. 它的核心矛盾是什么？
按值去重(需要值 hash)与 hash 稳定(需要不可变)互相制约。按身份算 hash(数组/默认 Object)虽然稳定,但无法按值去重;按值算 hash(POJO/Entity)能去重,但元素一旦可变,放入后修改会影响 hash,Set 找不到它、能塞进重复。
## 3. 它的本质模型是什么？
Set 的唯一性靠元素的 equals/hashCode 判断。可变值对象放入后被修改 → hashCode 漂移 → Set 找不到它 → 能塞进"重复"元素,不变量静默破裂,无异常。唯一出路:让按值计算 hash 的对象不可变。这正是 Java 里 Set 友好的值类型(String/Integer/record)全部不可变的原因。
## 4. 它还能解释什么？
HashMap 的 key 同理;数据库唯一索引之所以稳,是因为被索引的列一般不会改(或改了会级联);任何"按值去重"的容器都隐含"被去重的值应不可变"这一前提。
## 5. 认知变化
**以前我以为:** Set 自动去重,放进去就安全了。
**现在我认为:** Set 的不变量是 Set 和元素的协作契约;可变值对象会违约,不可变值对象才真正成立。
## 6. 最终压缩
> Set 的唯一性不是 Set 单独维护的,是它和元素的 equals/hashCode 的合同;可变值对象会静默违约,不可变值类型(String/Integer/record)才真正安全。
