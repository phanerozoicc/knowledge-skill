---
name: obsidian-vault
description: >-
  Search, create, and manage notes in the Obsidian vault with wikilinks.
  Use when the user wants to find, create, or organize notes in Obsidian,
  or says "Obsidian", "笔记库", "找一下笔记", "创建新笔记", "整理索引".
---

# Obsidian Vault

## Vault location

The Obsidian vault root is the **repository root** (the whole repo is the vault). All paths below are relative to the repo root, so the same layout works across machines via git.

The Knowledge Units tree `knowledge-unit/<Domain>/` is managed by the `notion-sync` skill — those files mirror the Notion Knowledge Units database and are written local-first by `knowledge-modeling`. When working inside `knowledge-unit/`, follow the naming and frontmatter conventions from `notion-sync`'s [references/local-format.md](../notion-sync/references/local-format.md).

Other notes may live in **topic folders** (e.g. `AI/`, `Kubernetes/`, `分布式/`, `java知识体系/`), not a flat root. Prefer placing new non-Knowledge-Unit notes inside the matching folder.

## Naming conventions

- Prefer the existing folder's naming style (often Chinese topic titles; numbered sequences like `01. 容器基础.md` where already used)
- **Title Case** for English-only note names
- Use folders for domain grouping; use `[[wikilinks]]` for cross-links within and across folders

## Linking

- Use Obsidian `[[wikilinks]]` syntax: `[[Note Title]]` or `[[path/Note Title]]`
- Related notes: list `[[wikilinks]]` at the bottom of the note

## Workflows

### Search for notes

Use Grep/Glob on the vault root (preferred), or:

```bash
# Search by filename
find . -name "*.md" | grep -i "keyword"

# Search by content
grep -rl "keyword" . --include="*.md"
```

### Create a new note

1. Pick the topic folder that matches the domain; create the folder only if none fits
2. Match that folder's filename style
3. Write the note; add `[[wikilinks]]` to related notes at the bottom
4. If part of a numbered sequence in that folder, continue the numbering

### Find related notes / backlinks

```bash
grep -rl "\[\[Note Title\]\]" .
```

### Find index-style notes

```bash
find . -iname "*index*" -o -iname "*索引*"
```
