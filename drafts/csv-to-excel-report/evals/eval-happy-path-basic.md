<!-- eval-version: v1 -->
<!-- eval-notes: v1=Original criteria -->
# Eval: Basic report generation

**Skill:** `csv-to-excel-report`
**Type:** happy-path

## Setup

Provide the two sample CSVs from `assets/sample_sales_data.csv` (50 rows) and `assets/sample_sales_targets.csv` (80 rows).

## Prompt

```
I have two CSV files: sales_data.csv with our transaction data (date, region, sales rep, product category, units sold, unit price, revenue) and sales_targets.csv with quarterly targets (region, sales rep, quarter, target revenue). Generate a polished Excel report that merges them and shows how each region and rep performed against their targets.
```

## Expected behavior

- [ ] Validates both CSVs have required columns before processing
- [ ] Derives quarter from date column correctly (e.g., 2024-01-12 → "2024-Q1")
- [ ] Left-joins sales onto targets on (region, sales_rep, quarter)
- [ ] Calculates achievement_pct and variance columns
- [ ] Creates "Executive Summary" sheet with KPIs (total revenue, units, deal size, reps)
- [ ] Creates "Sales Data" sheet with merged data (all 50 rows present)
- [ ] Output is a valid .xlsx file that opens without errors
- [ ] Row count on data sheet matches expected merged count (50)
- [ ] Installs or imports openpyxl before attempting Excel operations
- [ ] Prints summary stats (row count, file path) to stdout

## Should NOT

- Should not use xlsxwriter instead of openpyxl
- Should not skip CSV column validation
- Should not hardcode date ranges (must derive from data)
- Should not crash or produce corrupt output on the sample data
- Should not use inner join (which would drop rows)

## Pass criteria

Both sheets present with correct data. KPIs match manual calculation ($453,600 total revenue, 20 reps, 50 transactions). File opens in Excel without errors. All 50 sales rows appear in the data sheet.
