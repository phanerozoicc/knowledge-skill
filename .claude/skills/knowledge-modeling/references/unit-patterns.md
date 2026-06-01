# Knowledge Unit Patterns

Use this reference when shaping raw input into knowledge units.

## Field Meanings

- `Name`: A compact claim, not a topic label. Prefer "volatile is a visibility contract" over "volatile".
- `Type`: `Raw`, `Insight`, `Model`, `Principle`, `Update`, or `Reference`.
- `Status`: `Inbox`, `Draft`, `Active`, `Stable`, or `Archived`.
- `Domain`: Technical area tags. Use them for retrieval, not hierarchy.
- `Problem`: The pressure that made this idea necessary.
- `Essence`: The smallest useful understanding.
- `Tradeoff`: What is sacrificed, constrained, or made more expensive.
- `Transfer`: Other places where the same idea appears.
- `Boundary`: When the idea stops applying.
- `Before` / `After`: Use only for `Update`.
- `Memory`: Whether this should produce spaced-repetition material.

## Type Guide

### Raw

Use for material that feels promising but is not yet compressed.

Example:

```text
Name: volatile article notes
Type: Raw
Status: Inbox
Essence: Mentions visibility, happens-before, and instruction reordering.
```

### Insight

Use for concrete understanding.

```text
Name: volatile separates visibility from atomicity
Type: Insight
Problem: Threads may observe stale shared state.
Essence: volatile makes writes visible to later reads but does not make read-modify-write atomic.
Tradeoff: Less coordination cost than locks, but weaker correctness guarantees.
Transfer: stop flags, readiness markers, config switches.
Boundary: Not enough for increments or compound invariants.
```

### Model

Use only when multiple insights share the same structure.

```text
Name: Feedback Control
Type: Model
Problem: A system cannot precompute the correct behavior under changing conditions.
Essence: Observe feedback, compare, adjust, repeat.
Transfer: TCP congestion control, circuit breakers, adaptive thread pools.
```

### Principle

Use for stable judgment.

```text
Name: Shared State Creates Coordination Cost
Type: Principle
Essence: Once multiple actors can observe or mutate the same state, local changes become coordination problems.
Boundary: Immutable or single-writer state can keep the cost contained.
```

### Update

Use when understanding changes.

```text
Name: TCP is not just reliable delivery
Type: Update
Before: TCP is a reliable transport protocol.
After: TCP is also a feedback-control system around congestion and delivery signals.
```

### Reference

Use only for source traceability.

```text
Name: Jenkov - Java volatile keyword
Type: Reference
Source URL: https://jenkov.com/tutorials/java-concurrency/volatile.html
Essence: Source article for volatile visibility and happens-before discussion.
```

## Anti-Patterns

- Do not create a unit named only after a broad topic, such as `Java Memory Model`.
- Do not paste a full article summary into `Essence`.
- Do not promote an idea to `Model` because it sounds abstract; require multiple concrete cases.
- Do not make every interesting thing a flashcard.
- Do not split `Insight`, `Model`, and `Principle` into separate databases unless the user explicitly accepts the maintenance cost.
