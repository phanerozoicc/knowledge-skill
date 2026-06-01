# Knowledge Skill

基于 Claude Code 的交互式知识捕获与压缩工具。将学习材料（文章、代码、思考）通过认知压缩流程提炼为结构化知识单元，持久化到 Notion，并为关键概念自动生成艾宾浩斯复习卡片。

## 工作流程

1. **输入** — 用户提供文章、URL、代码片段或想法
2. **压缩/讨论** — 通过四问思考管线（问题、本质、权衡、迁移）进行知识压缩，支持直接压缩和讨论两种模式
3. **审阅确认** — 用户确认生成的知识单元
4. **写入 Notion** — 将知识单元写入 Knowledge Units 数据库
5. **生成复习卡片** — 为标记为需要记忆的单元自动创建艾宾浩斯复习卡片

## 项目结构

```
.claude/
├── settings.json              # 项目配置（启用的插件）
├── settings.local.json        # 本地权限配置（允许的 MCP 工具）
└── skills/
    └── knowledge-modeling/
        ├── SKILL.md           # 主 Skill 定义
        └── references/
            ├── notion-schema.md    # Notion 数据库结构与字段定义
            ├── review-rules.md     # 艾宾浩斯复习卡片生成规则
            └── unit-patterns.md    # 知识单元类型指南与反模式
```

## Skill

### knowledge-modeling

交互式学习伴侣 Skill。当用户分享学习材料时触发，引导用户完成认知压缩流程，并将结果写入 Notion Knowledge Units 系统。

**支持的输入类型：** 文章、技术文档、代码、读书笔记、用户自己的思考或调试过程。

**知识单元类型：** Raw → Insight → Model → Principle → Update → Reference，支持渐进式提炼。

## MCP 工具

### Notion（notion-workspace-plugin）

用于知识持久化的核心 MCP 服务。

| 工具 | 用途 |
|------|------|
| `notion-search` | 搜索已有的知识单元 |
| `notion-fetch` | 获取数据库结构和页面内容 |
| `notion-create-pages` | 创建知识单元和复习卡片 |
| `notion-update-page` | 更新已有知识单元 |
| `notion-update-data-source` | 修改数据库结构 |
| `notion-move-pages` | 移动页面 |

**Notion 数据库：**

- **Knowledge Units** — 知识单元主库，包含 Type、Status、Domain、Problem、Essence、Tradeoff、Transfer 等字段
- **艾宾浩斯记忆** — 间隔复习卡片库，与 Knowledge Units 通过 Relation 关联

## 使用方式

在 Claude Code 中打开此项目目录，直接粘贴学习材料即可触发 knowledge-modeling Skill：

```
# 直接压缩
帮我压缩这篇文章：https://example.com/article

# 先讨论再压缩
讨论一下 volatile 关键字

# 整理笔记
整理这个知识：[粘贴代码或笔记]
```
