---
name: notion-sync
description: >-
  Local-first sync between Notion Knowledge Units and the local Obsidian vault.
  Pull Notion pages into local Markdown files, push local edits back to Notion,
  and produce local-first drafts for review before publishing to Notion.
  Use when the user wants to pull from Notion, sync notes, push a local file to
  Notion, or says "拉取 notion", "同步笔记", "sync notion", "把 X 推到 notion",
  "X 改了同步一下", "notion 同步", "同步一下笔记".
---

# Notion Sync

## Purpose

Keep the local Obsidian vault and the Notion Knowledge Units database in step, with one principle:

> **Obsidian is the local working copy and review surface; Notion is the final source of truth.**

Every agent write goes **local-first**: produce a local Markdown file for the user to review, then push to Notion after confirmation. There is no background auto-sync, no file watcher. Sync only happens when explicitly invoked — as a pull, a push, or a local-first write produced by `knowledge-modeling`.

The Ebbinghaus memory database is **out of scope** — it holds process data (review counts, next-review dates are Notion formulas that change constantly), so a local copy would be permanently stale. Reviews read Notion directly via `knowledge-review`.

## How this skill works: agent + script

Two parts collaborate, and each does only what it can do:

- **The agent** does all Notion I/O via MCP (`notion-query-data-sources`, `notion-fetch`, `notion-search`, `notion-create-pages`, `notion-update-page`). No script can call these — they live in the session.
- **`sync.js`** (this folder) does all local work: parse/build markdown + frontmatter, maintain `.notion-sync-index.json`, run the three-state pull decision, emit Notion write parameters for push. Zero Node dependencies.

So the workflow is always: agent fetches from Notion → assembles a `pages.json` → runs `sync.js pull`; or runs `sync.js push <file>` → takes its JSON output → calls the Notion MCP tool. Never hand-write frontmatter or edit the index manually — let the script do it.

## Trigger

Use this skill when:
- The user says any of the following (or variations):
  - "拉取 notion", "同步笔记", "notion 同步", "同步一下笔记"
  - "把 X 推到 notion", "X 改了同步一下", "推一下这个笔记"
  - "sync notion", "pull from notion", "push to notion"
- The user wants to backfill local files from Notion (cold start / new machine / catch up)
- The user edited a local Knowledge Unit file and wants it reflected in Notion
- The user renamed a local file and wants the rename reflected in Notion
- `knowledge-modeling` finishes a capture and needs to write local-first (Step 3 below)

## Vault layout

- **Vault root = repository root** (the Obsidian vault is the whole repo).
- Knowledge Units live under `knowledge-unit/<Domain>/`, e.g. `knowledge-unit/Java/虚拟机栈深度为何有限.md`.
- All paths are relative to the repository root, so the same layout works across machines via git.

## Sync index

A single index file at the repository root tracks sync state: **`.notion-sync-index.json`**.

- It is keyed by **Notion page id**, never by filename (filenames change on rename; ids do not).
- It is committed to git, so a fresh machine can clone and do an incremental pull without re-downloading everything.
- `last_edited_time` stored in the index is the Notion-side value (objective), so cross-machine incremental comparison is valid. `synced_at` is local-action time and may drift across machines — that is harmless, since incremental decisions depend on `last_edited_time` only.
- The index and each file's frontmatter `notion_id` are redundant cross-checks; either can rebuild the other.

See [references/local-format.md](references/local-format.md) for the full schema.

## Workflow

### Step 1: Pull (Notion → Local)

Pull Knowledge Units from Notion into local files. The agent does the Notion I/O; the script does all local work (write files, update index, three-state decision, report).

1. **Fetch the candidate set via SQL** (`notion-query-data-sources`):

   ```sql
   SELECT url, "Name", "Type", "Status", "Domain", "Source URL", "Memory",
          "date:Created:start"
   FROM "collection://a0837cf8-c21b-4877-a713-63a8cb0d5dc5"
   WHERE "Status" != 'Archived'
   ```

