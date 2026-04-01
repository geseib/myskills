# Skills Dashboard

*Last generated: 2026-04-01 12:25 UTC*

## Overview

| Skill | Status | Version | Rating | Evals | Skill Impact |
|-------|--------|---------|--------|-------|-------------|
| [dynamodb-single-table](#dynamodb-single-table) | `draft` | `v2` | █████████░ 93% | 8 | -6% |
| [nodejs-security](#nodejs-security) | `draft` | `v1` | ░░░░░░░░░░ 0% | 8 | — |

## Skill Details

### Dynamodb Single Table

| | |
|---|---|
| **Status** | `draft` |
| **Version** | `v2` |
| **Last eval** | 2026-04-01 |
| **Eval cases** | 8 |
| **Rating** | █████████░ **93%** |
| **vs previous** | -4% |
| **vs baseline** | -6% (baseline=99%) |

**Version history (per model)**

| Version | Model | Score | Rating | Evals | Best? |
|---------|-------|-------|--------|-------|-------|
| `v1` | Haiku | 59/65 | █████████░ 91% | 7 |  |
| `v1` | Opus | 65/65 | ██████████ 100% | 7 | ⭐ |
| `v1` | Sonnet | 65/65 | ██████████ 100% | 7 |  |
| `v2` | Haiku | 34.5/39 | ████████░░ 88% | 4 |  |
| `v2` | Opus | 8/8 | ██████████ 100% | 1 |  |
| `v2` | Sonnet | 17/17 | ██████████ 100% | 2 |  |

**Eval results (current version)**

| Eval | Type | Score | Result |
|------|------|-------|--------|
| adversarial-kitchen-sink | adversarial | 7/8 | PASS |
| adversarial-kitchen-sink | adversarial | 8/8 | PASS |
| adversarial-kitchen-sink | adversarial | 8/8 | PASS |
| edge-case-migration | edge-case | 8/9 | PARTIAL |
| edge-case-migration | edge-case | 9/9 | PASS |
| happy-path-basic-app | happy-path | 11/11 | PASS |
| happy-path-multi-tenant | happy-path | 8.5/11 | PARTIAL |
**Cross-model comparison (current version)**

| Eval | Haiku | Opus | Sonnet |
|------|-----|-----|-----|
| adversarial-kitchen-sink | 7/8 | 8/8 | 8/8 |
| edge-case-migration | 8/9 | — | 9/9 |
| happy-path-basic-app | 11/11 | — | — |
| happy-path-multi-tenant | 8.5/11 | — | — |
| **Total** | **88%** | **100%** | **100%** |

**Skill impact: With Skill vs Without Skill (Baseline)**

*Baseline = same prompt, same model, no skill loaded. Shows whether the skill actually helps.*

| Model | With Skill | Without Skill | Skill Impact |
|-------|-----------|---------------|-------------|
| Haiku | 88% | 100% | -12% |
| Opus | 100% | 100% | = |
| Sonnet | 100% | 100% | = |

<details>
<summary>Per-eval baseline details</summary>

| Eval | Model | With Skill | Without Skill | Delta |
|------|-------|-----------|---------------|-------|
| adversarial-kitchen-sink | Haiku | 7/8 | 8/8 | -12% |
| happy-path-basic-app | Haiku | 11/11 | 11/11 | = |
| happy-path-multi-tenant | Haiku | 8.5/11 | 11/11 | -23% |
| adversarial-kitchen-sink | Opus | 8/8 | 8/8 | = |
| happy-path-basic-app | Opus | — | 11/11 | — |
| happy-path-multi-tenant | Opus | — | 11/11 | — |
| adversarial-kitchen-sink | Sonnet | 8/8 | 8/8 | = |
| happy-path-basic-app | Sonnet | — | 11/11 | — |
| happy-path-multi-tenant | Sonnet | — | 10.5/11 | — |

</details>

---

### Nodejs Security

| | |
|---|---|
| **Status** | `draft` |
| **Version** | `v1` |
| **Last eval** | n/a |
| **Eval cases** | 8 |
| **Rating** | ░░░░░░░░░░ **0%** |

**Eval results (current version)**

| Eval | Type | Score | Result |
|------|------|-------|--------|

---

## How to read this dashboard

- **Rating** = percentage of eval criteria passed across all eval cases (all models combined)
- **Skill Impact** = does the skill help? Compares with-skill vs without-skill (baseline) on the same model and evals
- **Cross-model comparison** = how each model performs WITH the skill loaded
- **vs Previous** = rating change from the prior skill version
- Regenerate with: `python3 scripts/generate-dashboard.py`
