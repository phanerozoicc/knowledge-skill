---
name: research
description: >-
  Investigate a question against high-trust primary sources (official docs,
  source code, specs, first-party APIs) and write findings as a cited Markdown
  file in the repo. Use when the user wants primary-source research, API/docs
  fact-gathering, or "调研一下 / 查官方文档 / 一手资料" — not for social/platform
  browsing (use agent-reach) and not for Notion knowledge capture
  (use knowledge-modeling after facts are gathered).
---

Spin up a **background agent** (Cursor: `Task` with `run_in_background: true`; Claude Code: equivalent background agent) so the main session can keep working while it reads.

Its job:

1. Investigate the question against **primary sources** — official docs, source code, specs, first-party APIs — not a secondary write-up of them. Follow every claim back to the source that owns it.
2. Write the findings to a single Markdown file, citing each claim's source.
3. Save it where the repo already keeps such notes; match the existing convention, and if there is none, put it somewhere sensible and say where.

**Not this skill:** platform/social search → `agent-reach`. Settling understanding into Notion → `knowledge-modeling`.
