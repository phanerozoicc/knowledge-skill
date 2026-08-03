---
name: knowledge-modeling
description: Interactive learning and knowledge capture skill. Use when the user wants to understand, discuss, compress, or preserve knowledge from articles, code, documentation, or their own thinking. Supports a lightweight learn mode with diagnostic questions and retrieval practice, a discussion mode, and a direct compression mode. Writes finalized knowledge to Notion Knowledge Units.
---

# Knowledge Modeling

## Purpose

This skill helps the user understand, compress, and store knowledge in their Notion Knowledge Units system.

The user may provide learning material (articles, links, code, screenshots, thoughts) or a topic. Help them reach demonstrable understanding when needed, then guide cognitive compression and write the result to Notion.

## Trigger

Use this skill when:
- User pastes an article, URL, file link, or code snippet
- User says any of the following (or variations):
  - "一起学习", "帮我学习", "学习一下", "我来学"
  - "整理这个知识", "帮我压缩", "压缩一下"
  - "讨论一下 XXX", "聊聊 XXX"
  - "看看这篇文章", "读一下这个"
  - "和我一起看", "一起研究"
  - "教我 XXX", "我想学 XXX", "带我学 XXX", "给我讲讲 XXX"
- User asks about a technical concept and wants to preserve the understanding
- User shares a learning goal or wants to study a topic together

## Workflow

### Step 0: Recall & Relate

Before capturing anything, recall what the user already has. The source of truth is Notion — global "what do I already know" questions are answered by searching Notion, never by reading local copies. This step is what keeps沉淀 from becoming write-only: existing units are read back before new ones are written.

1. **Recall from Notion.** Search the Knowledge Units database for anything related to this topic:

   - Use `notion-search` with `data_source_url` = `collection://a0837cf8-c21b-4877-a713-63a8cb0d5dc5` (the Knowledge Units database). Search by the topic name, key terms from the input, and likely synonyms.
   - Look for same-name units, same-domain units covering overlapping ground, and concepts that would be superseded or refined by the new learning.

2. **Recall from a local learning hand-off (if present).** If the current directory (or a topic subfolder) contains `MISSION.md` and/or `learning-records/`, read them — they hold compressed conclusions from a prior learning stage and should be treated as first-class input, not re-derived.

3. **Decide how the new unit relates to existing knowledge.** Based on what was recalled, present the user with the relevant existing units and choose one of:

   - **Update an existing unit** — the new learning corrects or deepens an old one. Use `Type = Update`, fill `Before` / `After`, and relate it to the old unit via `Related Units`. This is the supersession path: the old unit stays, the understanding evolves on record.
   - **New unit, related** — the new unit is distinct but connected. Create it and link via `Related Units` (or `Backlinks`).
   - **New unit, standalone** — no meaningful relation found.

   Default toward Update or relate when any overlap exists. Suppress the urge to create a new island.

Only after Step 0 is complete does the unit enter the normal capture flow below.

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

> "这份材料你想怎么处理——先读懂、一起讨论，还是直接压缩？"

- **压缩模式**: Skip to Step 3a. Fast, produces draft Knowledge Units for review. Best when the user already understands the material and just wants to settle it.
- **讨论模式**: Go to Step 3b. Slower, but explores connections, challenges assumptions, and surfaces insights together.
- **读懂模式**: Go to Step 3c. Use a short diagnostic, minimal explanation, closed-book retrieval, and a transfer question before compression. Best for unfamiliar material.

If the user has already specified the mode, proceed directly.

Infer the mode when intent is clear instead of asking unnecessarily:
- "压缩/整理/沉淀" → compression mode
- "讨论/聊聊" → discussion mode
- "教我/我想学/带我读懂" → learn mode

Recommend learn mode when the material relies on unfamiliar prerequisites, the closest existing units are only `Draft`, or the user cannot explain the core idea in their own words.

### Routing (avoid skill collisions)

| User intent | Use |
|-------------|-----|
| Capture / compress / study together / settle understanding into Notion | **this skill** |
| Spaced-repetition quiz on existing cards | `knowledge-review` |
| Internet / platform lookup (小红书、推特、B站、网页等) | `agent-reach` (personal skill), then optionally return here to compress |
| Primary-source docs/API investigation → Markdown report in repo | `research` |

"研究一下" alone is ambiguous: prefer this skill when the goal is *learning + Notion capture*; prefer `research` / `agent-reach` when the goal is *fetch facts first*.
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

