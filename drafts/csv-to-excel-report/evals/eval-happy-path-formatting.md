<!-- eval-version: v1 -->
<!-- eval-notes: v1=Original criteria -->
# Eval: Professional formatting and styling

**Skill:** `csv-to-excel-report`
**Type:** happy-path

## Setup

Same two sample CSVs from `assets/`.

## Prompt

```
Generate the Excel report from these CSVs. I need it to look professional — proper formatting, colors, number formatting. It should be ready to email to my VP of Sales.
```

## Expected behavior

- [ ] Executive Summary has a header area with report title and date range
- [ ] KPI values are formatted as currency ($XXX,XXX.XX for revenue) and integers (units, reps)
- [ ] Regional table has borders on all cells
- [ ] Achievement percentages are formatted as "XX.X%" not raw decimals (e.g., 0.533...)
- [ ] Currency values show "$XX,XXX.XX" format, not plain numbers
- [ ] Data sheet has frozen header row (row 1 stays visible when scrolling)
- [ ] Data sheet has auto-filters enabled on all columns
- [ ] Alternating row colors applied on data sheet (e.g., gray/white)
- [ ] Column widths are reasonable (not default narrow columns)
- [ ] Header row has distinct styling (bold, colored background, contrasting text)
- [ ] No raw Python types visible in cells (no "nan", "None", "Timestamp(...)")

## Should NOT

- Should not leave default column widths (8.43 chars)
- Should not show unformatted decimals for currency (e.g., 9600.0 instead of $9,600.00)
- Should not leave NaN or None visible in any cell
- Should not use garish or clashing colors
- Should not skip the Executive Summary sheet (data-only reports aren't "VP-ready")

## Pass criteria

At least 9/11 formatting criteria met. File looks polished enough to share with a VP — styled headers, proper number formatting, filters enabled, no raw data artifacts.
