# eval-methodology

Fair, reproducible skill evaluations across models and versions.

## What it does

Enforces a rigorous eval protocol that separates generation from grading, requires complete coverage across versions and models, and uses cost-aware tiebreaking when scores are equal.

## Key principles

- **Separate generation from grading** — the model never sees eval criteria during generation, preventing score inflation
- **Complete coverage** — version comparisons require the same eval set on the same models
- **Cost-aware tiebreaking** — when models score equally, the cheaper model wins (Haiku < Sonnet < Opus)
- **Baseline comparison** — measure skill impact by comparing with-skill vs without-skill on the same prompts

## When it triggers

- Running evals for any skill
- Comparing results across skill versions or models
- Someone asks to "eval", "test", or "benchmark" a skill

## Works well with

- [eval-rebase](../eval-rebase) — eval versioning and consistency enforcement
- [dashboard-management](../dashboard-management) — auto-generated dashboard from results

## Source

Developed in [myskills](https://github.com/geseib/myskills) through iterative testing of the DynamoDB single-table and Node.js security skills across Haiku, Sonnet, and Opus.
