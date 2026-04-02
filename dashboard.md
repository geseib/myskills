# Skills Dashboard

*Last generated: 2026-04-02 14:00 UTC*

## Overview

| Skill | Status | Version | Rating | Evals | Skill Impact |
|-------|--------|---------|--------|-------|-------------|
| [dynamodb-single-table](#dynamodb-single-table) | `draft` | `v3` | █████████░ 98% | 9 | -1% |
| [nodejs-security](#nodejs-security) | `draft` | `v1` | █████████░ 96% | 9 | +18% |

## Skill Details

### Dynamodb Single Table

| | |
|---|---|
| **Status** | `draft` |
| **Version** | `v3` |
| **Last eval** | 2026-04-01 |
| **Eval cases** | 9 |
| **Rating** | █████████░ **98%** |
| **vs previous** | +4% |
| **vs baseline** | -1% (baseline=99%) |

**Version notes**

- `v1`: Initial skill with core patterns and examples
- `v2`: Added feed fanout, migration guidance, denormalization tradeoffs
- `v3`: Condensed for smaller models — rules over examples, removed verbose patterns

**Version history (per model)**

| Version | Model | Score | Rating | Evals | Best? |
|---------|-------|-------|--------|-------|-------|
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

**Skill impact: With Skill vs Without Skill (Baseline)**

*Baseline = same prompt, same model, no skill loaded. Shows whether the skill actually helps.*

| Model | With Skill | Without Skill | Skill Impact |
|-------|-----------|---------------|-------------|
| Haiku | 98% | 100% | -2% |
| Opus | 98% | 100% | -2% |
| Sonnet | 98% | 98% | = |

<details>
<summary>Per-eval baseline details</summary>

| Eval | Model | With Skill | Without Skill | Delta |
|------|-------|-----------|---------------|-------|
| adversarial-kitchen-sink | Haiku | 8/8 | 8/8 | = |
| happy-path-basic-app | Haiku | 11/11 | 11/11 | = |
| happy-path-multi-tenant | Haiku | 10.5/11 | 11/11 | -5% |
| adversarial-kitchen-sink | Opus | 8/8 | 8/8 | = |
| happy-path-basic-app | Opus | 11/11 | 11/11 | = |
| happy-path-multi-tenant | Opus | 10.5/11 | 11/11 | -5% |
| adversarial-kitchen-sink | Sonnet | 8/8 | 8/8 | = |
| happy-path-basic-app | Sonnet | 11/11 | 11/11 | = |
| happy-path-multi-tenant | Sonnet | 10.5/11 | 10.5/11 | = |

</details>

---

### Nodejs Security

| | |
|---|---|
| **Status** | `draft` |
| **Version** | `v1` |
| **Last eval** | 2026-04-02 |
| **Eval cases** | 9 |
| **Rating** | █████████░ **96%** |
| **vs baseline** | +18% (baseline=78%) |

**Version notes**

- `v1`: Initial skill covering OWASP Top 10, Zod validation, bcrypt, helmet, rate limiting

**Version history (per model)**

| Version | Model | Score | Rating | Evals | Best? |
|---------|-------|-------|--------|-------|-------|
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

**Skill impact: With Skill vs Without Skill (Baseline)**

*Baseline = same prompt, same model, no skill loaded. Shows whether the skill actually helps.*

| Model | With Skill | Without Skill | Skill Impact |
|-------|-----------|---------------|-------------|
| Haiku | 92% | 76% | +16% |
| Opus | 100% | 78% | +22% |
| Sonnet | 97% | 81% | +16% |

<details>
<summary>Per-eval baseline details</summary>

| Eval | Model | With Skill | Without Skill | Delta |
|------|-------|-----------|---------------|-------|
| adversarial-speed-vs-security | Haiku | 8/8 | 8/8 | = |
| edge-case-multitenancy | Haiku | 8/9 | 5/9 | +33% |
| edge-case-nosql-injection | Haiku | 8/8 | 8/8 | = |
| edge-case-ssr-xss | Haiku | 7/8 | 5/8 | +26% |
| edge-case-webhook-handler | Haiku | 7/9 | 5/9 | +22% |
| happy-path-auth-system | Haiku | 9/10 | 7/10 | +20% |
| happy-path-file-upload | Haiku | 8/9 | 6/9 | +22% |
| happy-path-rest-api | Haiku | 11/11 | 11/11 | = |
| adversarial-speed-vs-security | Opus | 8/8 | 8/8 | = |
| edge-case-multitenancy | Opus | 9/9 | 7/9 | +22% |
| edge-case-nosql-injection | Opus | 8/8 | 8/8 | = |
| edge-case-ssr-xss | Opus | 8/8 | 6/8 | +25% |
| edge-case-webhook-handler | Opus | 9/9 | 7/9 | +22% |
| happy-path-auth-system | Opus | 10/10 | 8/10 | +20% |
| happy-path-file-upload | Opus | 9/9 | 7/9 | +22% |
| happy-path-rest-api | Opus | 11/11 | 5/11 | +55% |
| adversarial-speed-vs-security | Sonnet | 8/8 | 8/8 | = |
| edge-case-multitenancy | Sonnet | 8/9 | 6/9 | +22% |
| edge-case-nosql-injection | Sonnet | 8/8 | 7.5/8 | +6% |
| edge-case-ssr-xss | Sonnet | 8/8 | 5/8 | +38% |
| edge-case-webhook-handler | Sonnet | 8/9 | 6/9 | +22% |
| happy-path-auth-system | Sonnet | 10/10 | 8/10 | +20% |
| happy-path-file-upload | Sonnet | 9/9 | 7/9 | +22% |
| happy-path-rest-api | Sonnet | 11/11 | 11/11 | = |

</details>

---

## How to read this dashboard

- **Rating** = percentage of eval criteria passed across all eval cases (all models combined)
- **Skill Impact** = does the skill help? Compares with-skill vs without-skill (baseline) on the same model and evals
- **Best for task** = cheapest model that achieves the highest score on each eval (score first, cost as tiebreaker)
- **Cross-model comparison** = how each model performs WITH the skill loaded
- **Version notes** = brief description of what changed in each version
- **vs Previous** = rating change from the prior skill version
- Regenerate with: `python3 scripts/generate-dashboard.py`
