---
name: knowledge-modeling
description: Interactive learning companion and knowledge capture skill. Use when the user wants to learn, study together, discuss a topic, capture knowledge from articles or code, or do cognitive compression. Covers phrases like "一起学习", "帮我学习", "学习一下", "研究一下", "整理知识", "讨论一下", "压缩一下", "看看这篇文章", and any shared learning material. Walks through the four-question thinking pipeline (Problem, Essence, Tradeoff, Transfer), supports both direct compression and discussion modes, and writes finalized knowledge to Notion Knowledge Units.
---

# Knowledge Modeling

## Purpose

This skill is an interactive learning companion. It helps the user capture, compress, and store knowledge into their Notion Knowledge Units system.

The user will provide learning material (articles, links, code, screenshots, thoughts). Your job is to guide them through cognitive compression, then write the results to Notion.

## Trigger

Use this skill when:
- User pastes an article, URL, file link, or code snippet
- User says any of the following (or variations):
  - "一起学习", "帮我学习", "学习一下", "我来学"
  - "整理这个知识", "帮我压缩", "压缩一下"
  - "讨论一下 XXX", "聊聊 XXX", "研究一下 XXX"
  - "看看这篇文章", "读一下这个"
  - "和我一起看", "一起研究"
- User asks about a technical concept and wants to preserve the understanding
- User shares a learning goal or wants to study a topic together

## Workflow

### Step 1: Receive Input

Identify the source type:
- Article / blog post
- Technical documentation
- Code or source file
- Book chapter / notes
- User's own thought or question
- Debugging / problem-solving session

Preserve only enough metadata for traceability: title, URL, author, date.

### Step 2: Ask Mode

Ask the user which mode they prefer:

> "直接压缩还是先讨论？"

- **压缩模式**: Skip to Step 3a. Fast, produces draft Knowledge Units for review.
- **讨论模式**: Go to Step 3b. Slower, but explores connections, challenges assumptions, and surfaces insights together.

If the user has already specified the mode, proceed directly.

### Step 3a: Compression Mode

Run the four-question pipeline on each candidate unit:

1. **Problem** — What problem does this solve?
2. **Essence** — What is it in one sentence?
3. **Tradeoff** — What does it sacrifice, and what does it gain?
4. **Transfer** — Where else does this pattern appear?

Additionally, for each unit:
- **Boundary** — When is this wrong or insufficient? (optional but valuable)
- **Before / After** — Has this changed the user's understanding? If yes, record both.

Produce 1-5 candidate Knowledge Units. Present them as a draft for the user to review.

### Step 3b: Discussion Mode

Engage the user before compressing:

1. **Diverge**: What does this make the user think of? Surface nearby concepts, prerequisites, contradictions, analogies.
2. **Challenge**: Ask "why?" and "what if not?" Push past surface understanding.
3. **Connect**: Look for shared models across domains. "Have we seen this pattern before?"
4. **Compress**: Only after discussion, run the four-question pipeline.

Key principles for discussion:
- User's own associations are first-class signals, even if not in the source material.
- Record the user's understanding in their own words, not a paraphrase of the source.
- Preserve ambiguity when understanding is incomplete — mark as `Raw` or `Draft`.
- Do not force every idea into a model. Models emerge from multiple shared insights.

### Step 4: Review and Confirm

Present the final Knowledge Units to the user in this format:

```text
Unit N: [Name]
  Type: [Raw | Insight | Model | Principle | Update | Reference]
  Status: [Inbox | Draft | Active | Stable]
  Domain: [tags]
  Problem: ...
  Essence: ...
  Tradeoff: ...
  Transfer: ...
  Memory: [yes/no]
  Review Question: ... (if Memory = yes)
  Review Answer: ... (if Memory = yes)
```

Ask: "确认写入 Notion？需要调整吗？"

### Step 5: Write to Notion

After user confirmation, create pages in Knowledge Units database.

**Notion target:**
- Database: `Knowledge Units`
- Data source ID: `a0837cf8-c21b-4877-a713-63a8cb0d5dc5`
- Use `notion-create-pages` with parent type `data_source_id`

