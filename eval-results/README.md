# Eval Results Tracking

This directory stores structured eval results for comparing skill performance across versions, models, and time.

## Directory structure

```
eval-results/
  <skill-name>/
    results.jsonl          # Append-only log of all eval runs
    summary.md             # Auto-generated comparison view
```

## Result format (JSONL)

Each line in `results.jsonl` is a JSON object:

```json
{
  "eval_id": "happy-path-basic-app",
  "run_id": "2026-04-01T11:45:00Z",
  "skill_version": "v1",
  "skill_commit": "72d5c3f",
  "model": "claude-opus-4-6",
  "with_skill": true,
  "criteria": {
    "access_patterns_first": { "pass": true, "notes": "" },
    "generic_pk_sk": { "pass": true, "notes": "" },
    "entity_prefixes": { "pass": true, "notes": "" },
    "gsi_count_ok": { "pass": true, "notes": "1 GSI used" },
    "no_scan": { "pass": true, "notes": "" },
    "entity_chart": { "pass": true, "notes": "" },
    "iac_included": { "pass": false, "notes": "Missing IaC output" }
  },
  "overall": "partial",
  "score": "6/7",
  "response_length": 1850,
  "notes": "Missed IaC output but design was sound"
}
```

## Fields

| Field | Description |
|-------|-------------|
| `eval_id` | Matches the eval case filename (without `eval-` prefix and `.md` suffix) |
| `run_id` | ISO timestamp of the eval run |
| `skill_version` | Semantic version tag (v1, v1.1, v2, etc.) |
| `skill_commit` | Git short SHA of the skill.md at time of eval |
| `model` | Model ID used (e.g., claude-opus-4-6, claude-sonnet-4-6) |
| `with_skill` | `true` = skill loaded, `false` = baseline (no skill) |
| `criteria` | Object mapping each criterion to pass/fail + notes |
| `overall` | `pass`, `partial`, or `fail` |
| `score` | Fraction of criteria passed |
| `response_length` | Approximate word count of response |
| `notes` | Free-text observations |

## Versioning

Skill versions are tagged in `skill.md` frontmatter and tracked in results:

```markdown
<!-- skill-version: v1 -->
```

When you modify a skill's prompt, bump the version. This lets you compare results across prompt iterations.

## Generating summaries

The `summary.md` for each skill is a markdown table comparing results across versions and models. Regenerate it from the JSONL data whenever you run new evals.
