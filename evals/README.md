# Evals

Evals validate that skills behave correctly and reliably. Each skill should have eval cases that cover its core behavior before promotion to `skills/`.

## Where evals live

- **Skill-specific evals:** `skills/<name>/evals/` or `drafts/<name>/evals/`
- **Eval template:** `templates/eval-case.md`

## Eval types

| Type | Purpose |
|------|---------|
| `happy-path` | Does the skill work for its intended use case? |
| `edge-case` | Does it handle unusual but valid inputs? |
| `regression` | Does it still work after a change? (captures past failures) |
| `adversarial` | Does it stay within its boundaries when pushed? |

## Writing good evals

1. **Be specific.** "It should work" is not an eval. "It should create a file at X with contents Y" is.
2. **Include negatives.** What should the skill NOT do? Over-triggering and side effects are common failure modes.
3. **Cover the trigger.** For auto-trigger skills, test that it fires when it should AND stays quiet when it shouldn't.
4. **Keep them fast.** An eval you don't run is worthless. Each case should be testable in a single Claude interaction.

## Running evals

1. Start a Claude Code session with the target skill loaded
2. Paste the eval prompt
3. Check behavior against the expected/should-not criteria
4. Mark pass/fail

## Eval versioning

Evals are versioned to maintain lineage between scores and the criteria that produced them.

### Individual eval files

Every eval file carries a version tag:

```markdown
<!-- eval-version: v1 -->
<!-- eval-notes: v1=Original criteria -->
# Eval: My eval name
```

When modifying criteria, bump `eval-version`, update `eval-notes`, and archive the old version in `evals/versions/`.

### Eval set manifest

Each skill maintains `evals/eval-set.md` — a manifest listing all eval files and their versions. Bump `eval-set-version` when any eval is added, removed, or version-bumped.

### Results lineage

Every result in `results.jsonl` includes `eval_set_version` to trace which criteria produced the score. See `.claude/skills/eval-rebase.md` for the full protocol on maintaining consistency when evals change.

## When to write evals

- **Before promoting** a draft to production — minimum: 2 happy-path, 1 edge-case
- **When a skill fails** in real use — write a regression eval capturing the failure
- **When modifying** a production skill — run existing evals, add new ones for the change
