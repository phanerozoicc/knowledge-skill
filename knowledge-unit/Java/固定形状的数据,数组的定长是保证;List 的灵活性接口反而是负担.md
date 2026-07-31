---
notion_id: 37fa2efbb18d81e596f9eebb5b8eee09
notion_url: https://app.notion.com/p/37fa2efbb18d81e596f9eebb5b8eee09
last_edited_time: 2026-06-14T09:12:46.151Z
synced_at: 2026-07-31T15:59:39.457Z
type: Model
status: Active
domain: Java
source_url: https://jenkov.com/tutorials/java/arrays.html
memory: true
review_question: "什么场景下数组比 List 更合适?为什么 List 的灵活性在那里反而是负担?"
review_answer: "数据形状固定时(如 2D 坐标、N 维矩阵):List 的 add/remove 在语义上无意义且危险(手滑加一维编译器不拦),数组的定长约束把形状焊进类型;同时原始类型数组无装箱、连续内存,在热循环里快且省内存。List 的灵活性接口在固定数据上是负债。"
---

## 1. 它解决了什么问题？
既然有 List,什么时候反而该用数组?
## 2. 它的核心矛盾是什么？
List 接口提供的灵活性(add/remove/可替换实现),和"固定形状数据不想要灵活性",是同一件事的两面。让 List 在动态数据上发光的 add/remove,正是它在固定数据上碍事的同一套 API。
## 3. 它的本质模型是什么？
数据形状本身固定时(坐标、矩阵),List 的 add/remove 是语义上无意义且危险的 API;数组的"不能改长度"从约束变成形状保证,外加原始类型无装箱的性能/内存优势。
## 4. 它还能解释什么？
DB 定 schema 列 vs JSON/EAV;C 的 struct vs malloc——形状可固定时,固定本身就是收益。
## 5. 认知变化
**以前我以为:** List 比 array 强在长度可变,List 是"更好的数组"。
**现在我认为:** 动态数据选 List 的灵活性,固定形状数据选数组的约束;两者没有绝对优劣,边界在"数据形状是否固定"。
## 6. 最终压缩
> 形状固定的数据,数组的定长是保证而非缺陷,List 的灵活性接口在那里是负债。
