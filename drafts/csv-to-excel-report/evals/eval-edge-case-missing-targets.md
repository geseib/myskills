<!-- eval-version: v1 -->
<!-- eval-notes: v1=Original criteria -->
# Eval: Reps with missing targets

**Skill:** `csv-to-excel-report`
**Type:** edge-case

## Setup

Use sample sales data as-is. Modify sample targets CSV to remove target rows for 3 reps in Q1 and Q2: Sarah Chen (Q1, Q2), Marcus Williams (Q1, Q2), and Kevin Zhang (Q1). This simulates mid-year hires or late target assignment.

## Prompt

```
Generate my sales report from these two CSVs. Note: we just hired a few new reps mid-year so they won't have targets for Q1 and Q2 — the targets CSV only has their Q3 and Q4 entries.
```

## Expected behavior

- [ ] Does not crash when some sales rows have no matching target
- [ ] Uses left join — keeps all sales rows even without targets
- [ ] Achievement % and variance show as blank or "N/A" for missing targets (not 0%, not #DIV/0!)
- [ ] Executive Summary KPIs still calculate correctly (revenue based on all sales, not just matched)
- [ ] Regional summary handles partial target coverage gracefully
- [ ] Mentions or warns about reps with missing targets in stdout output
- [ ] Top 5 performers table still works (ranks by revenue, not achievement %)
- [ ] Does not silently drop rows without targets

## Should NOT

- Should not inner-join and lose sales rows
- Should not show division-by-zero errors or "inf" in the Excel file
- Should not display Python "nan" or "NaN" in cells
- Should not crash with a KeyError or TypeError
- Should not count missing-target reps differently in the rep count KPI

## Pass criteria

All sales rows preserved in the data sheet. Missing targets clearly shown as blank or N/A. No crashes, no corrupted values. Summary KPIs are still accurate based on actual revenue.
