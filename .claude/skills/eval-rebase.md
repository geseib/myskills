# Eval Rebase

Ensure eval consistency across skill versions. When evals change, rebase results so comparisons remain fair.

## When to use

TRIGGER when:
- Evals are added, removed, or modified for a skill
- A version has incomplete eval coverage compared to other versions
- Asked to "rebase evals", "update evals", or "fix eval coverage"
- Dashboard shows ⚠️ coverage warnings or uneven eval counts across versions

## Core principle

**Same evals, every version, every model.** A version's score is only meaningful when tested against the full eval set on all models. Partial coverage produces misleading comparisons.

## Rules

1. **All versions of a skill run the same eval set.** If v1 ran 7 evals, v2 and v3 must also run those same 7 evals on all 3 models.
2. **When evals change, the current and previous version must both be re-evaluated** against the new eval set so comparisons remain valid.
3. **Mark deprecated versions.** Versions that have NOT been tested against the current eval set are marked `deprecated` in results. Their scores should not be compared to non-deprecated versions.
4. **Never delete old results.** Append new results with updated evals; old results stay for audit trail.

## When evals are updated

Follow this protocol whenever an eval case is added, removed, or materially changed:

### Step 1: Document the change

Add a comment to the eval file header explaining what changed and why:
```
<!-- eval-version: v2 -->
<!-- change-notes: v1=Original criteria; v2=Added rate-limiting check, tightened scoring -->
```

### Step 2: Identify affected versions

Determine which skill versions need re-evaluation:
- **Current version** — must always be re-evaluated
- **Previous version** — must be re-evaluated for fair comparison
- **Older versions** — mark as `deprecated` unless explicitly re-evaluated

### Step 3: Re-run evals

Run the updated eval set against current and previous versions, on all 3 models (Haiku, Sonnet, Opus).

### Step 4: Mark deprecated versions

Append deprecation markers to results.jsonl for any version NOT re-evaluated against the new evals:

```json
{"eval_id":"_deprecation","run_id":"2026-04-01T14:00:00Z","skill_version":"v1","skill_commit":"abc1234","model":"all","with_skill":true,"score":"0/0","overall":"deprecated","notes":"v1 results based on eval-set-v1. Not re-evaluated against eval-set-v2. Do not compare directly to v2+ scores."}
```

### Step 5: Regenerate dashboard

```bash
python3 scripts/generate-dashboard.py
```

The dashboard should reflect:
- Deprecated versions shown with ⚠️ marker
- Only non-deprecated versions compared in "vs previous"
- Coverage warnings cleared for re-evaluated versions

## Checking coverage before committing

Before pushing eval results, verify complete coverage:

```
For each active (non-deprecated) version:
  For each model (Haiku, Sonnet, Opus):
    All eval_ids must have results
```

If any cell is missing, either run the missing eval or mark the version as deprecated.

## Anti-patterns

1. **Partial re-evaluation** — running new evals on only one model or one version
2. **Comparing across eval sets** — v1 scored on old evals vs v2 scored on new evals is meaningless
3. **Silently changing evals** — always document what changed and re-run affected versions
4. **Deleting old results** — append new results, never delete (results.jsonl is append-only)
