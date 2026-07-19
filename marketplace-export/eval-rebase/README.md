# eval-rebase

Eval versioning and consistency enforcement for skill evaluations.

## What it does

Tracks eval lineage so every score is traceable to the exact criteria, skill version, and model that produced it. When evals change, enforces re-evaluation of current and previous skill versions to keep comparisons fair.

## Key principles

- **Same evals, every version, every model** — partial coverage produces misleading comparisons
- **Evals are versioned** — individual eval files and the eval set as a whole carry version tags
- **Lineage is traceable** — every JSONL result records `eval_set_version` alongside `skill_version` and `model`
- **Deprecated versions** — skill versions not re-tested against updated evals are marked deprecated

## When it triggers

- Evals are added, removed, or modified
- A version has incomplete eval coverage
- Dashboard shows coverage warnings or uneven eval counts

## Eval versioning structure

```
evals/
  eval-set.md                    # Manifest: lists all evals + their versions
  eval-happy-path-basic.md       # <!-- eval-version: v1 -->
  eval-edge-case-tricky.md       # <!-- eval-version: v2 -->
  versions/
    eval-edge-case-tricky.v1.md  # Archived previous version
```

## Works well with

- [eval-methodology](../eval-methodology) — how to run fair evals
- [dashboard-management](../dashboard-management) — auto-generated dashboard from results

## Source

Developed in [myskills](https://github.com/geseib/myskills) after discovering that incomplete v2 eval coverage (4/7 vs 7/7) made version comparisons misleading.
