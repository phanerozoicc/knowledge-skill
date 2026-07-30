# Knowledge Skill

基于 Claude Code 的交互式知识学习、写作与思考工具集。包含认知压缩、间隔复习、结构化写作、想法压力测试等多种 Skill，知识持久化到 Notion 并生成艾宾浩斯复习卡片。

## 项目结构

```
.
├── .mcp.json                            # MCP Server 配置（Notion）
├── .cursor/
│   ├── mcp.json                         # Cursor MCP（与 .mcp.json 对齐）
│   └── skills/                          # Cursor Skill 镜像（软链 → .agents/skills/）
├── SKILL.md                             # DeepTutor CLI 使用指南
├── data/                                # DeepTutor 运行时数据（workspace, chat history, settings）
├── .agents/skills/                      # Skill 定义（唯一源；.claude/.cursor/skills 为软链镜像）
│   ├── knowledge-modeling/              # 知识沉淀 Skill
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── notion-schema.md         # Notion 数据库结构与字段
│   │       ├── review-rules.md          # 艾宾浩斯卡片生成规则
│   │       └── unit-patterns.md         # 知识单元类型指南与反模式
│   ├── knowledge-review/                # 间隔复习 Skill
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── ebbinghaus-schema.md     # 艾宾浩斯三库 Schema
│   │       └── review-feedback.md       # 复习反馈策略
│   ├── grilling/                        # 想法压力测试（单问模式）
│   ├── grill-me/                        # 想法压力测试（快捷入口）
│   ├── batch-grill-me/                  # 想法压力测试（轮次批量模式）
│   ├── handoff/                         # 对话交接文档生成
│   ├── obsidian-vault/                  # Obsidian 笔记管理
│   ├── research/                        # 一手资料调研
│   ├── writing-fragments/               # 写作：探索阶段，挖掘原始片段
│   ├── writing-beats/                   # 写作：节奏构建，片段到节拍
│   └── writing-shape/                   # 写作：成型阶段，片段到文章
└── .claude/
    ├── settings.json                    # 项目级 Claude Code 配置
    ├── settings.local.json              # 本地 MCP 权限配置
    └── skills/                          # Claude Code Skill 镜像（软链 → .agents/skills/）
```

## 核心工作流

```
学习 / 阅读 / 思考
        │
        ▼
knowledge-modeling（沉淀）
        ├── 回读 Notion + 本地记录 → 去重/关联
        ├── 四问思考管线（Problem → Essence → Tradeoff → Transfer）
        ├── 写入 Notion Knowledge Units
        └── 生成艾宾浩斯卡片
        │
        ▼
knowledge-review（间隔复习，主动回忆）
```

## Skills

### knowledge-modeling

交互式认知压缩 Skill。接收输入后**先回读 Notion 已有知识**做去重/关联（避免重复建孤岛），再通过四问思考管线压缩，写入 Notion Knowledge Units 并生成艾宾浩斯卡片。

**触发方式：**
- "一起学习", "帮我学习", "学习一下"
- "整理这个知识", "帮我压缩", "压缩一下"
- "讨论一下 XXX", "研究一下 XXX"
- "看看这篇文章", "读一下这个"

**支持输入：** 文章、技术文档、代码、读书笔记、个人思考或调试过程。

**知识单元类型：** Raw → Insight → Model → Principle → Update → Reference，渐进式提炼。

### knowledge-review

间隔复习 Skill。基于艾宾浩斯卡片库进行主动回忆训练。

**触发方式：**
- "复习", "帮我复习", "开始复习"
- "今天该复习什么", "有什么要复习的"
- "检查记忆", "测验一下", "复习卡片"

**复习流程：** 逐题呈现 → 主动回忆 → 自评记忆质量（记住/模糊/忘了）→ 针对性反馈 → 会话总结。

### writing-fragments

写作**探索阶段** Skill。与用户深度访谈，挖掘原始写作片段——不急于结构化，只做拓宽可能性的工作。

**触发方式：** 显式调用 `/writing-fragments`，或 "帮我收集写作素材"、"头脑风暴一下这个话题"。

**产出：** 以 `---` 分隔的片段 Markdown 文件，作为后续 writing-beats 或 writing-shape 的原材料。

### writing-beats

写作**节奏构建** Skill。将原材料组装成一段节拍旅程（choose-your-own-adventure 风格），每个节拍落地一个概念后才能被后续节拍引用（grounding 机制）。

**触发方式：** 显式调用 `/writing-beats`，并传入原材料 Markdown 文件。

### writing-shape

写作**成型阶段** Skill。将原材料逐段塑造成完整文章。从 pile 中挖掘素材，逐段讨论格式选择（散文/列表/表格/引用），在对话中完成文章。

**触发方式：** 显式调用 `/writing-shape`，并传入原材料 Markdown 文件。

### 写作三阶段关系

```
writing-fragments          writing-beats / writing-shape
    （explore 探索）              （exploit 开采）
        │                              │
   挖掘原始片段                  从 pile 中组装文章
   不预设结构                    逐 beat / 逐段推进
```

