# Eval Methodology

A skill that ensures fair, accurate, and comparable skill evaluations across models and versions.

## Key principles

1. **Separate generation from grading** — never show eval criteria during code generation
2. **Complete coverage** — compare versions only when they ran the same eval set
3. **Cost-aware ranking** — cheapest model wins ties
4. **Clean baselines** — baseline prompts must not contain the rubric

## Problems this skill prevents

| Problem | What goes wrong | How this skill fixes it |
|---------|----------------|----------------------|
| Criteria leakage | Model sees rubric, treats it as requirements → inflated baseline scores | Separate generation from grading |
| Partial coverage | v2 runs 4/7 evals, appears better than v1 | Dashboard flags missing evals |
| Cost-blind ranking | Opus gets ⭐ over Sonnet at same score | Cost tiebreaker in best markers |
| Self-grading bias | Models grade themselves generously | Separate grading agent/pass |

## What triggered this skill

During the Node.js security eval, baseline prompts included "SELF-EVALUATE against these 11 criteria" which listed every security feature to check. Haiku and Sonnet read the criteria and built code matching them — scoring 11/11 on baselines. Opus wrote code first and self-evaluated honestly, scoring 5/11. The criteria leakage made baselines unreliable.

## Usage triggers

- Running any eval (with-skill or baseline)
- Comparing skill versions
- Reviewing dashboard accuracy
- Planning a new eval run
