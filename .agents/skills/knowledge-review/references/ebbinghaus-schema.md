# Ebbinghaus Database Schema

Reference for the three Notion databases that power the Ebbinghaus review system.

## Architecture

```
knowledge (page)
└── 艾宾浩斯记忆 (page)
    ├── 艾宾浩斯卡片库 (database) -- review cards
    └── 艾宾浩斯复习记录 (database) -- review session logs
```

## Database 1: 艾宾浩斯卡片库

**Data source ID:** `29ea2efb-b18d-8104-806b-000b8f294206`
**Location:** Under knowledge -> 艾宾浩斯记忆

### Fields

| Field | Type | Read/Write | Description |
|-------|------|------------|-------------|
| `名称` | title | RW | Review question (card front) |
| `备注` | text | RW | Reference answer (card back) |
| `Knowledge Units` | relation | RW | Link back to source Knowledge Unit (multi-relation) |
| `文件链接` | text | RW | URL to source Knowledge Unit page |
| `创建日期` | date | RW | Card creation date |
| `批量复习` | checkbox | RW | Whether card is active in review system |
| `归档` | checkbox | RW | Whether card is archived (skip if true) |
| `自定义复习间隔` | text | RW | Custom interval override, comma-separated days |
| `下次复习时间` | formula | RO | Calculated next review date (**not in SQL**) |
| `复习次数` | formula | RO | Count of completed reviews (**not in SQL**) |
| `复习状态` | formula | RO | Status label for grouping (**not in SQL**) |
| `复习提醒` | formula | RO | Reminder text (**not in SQL**) |
| `默认复习间隔` | formula | RO | Default interval string (**not in SQL**) |
| `复习` | button | N/A | Triggers review in Notion UI (**not in SQL**) |
| `艾宾浩斯复习记录` | relation | RO | Linked review records |

### SQL availability

`notion-query-data-sources` exposes writable/simple columns only. Formulas and the button above are listed in Notion as `notAvailableInQuerySql` — filter candidates in SQL (`批量复习`, `归档`, text fields), then `notion-fetch` pages to read due dates.

## Database 2: 艾宾浩斯复习记录

**Data source ID:** `29ea2efb-b18d-8165-a3e7-000b09e45612`
**Location:** Under knowledge -> 艾宾浩斯记忆

### Fields

| Field | Type | Read/Write | Description |
|-------|------|------------|-------------|
| `备注` | title | RW | Note about the review outcome |
| `文件链接` | text | RW | Link to card page |
| `日期` | date | RW | Date of review |
| `状态` | status | RW | one of "未开始" / "进行中" / "完成" |
| `艾宾浩斯` | relation | RW | Link to the card (single-relation, limit 1) |

## Database 3: Knowledge Units (related)

**Data source ID:** `a0837cf8-c21b-4877-a713-63a8cb0d5dc5`

The card's `Knowledge Units` relation points here. When the user wants deeper context during review, fetch the linked Knowledge Unit page to access its full Thinking Pipeline content.

Key fields for review context:
- `Name`, `Type`, `Status`, `Domain`
- `Problem`, `Essence`, `Tradeoff`, `Transfer`, `Boundary`
- `Review Question`, `Review Answer`
- `Before`, `After` (for Type=Update)
- `Review Cards` (relation back to Ebbinghaus cards)