0. **Ground the material first.** Before asking anything, lay out the source material clearly and completely enough that the user can reason about it from your output alone. Discussion is a shared activity — it fails the moment the user is being quizzed on material they have not been shown. Specifically:
   - Do **not** assume the user has read the source. The source may have been fetched by the agent (e.g. via a web reader); the user has not seen it.
   - Do **not** summarize so thinly that the discussion question references entities/examples the user has never been introduced to (e.g. "why does V2 fix V1's bug?" before explaining what V1 and V2 are).
   - Explain the core mechanism, the key examples, and any structure the upcoming questions will lean on, in the user's own language (Chinese if the user is writing in Chinese).
   - Only after the material is on the table may you move to the steps below. If you catch yourself about to ask "why does X happen?" — first make sure X has been described.
1. **Diverge**: What does this make the user think of? Surface nearby concepts, prerequisites, contradictions, analogies.
2. **Challenge**: Ask "why?" and "what if not?" Push past surface understanding.
3. **Connect**: Look for shared models across domains. "Have we seen this pattern before?"
4. **Compress**: Only after discussion, run the four-question pipeline.

Key principles for discussion:
- **Grounding first, questioning second.** Never put a "why / what if" question to the user before the relevant facts and mechanism are in front of them. A challenge question built on unexplained material is not discussion — it is a pop quiz, and it erodes trust.
- User's own associations are first-class signals, even if not in the source material.
- Record the user's understanding in their own words, not a paraphrase of the source.
- Preserve ambiguity when understanding is incomplete — mark as `Raw` or `Draft`.
- Do not force every idea into a model. Models emerge from multiple shared insights.

### Step 3c: Learn Mode

Keep this mode lightweight. Do not create a separate course workspace or long lesson artifact.

1. **Set the target.** Ask what the user needs to be able to explain, decide, debug, or build. If the goal is already clear, do not ask again.
2. **Run one diagnostic.** Ask a single question that exposes the user's current model or prerequisite gap. Wait for the answer.
3. **Teach the smallest missing piece.** Explain only what closes the observed gap. Ground factual claims in the provided source or a high-trust primary source.
4. **Retrieve closed-book.** Ask the user to restate the idea, key distinction, or mechanism without looking at the explanation. Wait for the answer before giving feedback.
5. **Test transfer.** Give one new scenario, counterexample, or boundary case and ask the user to apply the idea.
6. **Compress only after evidence.** If retrieval and transfer are adequate, continue to the four-question pipeline. Otherwise, correct the specific gap and retry once. Keep unresolved understanding as `Raw` / `Draft` with `Open Questions`; do not present fluency as mastery.

Do not generate both the user's retrieval answer and its evaluation in the same turn.

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
  Boundary: ...
  Evidence: ...
  Open Questions: ... (if unresolved)
  Memory: [yes/no]
  Review Question: ... (if Memory = yes)
  Review Answer: ... (if Memory = yes)
