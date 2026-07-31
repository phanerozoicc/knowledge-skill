---
notion_id: 37fa2efbb18d815cb019fd1902de17b7
notion_url: https://app.notion.com/p/37fa2efbb18d815cb019fd1902de17b7
last_edited_time: 2026-06-14T09:12:46.128Z
synced_at: 2026-07-31T15:59:39.457Z
type: Insight
status: Active
domain: Java
source_url: https://jenkov.com/tutorials/java-collections/list.html
memory: false
review_question: ""
review_answer: ""
---

## 1. 它解决了什么问题？
ArrayList 和普通数组到底"差"在哪?是不是只差长度?
## 2. 它的核心矛盾是什么？
封装掉手写搬移/扩容的脏活 vs. 代价没消失只是藏进实现(add/remove 仍是 O(n))。
## 3. 它的本质模型是什么？
ArrayList 不是"更好的数组",而是 数组实现 + 自动扩容 + List 接口契约 三件打包;其中接口契约(可替换 ArrayList/LinkedList)是最值钱的那件,扩容只是顺带便利。
## 4. 它还能解释什么？
String(不可变) vs StringBuilder(可变) 是同一类"把约束藏到抽象背后"的切分。
## 5. 认知变化
无明显 before/after,作为独立 Insight 记录。
## 6. 最终压缩
> ArrayList = 数组实现 + 自动扩容 + List 接口契约,接口契约是其中最值钱的一件。
