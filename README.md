# Knowledge Skill

基于 Codex 的交互式知识捕获、压缩与复习工具。将学习材料（文章、代码、思考）通过认知压缩流程提炼为结构化知识单元，持久化到 Notion，并为关键概念自动生成艾宾浩斯复习卡片。

## 工作流程

1. **输入** — 用户提供文章、URL、代码片段或想法
2. **压缩/讨论** — 通过四问思考管线（问题、本质、权衡、迁移）进行知识压缩，支持直接压缩和讨论两种模式
3. **审阅确认** — 用户确认生成的知识单元
4. **写入 Notion** — 将知识单元写入 Knowledge Units 数据库
5. **生成复习卡片** — 为标记为需要记忆的单元自动创建艾宾浩斯复习卡片
6. **间隔复习** — 基于艾宾浩斯卡片库进行主动回忆训练

## 项目结构

```
.agents/
└── skills/
    ├── knowledge-modeling/
    │   ├── SKILL.md                    # 知识捕获与压缩 Skill
    │   └── references/
    │       ├── notion-schema.md        # Notion 数据库结构与字段定义
    │       ├── review-rules.md         # 艾宾浩斯复习卡片生成规则
    │       └── unit-patterns.md        # 知识单元类型指南与反模式
    └── knowledge-review/
        ├── SKILL.md                    # 间隔复习 Skill
        └── references/
            ├── ebbinghaus-schema.md    # 艾宾浩斯三库 Schema 定义
            └── review-feedback.md      # 复习反馈策略与教学技巧
```

## Skills

### knowledge-modeling

交互式学习伴侣 Skill。当用户分享学习材料或提出学习需求时触发，引导用户完成认知压缩流程，并将结果写入 Notion Knowledge Units 系统。

**触发方式：**
- "一起学习", "帮我学习", "学习一下", "我来学"
- "整理这个知识", "帮我压缩", "压缩一下"
- "讨论一下 XXX", "聊聊 XXX", "研究一下 XXX"
- "看看这篇文章", "读一下这个"
- "和我一起看", "一起研究"

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
| **Knowledge Units** | 知识单元主库，包含 Type、Status、Domain、Problem、Essence、Tradeoff、Transfer 等字段 |
| **艾宾浩斯卡片库** | 间隔复习卡片库，与 Knowledge Units 通过 Relation 关联 |
| **艾宾浩斯复习记录** | 复习会话日志，记录每次复习的结果 |

## 使用方式

在 Codex 中打开此项目目录，直接输入即可触发对应 Skill：

```
# 学习和捕获知识（触发 knowledge-modeling）
帮我学习一下 Java 虚拟线程
讨论一下 volatile 关键字
帮我压缩这篇文章：https://example.com/article

# 间隔复习（触发 knowledge-review）
帮我复习
今天该复习什么
测验一下 JVM 相关的知识
```
