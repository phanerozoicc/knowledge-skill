# Local Format Reference

Detailed spec for local Knowledge Unit files and the sync index. Consult this whenever the main SKILL.md is unclear about format.

## Local file format

Each Knowledge Unit becomes one Markdown file at `knowledge-unit/<Domain>/<Name>.md`.

### Full template

```markdown
---
notion_id: 1a919cbd-b19f-41f5-9886-fcfa61a8d0bb
notion_url: https://www.notion.so/1a919cbd-b19f-41f5-9886-fcfa61a8d0bb
last_edited_time: 2026-07-15T10:30:00.000Z
synced_at: 2026-07-31T08:00:00.000Z
type: Model
status: Active
domain: Java
source_url: https://example.com/the-article
memory: false
review_question: ""
review_answer: ""
---

## 1. 它解决了什么问题？
<content>

## 2. 它的核心矛盾是什么？
<content>

## 3. 它的本质模型是什么？
<content>

## 4. 它还能解释什么？
<content>

## 5. 认知变化
**以前我以为：** <content>
**现在我认为：** <content>

## 6. 最终压缩
> <one-sentence compression>

## Related
- [[Other Unit Name]]
```

### Frontmatter fields

Two groups: **sync metadata** (managed by notion-sync) and **Notion property mirrors** (round-tripped to/from Notion).

| Field | Group | YAML type | Maps to Notion | Notes |
|-------|-------|-----------|----------------|-------|
| `notion_id` | sync | string | page id | **Stable anchor.** Filled after first successful push; never changes on rename. Missing on freshly-written local-first drafts. |
| `notion_url` | sync | string | page url | Filled after first push. |
| `last_edited_time` | sync | string (ISO 8601) | Notion system field | Notion-side value, read via `notion-fetch`. Auto-updated on any Notion write — no skill maintains it. Basis for incremental pull. |
| `synced_at` | sync | string (ISO 8601) | — | Local time of last successful sync. Cross-machine drift is harmless; not used for incremental decisions. |
| `type` | property | string | `Type` (select) | `Raw` / `Insight` / `Model` / `Principle` / `Update` / `Reference` |
| `status` | property | string | `Status` (select) | `Inbox` / `Draft` / `Active` / `Stable` / `Archived` |
| `domain` | property | string | `Domain` (multi-select) | **Single value only** in YAML — Notion API accepts one string per write. Pick the most relevant tag. |
| `source_url` | property | string | `Source URL` (url) | Empty string if none. |
| `memory` | property | boolean | `Memory` (checkbox) | YAML `true`/`false`. Convert to `"__YES__"`/`"__NO__"` on Notion write. |
| `review_question` | property | string | `Review Question` (text) | Only meaningful when `memory: true`. Empty string otherwise. |
| `review_answer` | property | string | `Review Answer` (text) | Only meaningful when `memory: true`. Empty string otherwise. |

Text properties not always present (`Problem`, `Essence`, `Tradeoff`, `Transfer`, `Boundary`, `Evidence`, `Open Questions`, `Before`, `After`) live in the **body**, not frontmatter — they are the long-form thinking. The body's six sections already carry them. Only persist the short, structured ones above as frontmatter.

### Type → YAML conversion rules (push)

- `memory`: YAML `true` → Notion `"__YES__"`; YAML `false` → Notion `"__NO__"`. Never send booleans or `1/0`.
- `domain`: single string, e.g. `Java`. Never `"Java, JVM"`.
- `source_url`: place inside the `properties` object on the Notion page, not as a top-level page key.
- Relations (`Related Units`, `Backlinks`, `Review Cards`): JSON array `["url"]` for multi, JSON string `"url"` for single. Round-tripping relations is best-effort; the body's `## Related` wikilink list is the human-readable equivalent.

## File naming

- Path: `knowledge-unit/<Domain>/<Name>.md`. `<Domain>` is the single domain tag, title-cased (e.g. `Java`, `Distributed System`, `DDD`).
- `<Name>` is the compact claim (the Knowledge Unit `Name`), not a topic label. Keep it identical to the Notion `Name` property so the two are visually paired.
- Strip characters illegal in filenames: `/ \ : * ? " < > |`. Replace with spaces or omit.
- Example: Knowledge Unit "虚拟机栈深度为何有限" with `Domain = JVM` → `knowledge-unit/JVM/虚拟机栈深度为何有限.md`.

## Wikilinks

- Use Obsidian `[[wikilinks]]` for cross-unit links: `[[Other Unit Name]]` or `[[path/Other Unit Name]]`.
- Maintain a `## Related` section at the bottom listing related units as wikilinks.
- This is the human-readable mirror of Notion's `Related Units` / `Backlinks` relations.

## `.notion-sync-index.json` schema

Lives at the **repository root**. Committed to git.

```json
{
  "<data_source_id>": {
    "<notion_page_id>": {
      "filename": "knowledge-unit/<Domain>/<Name>.md",
      "last_edited_time": "2026-07-15T10:30:00.000Z",
      "synced_at": "2026-07-31T08:00:00.000Z"
    }
  }
}
```

- **Outer key** = Notion data source id (the database). Currently only Knowledge Units: `a0837cf8-c21b-4877-a713-63a8cb0d5dc5`.
- **Inner key** = Notion page id. This is the primary key — never the filename.
- `filename` is relative to the repo root. It is the *expected* location; if the file is missing there, that's the rename/delete signal.
- `last_edited_time` is the Notion-side value (objective across machines).
- `synced_at` is local sync time (may drift across machines; harmless).

### Concrete example