`writing-beats` 和 `writing-shape` 都是 exploit 阶段 Skill，从已有原材料出发构建文章，区别在于：
- **beats** 更关注概念 grounding 依赖关系和节奏旅程
- **shape** 更关注段落间过渡、格式选择和论证线

### grilling

想法压力测试 Skill。对用户的计划、决定或想法进行无情的追问访谈，逐个击破决策树的每个分支，迫使用户在每一个节点上做出明确选择（附推荐答案）。

**三种模式：**

| 模式 | Skill | 触发方式 | 特点 |
|------|-------|---------|------|
| 单问模式 | `grilling` | "grill me", "拷问我", "压力测试" | 逐题追问，等待每问回答后再继续 |
| 快捷入口 | `grill-me` | `/grill-me` | 等同于 `/grilling` session |
| 批量模式 | `batch-grill-me` | "batch grill me" | 每轮同时抛出所有 frontier 问题（依赖已满足的） |

### handoff

对话交接 Skill。将当前对话压缩为交接文档，供新 Agent 接续工作。

**触发方式：** 显式调用 `/handoff`，可选传入 "下一次 session 会用来做什么" 作为参数。

**产出：** 保存到系统临时目录的交接文档，包含当前状态摘要和建议调用的 Skill。

### obsidian-vault

Obsidian 笔记管理 Skill。在 Obsidian Vault 中搜索、创建和组织笔记，支持 wikilinks 和索引笔记。

**触发方式：** "找一下 Obsidian 里的笔记", "创建新笔记", "整理索引"。

**Vault 位置：** `/home/unt/knowledge/`（按主题目录组织）

### research

一手资料调研 Skill。启动后台 Agent，基于官方文档、源码、规范等一手资料调研问题，产出带引用来源的 Markdown 报告。

**触发方式：** "调研一下 XXX", "帮我查一下 XXX 的官方文档", "研究一下这个 API"。

**特点：** 每个结论必须追溯到一手来源，不在当前对话中阻塞。平台/社交检索用个人 skill `agent-reach`；沉淀到 Notion 用 `knowledge-modeling`。

## Skill 路由（易混触发）

| 意图 | Skill |
|------|-------|
| 学习/压缩/写入 Notion | `knowledge-modeling` |
| 间隔复习 | `knowledge-review` |
| 一手文档/API 调研 → 仓库 Markdown | `research` |
| 全网/平台检索（小红书、推特、B站等） | `agent-reach`（个人 skill） |
| Obsidian 笔记 | `obsidian-vault` |
| 方案压力测试 | `grilling` / `batch-grill-me` |
| 写作 explore → exploit | `writing-fragments` → `writing-beats` 或 `writing-shape` |

## Notion 数据库

通过 `.mcp.json` 中配置的 Notion MCP Server 连接，`settings.local.json` 中声明了相应权限。

| 数据库 | 用途 |
|--------|------|
| **Knowledge Units** | 知识单元主库，**唯一真相源**。含 Type、Status、Domain、Problem、Essence、Tradeoff、Transfer 等字段 |
| **艾宾浩斯卡片库** | 间隔复习卡片库，与 Knowledge Units 通过 Relation 关联 |
| **艾宾浩斯复习记录** | 复习会话日志，记录每次复习结果 |

## DeepTutor 集成

根目录 `SKILL.md` 包含 DeepTutor CLI 的完整使用指南，涵盖聊天、知识库管理、Partner 管理、Skill Hub、Book、Memory、Session 等功能。`data/` 目录存放 DeepTutor 的运行时数据。

## 使用方式

在 Cursor 或 Claude Code 中打开此项目目录。自动触发类 Skill（如 knowledge-modeling / knowledge-review / grilling）可直接说触发短语；写作与 handoff 等带 `disable-model-invocation` 的 Skill 需显式调用（`/skill-name`）。

```bash
# 沉淀知识
帮我学习一下 Java 虚拟线程
讨论一下 volatile 关键字
帮我压缩这篇文章：https://example.com/article

# 间隔复习
帮我复习
今天该复习什么
测验一下 JVM 相关的知识

# 写作
/writing-fragments 我想写一篇关于 X 的文章
/writing-beats fragments.md
/writing-shape fragments.md -o article.md

# 想法压力测试
grill me on my architecture decision
batch grill me on the deployment plan

# 调研
调研一下 WebAssembly 组件模型的最新进展

# 交接
/handoff 继续实现用户认证模块
```

## Skill 触发速查

| 触发短语 | Skill |
|----------|-------|
| 一起学习 / 帮我学习 / 压缩一下 / 看看这篇文章 | knowledge-modeling |
| 复习 / 今天该复习什么 / 测验一下 | knowledge-review |
| grill me / 拷问我 / 压力测试 | grilling |
| batch grill me | batch-grill-me |
| /grill-me | grill-me |
| /handoff | handoff |
| 找 Obsidian 笔记 / 创建新笔记 | obsidian-vault |
| 调研一下 / 官方文档 | research |
| /writing-fragments | writing-fragments |
| /writing-beats | writing-beats |
| /writing-shape | writing-shape |