```

Ask: "确认写入 Notion？需要调整吗？"

### Step 4.5: Compression Quality Bar

Before showing a unit to the user, verify it passes three quality gates. A unit that fails these is not a Knowledge Unit — it is a tutorial, a paraphrase, or a set of lecture notes, and should be rewritten.

1. **Compress, don't retell.** A Knowledge Unit is a cognitive compression — one insight that reframes understanding, supported by minimal scaffolding. It is not a walkthrough of the source. Symptoms of failure: enumerating "V1 / V2 / V3", listing every variant or fix the source tried, walking the reader through a three-act history. Ask: could a reader who already half-understands the topic extract the *one reframe* in under ten seconds? If the punchline is buried under narration, rewrite. The fix is almost always: move the core claim to the top, cut the narrative, keep only the evidence that proves the claim.

2. **Self-contained.** A reader must understand the unit from its own text alone, without having read the source, without having read sibling units, without recognizing any local jargon. No "as we saw in V2", no "the FairLock three-step evolution", no references that assume Jenkov's or any other author's narrative. If a phrase only makes sense to someone who has read the original, either expand it inline or cut it. Cross-references to other units are for *relations*, not for *comprehension*.

3. **Code is evidence, not the subject.** Code snippets are welcome and often necessary — a concurrency unit without code is "文字太贫瘠". But code serves the insight; it is not the body. Keep the smallest snippet that proves the point (often 2–5 lines), annotate the load-bearing line with a comment, and let the surrounding prose point at it. Do not reproduce a full class, do not show "fix version 1 then fix version 2 then final version" — that is teaching, not compressing. If the snippet is longer than the prose around it, the unit has flipped from insight-first into tutorial.

A concrete self-check: hold the candidate next to an existing high-quality unit in the vault (e.g. `非阻塞算法的核心是「不阻塞，只尝试」`). The new unit should read the same way — a one-line essence up front, the model unpacked in a few sentences, evidence in service of the claim, tradeoff and transfer crisp. If it reads heavier, drier, or more like documentation, it has failed the bar; rewrite before showing the user.

### Step 5: Write Local-first, then Push to Notion

After user confirmation, write **local first**, let the user review the file in Obsidian, then **push to Notion**. The local file is the review surface; Notion remains the final source of truth. Format details and the full field mapping live in the `notion-sync` skill's [references/local-format.md](../notion-sync/references/local-format.md).

**Step 5a — Write the local file.** Create `knowledge-unit/<Domain>/<Name>.md` with:

- Frontmatter carrying the Notion properties (`type`, `status`, `domain`, `source_url`, `memory`, `review_question`, `review_answer`) plus sync metadata slots. At this point `notion_id` / `notion_url` / `last_edited_time` / `synced_at` are **empty** — they are filled back after the push in 5b.
- Body following the Thinking Pipeline structure (below).

**Step 5b — Push to Notion (after the user reviews and confirms).** Follow the `notion-sync` skill's Step 2 (Push): `notion-search` to deduplicate first, then `notion-create-pages` (parent type `data_source_id`) for a new unit or `notion-update-page` for an existing one. After a successful push, write `notion_id` / `notion_url` / `last_edited_time` / `synced_at` back into the local file's frontmatter and update `.notion-sync-index.json`.

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
- `Evidence` ← source facts, examples, or observations supporting the unit
- `Open Questions` ← unresolved gaps, especially from learn mode
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

### Step 7: Archive Local Learning Records

If this capture consumed a local hand-off (`MISSION.md` / `learning-records/*.md`), those files now have a live Notion Knowledge Unit as their source of truth. Mark them archived rather than deleting.

For each `learning-records/*.md` file consumed:

- Add (or replace) the status line:
  ```
  Status: archived → https://www.notion.so/<new-or-updated-unit-page-id>
  ```
- Do **not** delete the file.

If there is no such hand-off, skip this step.

## Operating Rules

- Always run Step 0 (Recall & Relate) before capturing. Notion is the source of truth for "what do I already know"; search it, never read local copies for that question.
- When recall finds overlap, default to Update or relate — do not create a new island.
- Prefer fewer, sharper units over complete coverage.
- Do not summarize whole articles. Extract only what changes understanding.
- Let a unit evolve by changing Type and Status; do not create separate databases.
- Do not create a unit named only after a broad topic (e.g., "Java Memory Model").
- Do not promote to Model unless multiple concrete cases share the pattern.
- Use Notion only as persistence after thinking is coherent.
- **Write local-first (Step 5a → 5b)**: produce a local Markdown file under `knowledge-unit/` for the user to review before pushing to Notion. The local file is the review surface; Notion is the final source of truth. See the `notion-sync` skill for the local format and push workflow.
- On a local hand-off, treat `learning-records/` and `MISSION.md` as first-class input, and archive the records after writing (Step 7).
- Prefer Notion MCP tools already configured in this project (`notion-search`, `notion-fetch`, `notion-create-pages`, `notion-query-data-sources`). Discover schemas with `GetMcpTools` before calling unfamiliar tools.
- In learn mode, require the user to retrieve and apply the idea before treating it as understood.
- Prefer the smallest useful teaching loop; do not create course artifacts unless explicitly requested.
- When unsure about the schema, consult [references/notion-schema.md](references/notion-schema.md).
- When unsure about review card decisions, consult [references/review-rules.md](references/review-rules.md).
- When unsure about field format or anti-patterns, consult [references/unit-patterns.md](references/unit-patterns.md).

## References

- [../notion-sync/references/local-format.md](../notion-sync/references/local-format.md): Local Markdown file format, frontmatter field mapping, and the `.notion-sync-index.json` schema used by Step 5a (write local) and 5b (push to Notion).
- [references/notion-schema.md](references/notion-schema.md): Notion database fields, views, and implementation rules.
- [references/review-rules.md](references/review-rules.md): How to decide whether a unit should become an Ebbinghaus review card.
- [references/unit-patterns.md](references/unit-patterns.md): Field definitions, examples by type, and anti-patterns.
