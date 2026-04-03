# Skills Dashboard

*Last generated: 2026-04-03 11:35 UTC*

## Overview

| Skill | Status | Version | Rating | Evals | Skill Impact |
|-------|--------|---------|--------|-------|-------------|
| [csv-to-excel-report](#csv-to-excel-report) | `draft` | `v1` | █████████░ 92% | 6 | +43% |
| [dynamodb-single-table](#dynamodb-single-table) | `draft` | `v3` | █████████░ 98% | 9 | +31% |
| [nodejs-security](#nodejs-security) | `draft` | `v1` | █████████░ 96% | 9 | +18% |

## Skill Details

### Csv To Excel Report

| | |
|---|---|
| **Status** | `draft` |
| **Version** | `v1` |
| **Last eval** | 2026-04-02 |
| **Eval cases** | 6 |
| **Rating** | █████████░ **92%** |
| **vs previous** | +43% |

**Version notes**

- `v1`: Initial skill with 7-step methodology, openpyxl styling, sample data

**Version history (per model)**

| Version | Model | Score | Rating | Evals | Best? |
|---------|-------|-------|--------|-------|-------|
| `baseline` | Haiku | 9/44 | ██░░░░░░░░ 20% | 5 |  |
| `baseline` | Opus | 33/44 | ███████░░░ 75% | 5 |  |
| `baseline` | Sonnet | 23/44 | █████░░░░░ 52% | 5 |  |
| `v1` | Haiku | 37/44 | ████████░░ 84% | 5 |  |
| `v1` | Opus | 43/44 | █████████░ 98% | 5 | ⭐ |
| `v1` | Sonnet | 42/44 | █████████░ 95% | 5 |  |

**Eval results (current version)**

| Eval | Model | Type | Score | Result |
|------|-------|------|-------|--------|
| adversarial-wrong-columns | Haiku | adversarial | 3/8 | FAIL |
| adversarial-wrong-columns | Sonnet | adversarial | 6/8 | PASS |
| adversarial-wrong-columns | Opus | adversarial | 7/8 | PASS |
| edge-case-large-dataset | Haiku | edge-case | 6/7 | PASS |
| edge-case-large-dataset | Sonnet | edge-case | 7/7 | PASS |
| edge-case-large-dataset | Opus | edge-case | 7/7 | PASS |
| edge-case-missing-targets | Haiku | edge-case | 7/8 | PASS |
| edge-case-missing-targets | Sonnet | edge-case | 8/8 | PASS |
| edge-case-missing-targets | Opus | edge-case | 8/8 | PASS |
| happy-path-basic | Haiku | happy-path | 10/10 | PASS |
| happy-path-basic | Sonnet | happy-path | 10/10 | PASS |
| happy-path-basic | Opus | happy-path | 10/10 | PASS |
| happy-path-formatting | Haiku | happy-path | 11/11 | PASS |
| happy-path-formatting | Sonnet | happy-path | 11/11 | PASS |
| happy-path-formatting | Opus | happy-path | 11/11 | PASS |

**Cross-model comparison (current version)**

| Eval | Haiku | Opus | Sonnet |
|------|-----|-----|-----|
| adversarial-wrong-columns | 3/8 | 7/8 | 6/8 |
| edge-case-large-dataset | 6/7 | 7/7 | 7/7 |
| edge-case-missing-targets | 7/8 | 8/8 | 8/8 |
| happy-path-basic | 10/10 | 10/10 | 10/10 |
| happy-path-formatting | 11/11 | 11/11 | 11/11 |
| **Total** | **84%** | **98%** | **95%** |

**Best for task** *(highest score, cheapest model as tiebreaker)*

| Eval | Best Model | Score | Why |
|------|-----------|-------|-----|
| adversarial-wrong-columns | **Opus** | 7/8 | Highest score at lowest cost |
| edge-case-large-dataset | **Sonnet** | 7/7 | Highest score at lowest cost |
| edge-case-missing-targets | **Sonnet** | 8/8 | Highest score at lowest cost |
| happy-path-basic | **Haiku** | 10/10 | All models score 100%; Haiku is cheapest |
| happy-path-formatting | **Haiku** | 11/11 | All models score 100%; Haiku is cheapest |


---

### Dynamodb Single Table

| | |
|---|---|
| **Status** | `draft` |
| **Version** | `v3` |
| **Last eval** | 2026-04-01 |
| **Eval cases** | 9 |
| **Rating** | █████████░ **98%** |
| **vs previous** | +4% |

**Version notes**

- `v1`: Initial skill with core patterns and examples
- `v2`: Added feed fanout, migration guidance, denormalization tradeoffs
- `v3`: Condensed for smaller models — rules over examples, removed verbose patterns

**Version history (per model)**

| Version | Model | Score | Rating | Evals | Best? |
|---------|-------|-------|--------|-------|-------|
| `baseline` | Haiku | 24/65 | ███░░░░░░░ 37% | 7 |  |
| `baseline` | Opus | 30/30 | ██████████ 100% | 3 |  |
| `baseline` | Sonnet | 29.5/30 | █████████░ 98% | 3 |  |
| `v1` | Haiku | 59/65 | █████████░ 91% | 7 |  |
| `v1` | Opus | 65/65 | ██████████ 100% | 7 |  |
| `v1` | Sonnet | 65/65 | ██████████ 100% | 7 | ⭐ |
| `v2` | Haiku | 58.5/65 | █████████░ 90% | 7 |  |
| `v2` | Opus | 65/65 | ██████████ 100% | 7 |  |
| `v2` | Sonnet | 60.5/65 | █████████░ 93% | 7 |  |
| `v3` | Haiku | 64.5/65 | █████████░ 99% | 7 |  |
| `v3` | Opus | 63.5/65 | █████████░ 98% | 7 |  |
| `v3` | Sonnet | 64/65 | █████████░ 98% | 7 |  |

**Eval results (current version)**

| Eval | Model | Type | Score | Result |
|------|-------|------|-------|--------|
| adversarial-kitchen-sink | Haiku | adversarial | 8/8 | PASS |
| adversarial-kitchen-sink | Sonnet | adversarial | 8/8 | PASS |
| adversarial-kitchen-sink | Opus | adversarial | 8/8 | PASS |
| edge-case-many-to-many | Haiku | edge-case | 8/8 | PASS |
| edge-case-many-to-many | Sonnet | edge-case | 8/8 | PASS |
| edge-case-many-to-many | Opus | edge-case | 7.5/8 | PASS |
| edge-case-migration | Haiku | edge-case | 9/9 | PASS |
| edge-case-migration | Sonnet | edge-case | 8.5/9 | PASS |
| edge-case-migration | Opus | edge-case | 8.5/9 | PASS |
| edge-case-time-series | Haiku | edge-case | 9/9 | PASS |
| edge-case-time-series | Sonnet | edge-case | 9/9 | PASS |
| edge-case-time-series | Opus | edge-case | 9/9 | PASS |
| happy-path-basic-app | Haiku | happy-path | 11/11 | PASS |
| happy-path-basic-app | Sonnet | happy-path | 11/11 | PASS |
| happy-path-basic-app | Opus | happy-path | 11/11 | PASS |
| happy-path-multi-tenant | Haiku | happy-path | 10.5/11 | PASS |
| happy-path-multi-tenant | Sonnet | happy-path | 10.5/11 | PASS |
| happy-path-multi-tenant | Opus | happy-path | 10.5/11 | PASS |
| happy-path-realtime | Haiku | happy-path | 9/9 | PASS |
| happy-path-realtime | Sonnet | happy-path | 9/9 | PASS |
| happy-path-realtime | Opus | happy-path | 9/9 | PASS |

**Cross-model comparison (current version)**

| Eval | Haiku | Opus | Sonnet |
|------|-----|-----|-----|
| adversarial-kitchen-sink | 8/8 | 8/8 | 8/8 |
| edge-case-many-to-many | 8/8 | 7.5/8 | 8/8 |
| edge-case-migration | 9/9 | 8.5/9 | 8.5/9 |
| edge-case-time-series | 9/9 | 9/9 | 9/9 |
| happy-path-basic-app | 11/11 | 11/11 | 11/11 |
| happy-path-multi-tenant | 10.5/11 | 10.5/11 | 10.5/11 |
| happy-path-realtime | 9/9 | 9/9 | 9/9 |
| **Total** | **99%** | **98%** | **98%** |

**Best for task** *(highest score, cheapest model as tiebreaker)*

| Eval | Best Model | Score | Why |
|------|-----------|-------|-----|
| adversarial-kitchen-sink | **Haiku** | 8/8 | All models score 100%; Haiku is cheapest |
| edge-case-many-to-many | **Haiku** | 8/8 | Highest score at lowest cost |
| edge-case-migration | **Haiku** | 9/9 | Highest score at lowest cost |
| edge-case-time-series | **Haiku** | 9/9 | All models score 100%; Haiku is cheapest |
| happy-path-basic-app | **Haiku** | 11/11 | All models score 100%; Haiku is cheapest |
| happy-path-multi-tenant | **Haiku** | 10.5/11 | Highest score at lowest cost |
| happy-path-realtime | **Haiku** | 9/9 | All models score 100%; Haiku is cheapest |


---

### Nodejs Security

| | |
|---|---|
| **Status** | `draft` |
| **Version** | `v1` |
| **Last eval** | 2026-04-02 |
| **Eval cases** | 9 |
| **Rating** | █████████░ **96%** |
| **vs previous** | +18% |

**Version notes**

- `v1`: Initial skill covering OWASP Top 10, Zod validation, bcrypt, helmet, rate limiting

**Version history (per model)**

| Version | Model | Score | Rating | Evals | Best? |
|---------|-------|-------|--------|-------|-------|
| `baseline` | Haiku | 55/72 | ███████░░░ 76% | 8 |  |
| `baseline` | Opus | 56/72 | ███████░░░ 78% | 8 |  |
| `baseline` | Sonnet | 58.5/72 | ████████░░ 81% | 8 |  |
| `v1` | Haiku | 66/72 | █████████░ 92% | 8 |  |
| `v1` | Opus | 72/72 | ██████████ 100% | 8 | ⭐ |
| `v1` | Sonnet | 70/72 | █████████░ 97% | 8 |  |

**Eval results (current version)**

| Eval | Model | Type | Score | Result |
|------|-------|------|-------|--------|
| adversarial-speed-vs-security | Haiku | adversarial | 8/8 | PASS |
| adversarial-speed-vs-security | Sonnet | adversarial | 8/8 | PASS |
| adversarial-speed-vs-security | Opus | adversarial | 8/8 | PASS |
| edge-case-multitenancy | Haiku | edge-case | 8/9 | PASS |
| edge-case-multitenancy | Sonnet | edge-case | 8/9 | PASS |
| edge-case-multitenancy | Opus | edge-case | 9/9 | PASS |
| edge-case-nosql-injection | Haiku | edge-case | 8/8 | PASS |
| edge-case-nosql-injection | Sonnet | edge-case | 8/8 | PASS |
| edge-case-nosql-injection | Opus | edge-case | 8/8 | PASS |
| edge-case-ssr-xss | Haiku | edge-case | 7/8 | PASS |
| edge-case-ssr-xss | Sonnet | edge-case | 8/8 | PASS |
| edge-case-ssr-xss | Opus | edge-case | 8/8 | PASS |
| edge-case-webhook-handler | Haiku | edge-case | 7/9 | PASS |
| edge-case-webhook-handler | Sonnet | edge-case | 8/9 | PASS |
| edge-case-webhook-handler | Opus | edge-case | 9/9 | PASS |
| happy-path-auth-system | Haiku | happy-path | 9/10 | PASS |
| happy-path-auth-system | Sonnet | happy-path | 10/10 | PASS |
| happy-path-auth-system | Opus | happy-path | 10/10 | PASS |
| happy-path-file-upload | Haiku | happy-path | 8/9 | PASS |
| happy-path-file-upload | Sonnet | happy-path | 9/9 | PASS |
| happy-path-file-upload | Opus | happy-path | 9/9 | PASS |
| happy-path-rest-api | Haiku | happy-path | 11/11 | PASS |
| happy-path-rest-api | Sonnet | happy-path | 11/11 | PASS |
| happy-path-rest-api | Opus | happy-path | 11/11 | PASS |

**Cross-model comparison (current version)**

| Eval | Haiku | Opus | Sonnet |
|------|-----|-----|-----|
| adversarial-speed-vs-security | 8/8 | 8/8 | 8/8 |
| edge-case-multitenancy | 8/9 | 9/9 | 8/9 |
| edge-case-nosql-injection | 8/8 | 8/8 | 8/8 |
| edge-case-ssr-xss | 7/8 | 8/8 | 8/8 |
| edge-case-webhook-handler | 7/9 | 9/9 | 8/9 |
| happy-path-auth-system | 9/10 | 10/10 | 10/10 |
| happy-path-file-upload | 8/9 | 9/9 | 9/9 |
| happy-path-rest-api | 11/11 | 11/11 | 11/11 |
| **Total** | **92%** | **100%** | **97%** |

**Best for task** *(highest score, cheapest model as tiebreaker)*

| Eval | Best Model | Score | Why |
|------|-----------|-------|-----|
| adversarial-speed-vs-security | **Haiku** | 8/8 | All models score 100%; Haiku is cheapest |
| edge-case-multitenancy | **Opus** | 9/9 | Highest score at lowest cost |
| edge-case-nosql-injection | **Haiku** | 8/8 | All models score 100%; Haiku is cheapest |
| edge-case-ssr-xss | **Sonnet** | 8/8 | Highest score at lowest cost |
| edge-case-webhook-handler | **Opus** | 9/9 | Highest score at lowest cost |
| happy-path-auth-system | **Sonnet** | 10/10 | Highest score at lowest cost |
| happy-path-file-upload | **Sonnet** | 9/9 | Highest score at lowest cost |
| happy-path-rest-api | **Haiku** | 11/11 | All models score 100%; Haiku is cheapest |


---

## How to read this dashboard

- **Rating** = percentage of eval criteria passed across all eval cases (all models combined)
- **Skill Impact** = difference between current version rating and baseline rating in the overview
- **Version history** = `baseline` rows show model performance WITHOUT the skill; version rows show WITH the skill. Compare to see skill impact
- **Best for task** = cheapest model that achieves the highest score on each eval (score first, cost as tiebreaker)
- **Cross-model comparison** = how each model performs WITH the skill loaded
- **Version notes** = brief description of what changed in each version
- **vs Previous** = rating change from the prior skill version
- Regenerate with: `python3 scripts/generate-dashboard.py`
