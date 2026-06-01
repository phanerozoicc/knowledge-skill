# Notion Schema

This reference documents the current target Notion structure for the user's knowledge system.

## Architecture

Three layers, one primary database:

```
knowledge (page) — hub
├── Knowledge Units — single source of truth for learned knowledge
├── 艾宾浩斯记忆 — spaced-repetition engine for selected recall items
└── Migration Queue — archived legacy databases
```

Do not create new Notion databases during normal learning capture. Add fields or views only when repeated usage proves they are necessary.

## Knowledge Units

**Data source ID:** `a0837cf8-c21b-4877-a713-63a8cb0d5dc5`
**Database URL:** `https://www.notion.so/1a919cbdb19f41f59886fcfa61a8d0bb`
**Location:** Under `knowledge-codex` page, linked into `knowledge` page as inline view.

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `Name` | title | Compact claim, not topic label |
| `Type` | select | `Raw`, `Insight`, `Model`, `Principle`, `Update`, `Reference` |
| `Status` | select | `Inbox`, `Draft`, `Active`, `Stable`, `Archived` |
| `Domain` | multi-select | Tags: `Java`, `JVM`, `TCP`, `DDD`, `Distributed System`, `Backend`, `Learning` |
| `Problem` | text | What problem this unit addresses |
| `Essence` | text | Compressed understanding, one sentence |
| `Tradeoff` | text | Cost, limitation, or sacrifice |
| `Transfer` | text | Other situations explained by the same idea |
| `Boundary` | text | When the idea is wrong or insufficient |
| `Evidence` | text | Source facts, examples, or observations |
| `Open Questions` | text | Unresolved questions |
| `Before` | text | Prior understanding (for Type=Update) |
| `After` | text | New understanding (for Type=Update) |
| `Memory` | checkbox | Whether to create review material |
| `Review Question` | text | Flashcard question if Memory=true |
| `Review Answer` | text | Flashcard answer if Memory=true |
| `Review Cards` | relation | Linked Ebbinghaus cards |
| `Related Units` | relation | Self-relation for connected units |
| `Backlinks` | relation | Auto-reciprocal links |
| `Source URL` | url | Source link |
| `Created` | date | Capture date |

### Views

| View | Type | Configuration |
|------|------|---------------|
| Default | Table | Name, Type, Status, Domain, Essence, Created. Sort by Created DESC |
| 01 Inbox | Table | Filter: Status = Inbox. Shows core fields |
| 02 Active Knowledge | Table | Filter: Status = Active. Shows thinking fields |
| Thinking Pipeline | Table | Filter: Status ≠ Archived. Shows Problem, Essence, Tradeoff, Transfer, Before, After |
| By Domain | Board | Grouped by Domain. Shows Name, Type, Status, Essence, Transfer |
| 03 Memory Queue | Table | Filter: Memory = true. Shows Review Question, Review Answer |
| 04 Models & Principles | Board | Filter: Status ≠ Archived. Grouped by Type |
| Timeline | Timeline | By Created date |

### Page Template

New Knowledge Units should use the "Thinking Pipeline" template, which includes:

1. 它解决了什么问题？
2. 它的核心矛盾是什么？
3. 它的本质模型是什么？
4. 它还能解释什么？
5. 认知变化 (Before → After)
6. 最终压缩（一句话）

Each section includes expandable example blocks for guidance.

## Ebbinghaus Card Mapping

**Card database data source:** `collection://29ea2efb-b18d-8104-806b-000b8f294206`
**Location:** Under `knowledge-codex` → `艾宾浩斯记忆` page

When `Memory = true` on a Knowledge Unit, create one card:

- `名称`: Use `Review Question`
- `备注`: Use `Review Answer`
- `Knowledge Units`: Relation back to the source unit

Only create cards for concepts that need active recall. See `references/review-rules.md`.

## Notion API Quirks

When using `notion-create-pages` to write Knowledge Units, be aware of these API constraints:

- **Checkbox fields** (e.g., `Memory`): Use `"__YES__"` or `"__NO__"` as string values. Booleans (`true`/`false`) and numbers (`1`/`0`) will cause validation errors.
- **Multi-select fields** (e.g., `Domain`): The tool only accepts a single string value per property. Cannot pass comma-separated values like `"Java, JVM"`. Pick the single most relevant tag; add others manually in Notion if needed.
- **Source URL**: Must be placed inside the `properties` object, not as a top-level key in the page object. Top-level keys are `properties` and `content` only.

## Implementation Rules

- Add source records as `Reference`, not long summaries.
- Promote from `Raw` to `Insight` only after compression.
- Promote to `Model` only after multiple units share the same structure.
- Use `Update` only when there is a real before/after change in understanding.
- Keep old category databases in `Migration Queue`; do not maintain them as primary.
- For `Domain`, pick the single most relevant tag. Do not attempt comma-separated multi-select values.
