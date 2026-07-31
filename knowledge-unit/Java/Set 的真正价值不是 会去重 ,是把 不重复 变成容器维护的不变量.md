---
notion_id: 37fa2efbb18d817f9c16e0387c304214
notion_url: https://app.notion.com/p/37fa2efbb18d817f9c16e0387c304214
last_edited_time: 2026-06-14T13:22:50.216Z
synced_at: 2026-07-31T15:59:39.457Z
type: Insight
status: Active
domain: Java
source_url: https://www.digitalocean.com/community/tutorials/java-set
memory: false
review_question: ""
review_answer: ""
---

## 1. 它解决了什么问题？
既然 List 加 contains 检查也能去重,为什么要用 Set?
## 2. 它的核心矛盾是什么？
用 List 去重,不变量所有权在调用方(每次 add 前必须手动 contains,忘一次就破);用 Set,不变量收进容器,调用方不再负责。
## 3. 它的本质模型是什么？
Set 买的不是"去重操作",而是"不重复是一个被容器结构性保证的不变量"。代价是元素必须满足 equals/hashCode 稳定。
## 4. 它还能解释什么？
任何"把不变量从调用方手里收进容器/类型"的设计——如不可变集合(Guava/Java 9 List.of)把"不可变"收进类型、数据库约束把"合法状态"收进 schema。
## 5. 认知变化
无明显 before/after,作为独立 Insight 记录。
## 6. 最终压缩
> Set 买的不是"会去重",是把"不重复"从调用方责任变成容器结构性保证的不变量。
