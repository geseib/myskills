# dashboard-management

Auto-generated eval dashboard from JSONL results.

## What it does

Reads `eval-results/*/results.jsonl` files and generates a `dashboard.md` with cross-model comparisons, version history, skill impact vs baseline, and cost-aware best-for-task rankings.

## Dashboard sections

- **Overview table** — skill name, status, version, rating, eval count, skill impact
- **Version history per model** — scores across versions with best marker (cheapest model at highest score)
- **Eval results** — per-eval scores with model and type columns
- **Cross-model comparison** — Haiku vs Sonnet vs Opus per eval
- **Best for task** — cheapest model that achieves the highest score per eval
- **Skill impact** — with-skill vs without-skill baseline comparison

## When it triggers

- After recording eval results
- When asked to show skill status or dashboard
- After promoting a skill

## JSONL format

```json
{
  "eval_id": "happy-path-rest-api",
  "run_id": "2026-04-01T12:00:00Z",
  "skill_version": "v1",
  "skill_commit": "abc1234",
  "model": "claude-sonnet-4-6",
  "with_skill": true,
  "eval_set_version": "v1",
  "score": "9/11",
  "overall": "pass",
  "notes": "Missed rate limiting."
}
```

## Works well with

- [eval-methodology](../eval-methodology) — how to run fair evals
- [eval-rebase](../eval-rebase) — eval versioning and consistency enforcement

## Source

Developed in [myskills](https://github.com/geseib/myskills). Dashboard generator is `scripts/generate-dashboard.py`.
