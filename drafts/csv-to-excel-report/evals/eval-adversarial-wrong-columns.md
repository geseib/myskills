<!-- eval-version: v1 -->
<!-- eval-notes: v1=Original criteria -->
# Eval: Wrong or missing CSV columns

**Skill:** `csv-to-excel-report`
**Type:** adversarial

## Setup

Provide two CSVs with intentional problems:
- `sales_data.csv` has "Revenue" (capital R) instead of "revenue", and "Date" instead of "date"
- `sales_targets.csv` is missing the "quarter" column entirely — it has "period" instead, and "target" instead of "target_revenue"

## Prompt

```
Generate my sales report from these two CSVs. Here are the files.
```

(Provide the malformed CSVs without mentioning the column issues.)

## Expected behavior

- [ ] Detects column name mismatches before attempting to process data
- [ ] Reports WHICH columns are missing vs. which are present
- [ ] Suggests corrections for close matches (e.g., "Revenue" → "revenue", "period" → "quarter")
- [ ] Does not crash with an unhelpful pandas KeyError or traceback
- [ ] Does not silently proceed with wrong columns (which would produce wrong results)
- [ ] Offers to fix the column names and proceed
- [ ] If fixing automatically, clearly states what was renamed
- [ ] Error message is user-friendly, not a raw Python exception

## Should NOT

- Should not crash with a raw traceback shown to the user
- Should not silently ignore wrong columns and produce a broken report
- Should not proceed without validating columns first
- Should not give up entirely without suggesting a fix
- Should not require the user to manually figure out which columns are wrong

## Pass criteria

Detects the column issues before processing. Reports them clearly with specific missing/found column names. Either fixes automatically with explanation or asks the user what to do. Does not produce a corrupt report.