2. **Read `last_edited_time` per page via `notion-fetch`.** This is a Notion system field — it updates automatically on any write (including agent writes via `knowledge-modeling`), so no skill needs to maintain it. Fetch the page body at the same time. For blank Notion pages (no body), rebuild `content` from the structured properties (Essence/Problem/Tradeoff/Transfer/Boundary) — see [references/local-format.md](references/local-format.md).

3. **Assemble a `pages.json` array** (one object per page) and hand it to the script:

   ```json
   [{
     "id": "<32-hex notion page id>",
     "url": "https://app.notion.com/p/<id>",
     "name": "<Name property>",
     "last_edited_time": "<from notion-fetch as-of timestamp>",
     "type": "<Type>", "status": "<Status>", "domain": "<Domain, single tag>",
     "source_url": "<Source URL>", "memory": "__YES__|__NO__",
     "review_question": "...", "review_answer": "...",
     "content": "<markdown body; '' ok for blank pages>"
   }]
   ```

4. **Run the script** to do the local work:

   ```bash
   .agents/skills/notion-sync/sync.js pull /tmp/pages.json --full
   ```

   - Append `--full` when this is a **complete** pull of the data source (the normal case). `--full` enables the reverse scan that flags pages Notion deleted. Omit it for partial pulls (e.g. syncing one page) to avoid false "notion-side deleted" alarms.
   - The script prints a report (created / updated / skipped / suspected) and updates `.notion-sync-index.json` itself.

5. **Three-state decision** is done by the script, keyed by Notion page id (never filename):

   | State | Meaning | Script action |
   |-------|---------|---------------|
   | id in index **and** index filename exists locally | known page | Compare `last_edited_time`: equal → skip; newer → back up old to `.notion-sync-trash/`, overwrite |
   | id in index **but** index filename **not found locally** | ⚠️ suspected rename or deletion | Listed under `suspected`; **no auto-change** — ask the user |
   | id **not** in index | new Notion page | Create local file under `knowledge-unit/<Domain>/` |

6. **Act on `suspected` entries.** For each, ask the user whether it was renamed or deleted (never auto-delete). On rename, the push path (Step 2) updates the Notion `Name` and the index `filename` automatically since the anchor is the id.

7. **Fallback**: if `last_edited_time` cannot be obtained, set it to the current time so the script treats the page as updated and overwrites.

### Step 2: Push (Local → Notion)

Push a local Knowledge Unit file back to Notion. Explicit trigger only (the user names the file).

1. **Get the Notion write parameters from the script:**

   ```bash
   .agents/skills/notion-sync/sync.js push knowledge-unit/<Domain>/<Name>.md
   ```

   The script reads the file, parses frontmatter + body, and emits a JSON object: `action` (`update` if `notion_id` present, else `create`), `properties`, `content`, and `notes`.

2. **Deduplicate before writing**: `notion-search` first (the strong project convention from `knowledge-modeling`). If a same-name unit exists, default to update/relate rather than creating a duplicate.

3. **Call the Notion MCP tool** based on `action`:
   - `update` → `notion-update-page` on `notion_id` (properties + content). This also handles **rename**: if the file was renamed, the `Name` property is updated to the new title. Renames are correct automatically because the anchor is the id, not the filename.
   - `create` → `notion-create-pages` with parent type `data_source_id`.

4. **Obey every Notion API quirk** from `knowledge-modeling`:
   - Checkbox fields (e.g. `Memory`): string `"__YES__"` / `"__NO__"`, never booleans/numbers.
   - Multi-select (`Domain`): single string value only, no comma-separated list.
   - `Source URL`: goes inside `properties`, not as a top-level page key.
   - Relations: JSON array `["url"]` for multi, JSON string `"url"` for single.