**Page content** should follow the Thinking Pipeline structure:

```text
## 1. 它解决了什么问题？
[user's answer]

## 2. 它的核心矛盾是什么？
[user's answer]

## 3. 它的本质模型是什么？
[user's answer]

## 4. 它还能解释什么？
[user's answer]

## 5. 认知变化
**以前我以为：** [if applicable]
**现在我认为：** [if applicable]

## 6. 最终压缩
> [one-sentence compression]
```

**Property mapping:**
- `Name` ← unit name (compact claim, not topic label)
- `Type` ← Raw / Insight / Model / Principle / Update / Reference
- `Status` ← Inbox / Draft / Active / Stable
- `Domain` ← single tag only (see Notion API quirks below), pick the most relevant one from: Java, JVM, TCP, DDD, Distributed System, Backend, Learning
- `Problem` ← what problem it solves
- `Essence` ← one-sentence compression
- `Tradeoff` ← what it sacrifices
- `Transfer` ← where else this applies
- `Before` / `After` ← only for Type=Update
- `Boundary` ← when it stops applying (if known)
- `Source URL` ← original source link (must go in `properties`, NOT as a top-level page field)
- `Memory` ← checkbox: use `__YES__` / `__NO__` (not boolean, not 1/0)
- `Review Question` / `Review Answer` ← only if Memory = `__YES__`

**Notion API quirks:**
- **Checkbox fields**: Must use `__YES__` or `__NO__` as string values, not booleans or numbers.
- **Multi-select fields**: The `notion-create-pages` tool only accepts a single string value per property. For `Domain`, pick the single most relevant tag. Additional tags can be added manually in Notion afterwards.
- **Source URL**: Must be placed inside the `properties` object, not as a top-level key in the page object.

### Step 6: Ebbinghaus Review Cards

**Before marking Memory = true, check (from references/review-rules.md):**
- Will forgetting this block future understanding?
- Will the user need this in interviews, debugging, design, or code review?
- Can this be recalled as a crisp answer?

If fewer than two are yes → keep Memory = false.

**After writing Knowledge Units to Notion, automatically create Ebbinghaus review cards for all Memory = true units.**

**Card target:**
- Data source ID: `29ea2efb-b18d-8104-806b-000b8f294206`
- Use `notion-create-pages` with parent type `data_source_id`

**Card property mapping:**
- `名称` ← `Review Question` from the Knowledge Unit
- `备注` ← `Review Answer` from the Knowledge Unit
- `Knowledge Units` ← relation back to the source unit page URL (must be JSON array format: `["https://www.notion.so/<page-id>"]`)
- `文件链接` ← source Knowledge Unit page URL (plain string)
- `创建日期` ← today's date (use expanded format: `date:创建日期:start` = `"YYYY-MM-DD"`, `date:创建日期:is_datetime` = `0`)
- `批量复习` ← `"__YES__"` (enables the review system to pick up the card)

**Timing:** Create cards immediately after Step 5 (Write to Notion) completes successfully. This is a mandatory step, not optional — every Memory = true unit must get a card.

## Operating Rules

- Prefer fewer, sharper units over complete coverage.
- Do not summarize whole articles. Extract only what changes understanding.
- Let a unit evolve by changing Type and Status; do not create separate databases.
- Do not create a unit named only after a broad topic (e.g., "Java Memory Model").
- Do not promote to Model unless multiple concrete cases share the pattern.
- Use Notion only as persistence after thinking is coherent.
- When unsure about the schema, consult `references/notion-schema.md`.
- When unsure about review card decisions, consult `references/review-rules.md`.
- When unsure about field format or anti-patterns, consult `references/unit-patterns.md`.

## References

- `references/notion-schema.md`: Notion database fields, views, and implementation rules.
- `references/review-rules.md`: How to decide whether a unit should become an Ebbinghaus review card.
- `references/unit-patterns.md`: Field definitions, examples by type, and anti-patterns.