```json
{
  "a0837cf8-c21b-4877-a713-63a8cb0d5dc5": {
    "1a919cbd-b19f-41f5-9886-fcfa61a8d0bb": {
      "filename": "knowledge-unit/JVM/虚拟机栈深度为何有限.md",
      "last_edited_time": "2026-07-15T10:30:00.000Z",
      "synced_at": "2026-07-31T08:00:00.000Z"
    },
    "2b0a2dce-c320-4988-b8a6-0db8c6e4b9cc": {
      "filename": "knowledge-unit/DDD/聚合根边界由一致性范围决定.md",
      "last_edited_time": "2026-07-20T14:00:00.000Z",
      "synced_at": "2026-07-31T08:00:00.000Z"
    }
  }
}
```

### Recovery from inconsistency

The index and each file's frontmatter `notion_id` are redundant:

- **Index lost / corrupt**: rebuild by scanning `knowledge-unit/**/*.md`, reading each file's `notion_id` + `last_edited_time` frontmatter.
- **Frontmatter missing `notion_id`**: the file was written local-first but never pushed. Treat as a pending local-only file; on next push it gets an id written back.

## Rename / delete three-state decision (Pull)

During Step 1 (Pull), for each Notion page id, decide:

```
                    Notion page id in index?
                           /        \
                         yes         no
                         /             \
              index filename              new Notion page
              exists locally?             → create local file
                /        \
              yes         no
              /             \
         compare            ⚠️ SUSPECTED RENAME OR DELETE
         last_edited_time   → do NOT auto-process
         equal → skip         collect into report, ask user:
         newer → overwrite      "《<Name>》在本地找不到了，
                                 是被重命名了还是删除了？"
```

Reverse direction (local → Notion): for each local file with a frontmatter `notion_id` that is **absent** from this pull's Notion results → the Notion page was deleted. **Report it; do not auto-delete the local file.**

### Why id, not filename

If a file is renamed, filename-based tracking would see "old name gone + new name appeared" and could mis-treat it as a delete + a create — risking data loss or a duplicate. Keying on the Notion page id keeps the identity stable across renames:

- **Push side**: a renamed file is pushed via `notion-update-page` keyed on `notion_id`; the `Name` property and index `filename` are updated. Automatic and correct.
- **Pull side**: the only ambiguity is "Notion has it, local file gone" — which is genuinely ambiguous (rename vs delete) and is escalated to the user.

## Trash directory

When a pull overwrites an existing local file, the old version is backed up to `.notion-sync-trash/<filename>.<timestamp>.md` before overwriting, so no local edit is silently lost. This directory is not indexed and can be gitignored or committed at the user's discretion.

## Scripts: the `sync.js` contract

`sync.js` (in this skill folder) owns all local mutations. The agent feeds it data and consumes its output; the agent never hand-writes frontmatter or edits the index. Zero Node dependencies — run it with `node` directly or `./sync.js` (it is executable).

### `pull <pages.json> [--full]`

Input: a JSON array of page objects. Each object:

| key | required | notes |
|-----|----------|-------|
| `id` | yes | 32-hex Notion page id (or derived from `url`) |
| `url` | no | page url; used to derive `id` if `id` missing |
| `name` | yes | the `Name` property → becomes the filename + `Name` on push |
| `last_edited_time` | yes | the page's as-of timestamp from `notion-fetch`; basis for incremental skip |
| `type` / `status` / `domain` | no | Notion property mirrors; `domain` single tag (string or `["Tag"]`) |
| `source_url` | no | `Source URL` |
| `memory` | no | `"__YES__"` / `"__NO__"` (raw Notion checkbox value is fine) |
| `review_question` / `review_answer` | no | only meaningful when `memory` is yes |
| `content` | no | markdown body; `""` is valid (blank Notion page) |

`--full` enables the reverse scan (local `notion_id` not in this pull → suspected notion-side deletion). Pass it for a complete pull of the data source; omit it when pulling a subset, or every un-fetched page would false-alarm as deleted.

Output: a printed report (created / updated / skipped / suspected counts + details). Side effects: writes/overwrites local files under `knowledge-unit/`, backs up overwritten files to `.notion-sync-trash/`, and rewrites `.notion-sync-index.json`.

### `push <file.md>`

Input: a path to a local Knowledge Unit file (absolute, or relative to the repo root, or relative to cwd).

Output: a JSON object the agent consumes to call Notion:

```json
{
  "action": "update | create",
  "notion_id": "<id or null>",
  "notion_url": "<url or null>",
  "properties": { "Name": "...", "Type": "...", "Status": "...", "Domain": "...",
                  "Source URL": "...", "Memory": "__YES__|__NO__",
                  "Review Question": "...", "Review Answer": "..." },
  "content": "<markdown body>",
  "notes": ["Domain: pass single string value to Notion (multi-select quirk).",
            "After notion-update-page succeeds, update frontmatter synced_at + index ..."]
}
```

- `action = update` when frontmatter has `notion_id` → agent calls `notion-update-page`.
- `action = create` when no `notion_id` → agent calls `notion-create-pages`, then writes `notion_id`/`notion_url` back into the file.
- `Memory` is emitted as `__YES__`/`__NO__` (the form Notion expects), converted from the boolean frontmatter.
- The script does **not** call Notion and does **not** rewrite the file after a push — the agent must update `synced_at`/`notion_id`/index once the MCP call succeeds (easiest: re-run `pull` on that one page).

### `status`

No input. Output: a report of index entries, local file count, by-domain breakdown, and inconsistencies (files missing locally / files missing from index).

### Three-state → script mapping

| Three-state case | Script (`pull`) behavior |
|------------------|--------------------------|
| id in index + file present + same `last_edited_time` | `skipped` |
| id in index + file present + newer time | `updated` (backs up old first) |
| id in index + file **missing** | `suspected` (rename or delete) — no change |
| id not in index | `created` |
| local `notion_id` not in a `--full` pull | `suspected` (notion-side deleted) — local kept |

