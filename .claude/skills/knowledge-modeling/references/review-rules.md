# Review Rules

Use this reference when deciding whether a knowledge unit should create an Ebbinghaus review card.

## Create Review Cards For

1. **Precise concepts**
   - The user should recall the definition or key distinction without opening notes.
   - Example: "What does volatile guarantee and not guarantee?"

2. **High-frequency contrasts**
   - The idea is commonly confused.
   - Example: "volatile vs synchronized", "visibility vs atomicity", "happens-before vs execution order".

3. **Operational judgment sentences**
   - The sentence should guide future decisions.
   - Example: "Use volatile for state publication, not compound updates."

4. **Small mechanisms**
   - The mechanism can be compressed into one question and one answer.
   - Example: "What happens-before edge does volatile write/read create?"

## Do Not Create Review Cards For

- Full article summaries.
- Broad models that are better learned by applying them to cases.
- Unverified speculation.
- Low-value details that are searchable and not decision-relevant.
- Anything that cannot fit into one question and one concise answer.

## Card Format

```text
Question:
Answer:
Linked Knowledge Unit:
Why review:
```

## Review Threshold

Before marking `Memory = true`, ask:

- Will forgetting this block future understanding?
- Will I need this in interviews, debugging, design, or code review?
- Can this be recalled as a crisp answer?

If fewer than two answers are yes, keep `Memory = false`.
