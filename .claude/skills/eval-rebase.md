# Eval Rebase

Ensure eval consistency across skill versions. Track eval lineage so every score is traceable to the exact criteria that produced it.

## When to use

TRIGGER when:
- Evals are added, removed, or modified for a skill
- A version has incomplete eval coverage compared to other versions
- Asked to "rebase evals", "update evals", or "fix eval coverage"
- Dashboard shows ⚠️ coverage warnings or uneven eval counts across versions

## Core principles

1. **Same evals, every version, every model.** A version's score is only meaningful when tested against the full eval set on all models.
2. **Evals are versioned.** Every eval file and the eval set as a whole have version tags. Results record which eval version produced the score.
3. **Lineage is traceable.** Given any result in JSONL, you can determine: which skill version, which eval criteria version, and which model.

## Eval versioning

### Individual eval files

Every eval file carries a version tag and change notes in its header:

```markdown
<!-- eval-version: v1 -->
<!-- eval-notes: v1=Original criteria -->
# Eval: Basic app — e-commerce orders
```

When modifying criteria (adding/removing checkboxes, changing pass thresholds, tightening scoring):
1. Bump the eval-version tag
2. Add the change to eval-notes
3. Archive the previous version in `evals/versions/` (e.g., `eval-happy-path-basic-app.v1.md`)

### Eval set manifest

Each skill maintains an `evals/eval-set.md` manifest that ties together the current eval files and their versions:

```markdown
<!-- eval-set-version: v1 -->
<!-- eval-set-notes: v1=Initial 7-eval set -->
# Eval Set: dynamodb-single-table

| Eval ID | File | Eval Version | Type |
|---------|------|-------------|------|
| happy-path-basic-app | eval-happy-path-basic-app.md | v1 | happy-path |
| happy-path-multi-tenant | eval-happy-path-multi-tenant.md | v1 | happy-path |
| happy-path-realtime | eval-happy-path-realtime.md | v1 | happy-path |
| edge-case-many-to-many | eval-edge-case-many-to-many.md | v1 | edge-case |
| edge-case-time-series | eval-edge-case-time-series.md | v1 | edge-case |
| edge-case-migration | eval-edge-case-migration.md | v1 | edge-case |
| adversarial-kitchen-sink | eval-adversarial-kitchen-sink.md | v1 | adversarial |
```

Bump `eval-set-version` when:
- An eval file is added or removed from the set
- Any eval file's `eval-version` is bumped

### JSONL schema

Results must include `eval_set_version` to record which eval criteria produced the score:

```json
{
  "eval_id": "happy-path-basic-app",
  "run_id": "2026-04-01T14:00:00Z",
  "skill_version": "v3",
  "skill_commit": "abc1234",
  "model": "claude-sonnet-4-6",
  "with_skill": true,
  "eval_set_version": "v1",
  "score": "11/11",
  "overall": "pass",
  "notes": "Perfect score."
}
```

This creates full lineage: **skill v3 + eval-set v1 + Sonnet = 11/11**.

## When evals are updated

Follow this protocol whenever an eval case is added, removed, or materially changed:

### Step 1: Version the change

1. Bump `eval-version` in the changed eval file(s)
2. Archive previous eval version(s) to `evals/versions/`
3. Update `eval-set.md` manifest — bump `eval-set-version`

### Step 2: Identify affected skill versions

- **Current version** — must always be re-evaluated against the new eval set
- **Previous version** — must be re-evaluated for fair "vs previous" comparison
- **Older versions** — mark as `deprecated` (tested against an older eval set)

### Step 3: Re-run evals

Run the new eval set against current and previous skill versions, on all 3 models (Haiku, Sonnet, Opus). Record results with the new `eval_set_version`.

### Step 4: Mark deprecated versions

Append a deprecation marker to results.jsonl for any skill version NOT re-evaluated against the new eval set:

```json
{"eval_id":"_deprecation","run_id":"2026-04-01T14:00:00Z","skill_version":"v1","skill_commit":"abc1234","model":"all","with_skill":true,"eval_set_version":"v1","score":"0/0","overall":"deprecated","notes":"Tested against eval-set v1 only. Not re-evaluated against eval-set v2. Do not compare directly to v2+ scores."}
```

### Step 5: Regenerate dashboard

```bash
python3 scripts/generate-dashboard.py
```

Dashboard should:
- Show deprecated versions with ⚠️ marker
- Only compare non-deprecated versions in "vs previous"
- Show eval set version in results tables

## Coverage check before committing

```
For each active (non-deprecated) skill version:
  For each model (Haiku, Sonnet, Opus):
    For each eval in current eval-set manifest:
      Result must exist with matching eval_set_version
```

If any cell is missing, either run the missing eval or mark the skill version as deprecated.

## Anti-patterns

1. **Partial re-evaluation** — running new evals on only one model or one version
2. **Comparing across eval sets** — v1 scored on eval-set v1 vs v2 scored on eval-set v2 is misleading without re-evaluation
3. **Silently changing evals** — always bump version, archive old, and re-run affected skill versions
4. **Deleting old results** — append new results, never delete (results.jsonl is append-only)
5. **Missing eval_set_version in JSONL** — every result must trace back to the exact eval criteria
