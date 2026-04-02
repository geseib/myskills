---
name: dashboard-management
description: Manages the skills dashboard. Regenerates it after eval runs, validates accuracy, and ensures fair comparisons across models and versions.
user-invocable: false
---

# Dashboard Management

Manage the skills dashboard — regenerate it after eval runs, validate its accuracy, and ensure it reflects fair comparisons.

## When to use

TRIGGER when:
- After recording eval results to any `eval-results/<skill>/results.jsonl`
- When asked to show skill status, dashboard, or eval results
- When asked to "regenerate" or "update" the dashboard
- After promoting a skill from drafts/ to skills/

## How to regenerate

```bash
python3 scripts/generate-dashboard.py
```

This reads all `eval-results/*/results.jsonl` files and generates `dashboard.md`.

## What the dashboard shows

### Overview table
- Skill name, status (draft/prod), current version, rating, eval count, skill impact

### Per-skill sections
- **Version notes** — brief description of what changed per version (from `<!-- version-notes: ... -->` in SKILL.md)
- **Version history (per model)** — baseline rows first (no skill), then version rows (with skill), with ⭐ on best (cheapest model at highest score). Baseline is the reference point — compare version rows against it to see skill impact
- **Coverage warnings** — ⚠️ when current version has fewer evals than previous
- **Cross-model comparison** — per-eval scores across all models for current version
- **Best for task** — cheapest model that achieves the highest score per eval

## After recording results, always

1. Run `python3 scripts/generate-dashboard.py`
2. Review the output for:
   - ⚠️ coverage warnings (incomplete version comparisons)
   - Unexpected score patterns (baselines shouldn't all be 100%)
   - Missing models in cross-model tables
3. Commit the updated `dashboard.md` alongside the results

## Adding version notes

When bumping a skill version, add or update the frontmatter in SKILL.md:

```
<!-- skill-version: v2 -->
<!-- version-notes: v1=Initial skill with core patterns; v2=Added feed fanout and migration guidance -->
```

These appear in the dashboard's "Version notes" section.

## Dashboard accuracy checks

The dashboard script (`scripts/generate-dashboard.py`) enforces:
- **Cost-aware ⭐ markers** — cheapest model wins ties (Haiku < Sonnet < Opus)
- **Coverage flags** — ⚠️ when a version ran fewer eval_ids than the previous
- **Fair Skill Impact** — only compares with-skill vs baseline on matching eval+model pairs
- **Eval count visibility** — shows how many evals each model ran per version

## JSONL format for results

Each line in `eval-results/<skill>/results.jsonl`:

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
  "notes": "Missed rate limiting on one endpoint."
}
```

For baselines, use `"skill_version": "baseline"` and `"with_skill": false`.
