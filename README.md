# Knowledge Skill

基于 Codex 的交互式知识捕获、压缩与复习工具。将学习材料（文章、代码、思考）通过认知压缩流程提炼为结构化知识单元，持久化到 Notion，并为关键概念自动生成艾宾浩斯复习卡片。

## 工作流程

两个阶段：**学** 与 **沉淀**。teach 负责学会，knowledge-modeling 负责沉淀到 Notion。

**学习阶段（teach）** — 在本地按主题建工作区，通过讨论、资源、自包含 HTML 课把一个主题学透，留下 MISSION、learning-records、glossary 等过程材料。

**沉淀阶段（knowledge-modeling）** — 接收输入，先回读 Notion 已有知识做去重/关联，再通过四问思考管线压缩，写入 Knowledge Units，并为需要记忆的单元生成艾宾浩斯卡片。沉淀成功后归档 teach 的本地记录（保留为备份，不删除）。

```
teach（学会，本地工作区）
        │  理解稳定后交接
        ▼
knowledge-modeling（沉淀）
        ├── Step 0：回读 Notion + teach 本地记录 → 去重/关联
        ├── 压缩/讨论 → 审阅确认
        ├── 写入 Notion Knowledge Units
        ├── 生成艾宾浩斯卡片
        └── 归档 teach 本地记录（标 archived → Notion URL）
        │
        ▼
knowledge-review（间隔复习，主动回忆）
```

## 项目结构

```
.agents/  （.claude/ 下保持字节级镜像）
└── skills/
    ├── teach/                          # 学习阶段 Skill（显式 /teach 调用）
    │   ├── SKILL.md
    │   └── references/
    │       ├── MISSION-FORMAT.md       # 学习使命文档格式
    │       ├── LEARNING-RECORD-FORMAT.md  # ADR 风格学习记录 + 归档标记
    │       ├── GLOSSARY-FORMAT.md      # 术语表格式
    │       ├── RESOURCES-FORMAT.md     # 高可信资源格式
    │       └── LESSON-FORMAT.md        # 自包含 HTML 课格式
    ├── knowledge-modeling/             # 沉淀阶段 Skill
    │   ├── SKILL.md
    │   └── references/
    │       ├── notion-schema.md        # Notion 数据库结构与字段定义
    │       ├── review-rules.md         # 艾宾浩斯复习卡片生成规则
    │       └── unit-patterns.md        # 知识单元类型指南与反模式
    └── knowledge-review/              # 间隔复习 Skill
        ├── SKILL.md
        └── references/
            ├── ebbinghaus-schema.md    # 艾宾浩斯三库 Schema 定义
            └── review-feedback.md      # 复习反馈策略与教学技巧
```

## Skills

### teach

学习阶段 Skill。把一个主题学透：建立使命、收集高可信资源、写自包含 HTML 课、用 ADR 风格记录真正掌握的理解。显式调用，不自动触发，避免和 knowledge-modeling 的词冲突。学完后交接给 knowledge-modeling 沉淀到 Notion。

**触发方式：** 显式 `/teach`，或 "教我 XXX", "我想学 XXX", "带我学 XXX", "给我讲讲 XXX"。
**工作区：** 当前目录下每个学习主题一个文件夹（一个 mission 一个文件夹）。本地文件是过程材料 + 写入前备份；**Notion Knowledge Units 是唯一真相源**。

**设计要点（取自 mattpocock/teach 并改造）：**
- **最近发展区**：每次开课先回读 learning-records，据此判断该教什么、多深。
- **storage vs fluency**：通过检索练习、间隔、交叉追求长期记忆，而非当下流畅的虚假掌握感。
- **coverage ≠ learning**：只在有证据（答对题、纠正误解）时才写 learning-record，讲过不等于学会。
- **回读驱动**：沉淀前回读已有知识，抑制重复建孤岛。

### knowledge-modeling

沉淀阶段 Skill。接收输入后**先回读 Notion 已有知识**做去重/关联（避免重复建孤岛），再引导认知压缩流程，写入 Notion Knowledge Units。

**触发方式：**
- "一起学习", "帮我学习", "学习一下", "我来学"
- "整理这个知识", "帮我压缩", "压缩一下"
- "讨论一下 XXX", "聊聊 XXX", "研究一下 XXX"
- "看看这篇文章", "读一下这个"
- "和我一起看", "一起研究"

**回读桥（Step 0）：** 写入前用 `notion-search` 搜 Knowledge Units，发现重叠时默认走向 Update（填 Before/After）或 Related Units 关联，而非新建。teach 交接时还会读取主题文件夹的 learning-records 作为输入。

**支持的输入类型：** 文章、技术文档、代码、读书笔记、用户自己的思考或调试过程。

**知识单元类型：** Raw -> Insight -> Model -> Principle -> Update -> Reference，支持渐进式提炼。

### knowledge-review

间隔复习 Skill。基于艾宾浩斯卡片库进行主动回忆训练，支持按到期时间、按主题、随机抽测等多种复习模式。

**触发方式：**
- "复习", "帮我复习", "开始复习", "复习一下"
- "今天该复习什么", "有什么要复习的"
- "检查记忆", "测验一下", "测试一下"
- "一起复习", "复习卡片"

**复习流程：** 逐题呈现 -> 用户主动回忆 -> 自评记忆质量（记住/模糊/忘了）-> 针对性反馈 -> 会话总结。

**反馈策略：** 模糊时补充关键区分点，忘了时从 Thinking Pipeline 重新讲解，记住了时拓展深层联系。

## Notion 数据库

| 数据库 | 用途 |
|--------|------|
| **Knowledge Units** | 知识单元主库，**唯一真相源**。包含 Type、Status、Domain、Problem、Essence、Tradeoff、Transfer 等字段 |
| **艾宾浩斯卡片库** | 间隔复习卡片库，与 Knowledge Units 通过 Relation 关联 |
| **艾宾浩斯复习记录** | 复习会话日志，记录每次复习的结果 |

## 使用方式

在 Codex 中打开此项目目录，直接输入即可触发对应 Skill：

```
# 先学会一个主题（显式触发 teach）
/teach 我想搞懂 TCP 拥塞控制
教我 JVM 的 happens-before

# 沉淀知识（触发 knowledge-modeling，会先回读 Notion）
帮我学习一下 Java 虚拟线程
讨论一下 volatile 关键字
帮我压缩这篇文章：https://example.com/article

# 间隔复习（触发 knowledge-review）
帮我复习
今天该复习什么
测验一下 JVM 相关的知识
```
