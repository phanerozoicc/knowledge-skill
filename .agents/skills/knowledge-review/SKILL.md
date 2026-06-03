---
name: knowledge-review
description: Spaced repetition review skill based on the user's Ebbinghaus card system. Use when the user wants to review knowledge, do a review session, check memory, quiz themselves, or practice recall. Covers phrases like "复习", "帮我复习", "开始复习", "复习一下", "今天该复习什么", "检查记忆", "测验一下". Pulls due cards from the Ebbinghaus card database, runs an interactive Q&A session, and provides feedback.
---

# Knowledge Review

## Purpose

This skill runs interactive spaced-repetition review sessions based on the user's Ebbinghaus card system in Notion. It pulls cards that are due for review, presents them as questions, evaluates the user's recall, and provides feedback.

## Trigger

Use this skill when:
- User says any of the following (or variations):
  - "复习", "帮我复习", "开始复习", "复习一下"
  - "今天该复习什么", "有什么要复习的"
  - "检查记忆", "测验一下", "测试一下"
  - "一起复习", "复习卡片"
- User asks what's due for review today
- User wants to practice active recall of previously learned knowledge

## Workflow

### Step 1: Determine Review Scope

Ask the user how they want to review (if not already specified):

> "怎么复习？"
> 1. **按到期时间** -- 复习今天到期的卡片（默认）
> 2. **按主题/Domain** -- 复习某个领域（如 Java、JVM、DDD）
> 3. **随机抽测** -- 从所有卡片中随机抽取
> 4. **重点复习** -- 只复习复习次数较少或最近没复习过的卡片

If the user doesn't specify, default to **按到期时间**.

### Step 2: Fetch Cards from Notion

Search the Ebbinghaus card database for cards matching the chosen scope.

**Card database:**
- Data source ID: `29ea2efb-b18d-8104-806b-000b8f294206`
- Use `notion-search` with `data_source_url` = `collection://29ea2efb-b18d-8104-806b-000b8f294206`

**For due cards:** Search for cards where `下次复习时间` (formula field) indicates today or earlier. Since formula fields cannot be filtered via search, fetch recent cards and check their review status in the output.

**Card fields used during review:**
- `名称` (title) -- the review question
- `备注` -- the review answer / reference answer
- `Knowledge Units` -- relation back to source knowledge unit
- `文件链接` -- link to source knowledge unit
- `复习次数` (formula) -- how many times reviewed
- `下次复习时间` (formula) -- next review due date
- `归档` -- whether card is archived (skip archived cards)
- `批量复习` -- whether card is active in review system

### Step 3: Run Review Session

Present cards one at a time in an interactive Q&A format:

**For each card:**

1. **Show the question** (from `名称`)
2. **Wait for the user to answer** -- let them think and respond in their own words
3. **Reveal the reference answer** (from `备注`)
4. **Ask the user to self-assess:**

> "回忆得怎么样？
> - **记住了** -- 回忆清晰完整
> - **模糊** -- 有印象但不完整
> - **忘了** -- 完全想不起来"

5. **Provide targeted feedback:**
   - If **记住了**: Briefly acknowledge, optionally add a deeper connection or follow-up insight
   - If **模糊**: Explain the concept again, highlight the key distinction the user missed, connect it to related knowledge
   - If **忘了**: Walk through the concept from scratch, use the Thinking Pipeline approach (Problem -> Essence -> Tradeoff -> Transfer), offer to open the linked Knowledge Unit for full context

**Session principles:**
- Do NOT show all questions at once. Present one card at a time.
- When the user struggles, teach actively -- don't just show the answer and move on.
- Connect the current card to previously reviewed cards when patterns emerge.
- If the user asks to dig deeper into a card's source material, fetch the linked Knowledge Unit and discuss it.
- Keep the tone encouraging but honest about gaps.

### Step 4: Session Summary

After all cards are reviewed (or the user ends the session early), provide a summary:

```text
复习总结：
- 总卡片数: N
- 记住了: X
- 模糊: Y  
- 忘了: Z
- 跳过: W

薄弱点: [list topics where the user struggled]
建议: [specific follow-up actions]
```

**Follow-up suggestions might include:**
- "XXX 这个知识点建议回看 Knowledge Unit，理解不够深"
- "YYY 和 ZZZ 是相关概念，可以对比复习"
- "今天模糊的卡片建议明天再来一轮"

### Step 5: Update Review Status (Optional)

If the user wants to record the review session, create entries in the review record database:

**Review record database:**
- Data source ID: `29ea2efb-b18d-8165-a3e7-000b09e45612`
- Use `notion-create-pages` with parent type `data_source_id`

**Record property mapping:**
- `备注` ← brief note about the review outcome (e.g., "记住了" / "模糊，需加强" / "忘了，已重新讲解")
- `文件链接` ← card page URL
- `状态` ← "完成"
- `艾宾浩斯` ← relation to the card (JSON string of single page URL)
- `date:日期:start` ← today's date (ISO 8601)
- `date:日期:is_datetime` ← 0

Ask the user: "要记录这次复习结果到 Notion 吗？"

## Notion API Notes

- **Checkbox fields**: Use `"__YES__"` or `"__NO__"` as string values.
- **Formula fields** (`复习次数`, `下次复习时间`, `复习状态`, `默认复习间隔`, `复习提醒`): These are read-only. Do NOT try to write to them.
- **Relation fields**: Must be JSON array format `["https://www.notion.so/<page-id>"]` for multi-relation, or JSON string `"https://www.notion.so/<page-id>"` for single-relation.
- **Button field** (`复习`): Cannot be triggered via API. Ignore it.
- The Ebbinghaus system uses Notion formulas to calculate review intervals and next review dates. The review skill only needs to READ these values, not compute them.

## Operating Rules

- Always skip cards where `归档 = __YES__` (archived).
- Prefer cards that are due today or overdue. If no cards are due, offer to review recent or random cards instead.
- Do not show the answer before the user has attempted to recall.
- When the user's answer is partially correct, acknowledge what they got right before explaining what was missed.
- Limit each session to a reasonable number of cards (default 10). Offer to continue if there are more.
- If the user wants to review a specific Domain, search the Knowledge Units database first to find relevant cards.
- Do not create new Knowledge Units or cards during a review session. Review is for recalling, not capturing.
- When the user asks to understand a concept more deeply during review, switch to teaching mode -- explain using the four-question pipeline, but do not trigger the knowledge-modeling skill's write workflow.

## References

- `references/ebbinghaus-schema.md`: Detailed schema for all three Ebbinghaus databases and field definitions.
- `references/review-feedback.md`: Feedback strategies for different recall quality levels.