5. **After a successful push**, write back the sync metadata:
   - Update the local file's frontmatter: `notion_url` (and `notion_id` for a create), `synced_at` = now.
   - Update `.notion-sync-index.json`: set `last_edited_time` (re-fetch the page's as-of timestamp, or use now) and `synced_at` = now. (Re-running `sync.js pull` on just that one page with `--full` off is the easiest way to refresh both.)

6. **On failure**: report immediately ("本地文件已就绪，Notion 推送失败：<reason>，请重试"). The local file is untouched and can be retried.

### Step 3: Local-first write (used by knowledge-modeling)

When `knowledge-modeling` produces a finalized Knowledge Unit, the write flow is local-first:

1. **Write local first**: create `knowledge-unit/<Domain>/<Name>.md` with frontmatter (per [references/local-format.md](references/local-format.md)) and the Thinking Pipeline body. At this point frontmatter has **no `notion_id`** yet — it gets filled after the push.
2. **User reviews** the local file in Obsidian.
3. **After confirmation, push to Notion** using Step 2 of this skill.

The local file is the review surface; Notion remains the final source of truth. See the updated Step 5 of `knowledge-modeling` for how the two skills connect.

### Status check

Run anytime to inspect local-vs-index consistency:

```bash
.agents/skills/notion-sync/sync.js status
```

Reports tracked count, local file count, by-domain breakdown, and any files missing locally or missing from the index.

## Routing

| User intent | Use |
|-------------|-----|
| Pull from Notion / "同步笔记" / backfill local | **notion-sync** |
| Push a local file to Notion / "X 改了同步" / rename sync | **notion-sync** |
| Learn / compress / capture (writes local-first, then pushes) | `knowledge-modeling` (uses notion-sync's format) |
| Search / organize / wikilink inside the Obsidian vault (no Notion) | `obsidian-vault` |
| Spaced-repetition review | `knowledge-review` (reads Notion directly, never lands local) |

Boundary with `obsidian-vault`: this skill moves files between Notion and the `knowledge-unit/` tree; `obsidian-vault` handles in-vault search, naming, and wikilinks once files exist locally.

## Operating Rules

- Notion is the source of truth; the local vault is the review and working copy.
- Always key sync state by **Notion page id**, never by filename.
- **Prefer the script for local mutations.** Use `sync.js pull/push/status` for writing files, parsing frontmatter, and updating the index. Never hand-edit `.notion-sync-index.json` or hand-write sync frontmatter when the script can do it — the script owns the three-state logic and the index format.
- Never auto-resolve a suspected rename or deletion — ask the user. The cost of a wrong delete is far higher than one confirmation.
- Pull never deletes local files whose Notion side disappeared — report them instead.
- Push before write: always `notion-search` to deduplicate (project convention).
- Only sync the Knowledge Units database. Never pull the Ebbinghaus memory database into local files.
- Obey all Notion API quirks documented in `knowledge-modeling` (checkbox strings, single-value multi-select, `Source URL` inside `properties`).
- Do not add a `push_status` field. Push is explicit; on failure, report and leave the local file for retry.
- When in doubt about the local file format or index schema, consult [references/local-format.md](references/local-format.md).
- Discover tool schemas with `GetMcpTools` before calling unfamiliar Notion tools.

## Optional: SessionStart hook (not configured)

This skill is designed for manual invocation. If you later want to auto-pull on session start, add a hook yourself. Example shape (ZCode hook config, not written by this skill):

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "*",
        "hooks": [{ "type": "command", "command": "echo 'pull notion'" }]
      }
    ]
  }
}
```

The actual pull is done by invoking this skill; the hook is only a reminder/trigger and is left for the user to configure.

## References

- [sync.js](sync.js): the local sync engine. Run `sync.js` with no args for usage. Zero Node dependencies.
- [references/local-format.md](references/local-format.md): frontmatter field mapping, file naming, wikilink conventions, the `.notion-sync-index.json` schema, and the rename/delete three-state decision flow.
