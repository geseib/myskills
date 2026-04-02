<!-- eval-version: v1 -->
<!-- eval-notes: v1=Original criteria -->
# Eval: Large dataset performance

**Skill:** `csv-to-excel-report`
**Type:** edge-case

## Setup

Describe a 10,000-row sales dataset with 50 reps across 8 regions, same column schema. Do not provide the actual CSV — the model should handle the scale in its implementation.

## Prompt

```
I have a large sales dataset — about 10,000 transactions across 50 reps and 8 regions. Same format as our standard sales data (date, region, sales_rep, product_category, units_sold, unit_price, revenue). Targets file has 50 reps × 4 quarters = 200 rows. Generate the Excel report. It needs to handle this volume without being slow.
```

## Expected behavior

- [ ] Script handles the volume without memory issues or crashes
- [ ] Uses pandas vectorized operations, not row-by-row Python loops for calculations
- [ ] Excel file is generated in reasonable time (acknowledges or handles performance)
- [ ] Auto-filters still work on the 10K-row dataset
- [ ] Column width calculation does not iterate every cell individually (uses header length or samples)
- [ ] Regional summary aggregation uses groupby, not manual loops
- [ ] Top 5 performers correctly ranks from 50 reps

## Should NOT

- Should not iterate row-by-row in Python loops for metric calculations
- Should not try to style 10K rows one cell at a time in a slow loop
- Should not crash on memory with 10K rows
- Should not use `iterrows()` for calculations (slow for large DataFrames)

## Pass criteria

Implementation uses vectorized pandas operations for calculations. Excel generation approach is scalable. Script would complete in reasonable time on 10K rows. Auto-filters and frozen panes still function correctly.
