# Skills Dashboard

*Last generated: 2026-04-01 12:12 UTC*

## Overview

| Skill | Status | Version | Rating | Evals | vs Baseline |
|-------|--------|---------|--------|-------|-------------|
| [dynamodb-single-table](#dynamodb-single-table) | `draft` | `v1` | █████████░ 97% | 8 | -2% |

## Skill Details

### Dynamodb Single Table

| | |
|---|---|
| **Status** | `draft` |
| **Version** | `v1` |
| **Last eval** | 2026-04-01 |
| **Eval cases** | 8 |
| **Rating** | █████████░ **97%** |
| **vs baseline** | -2% (baseline=99%) |

**Version history**

| Version | Date | Score | Rating | Evals | Models |
|---------|------|-------|--------|-------|--------|
| `v1` | 2026-04-01 | 189.0/195.0 | █████████░ 97% | 21 | claude-haiku-4-5-20251001, claude-opus-4-6, claude-sonnet-4-6 |

**Eval results (current version)**

| Eval | Type | Score | Result |
|------|------|-------|--------|
| adversarial-kitchen-sink | adversarial | 8/8 | PASS |
| adversarial-kitchen-sink | adversarial | 8/8 | PASS |
| adversarial-kitchen-sink | adversarial | 5/8 | PARTIAL |
| edge-case-many-to-many | edge-case | 8/8 | PASS |
| edge-case-many-to-many | edge-case | 8/8 | PASS |
| edge-case-many-to-many | edge-case | 8/8 | PASS |
| edge-case-migration | edge-case | 9/9 | PASS |
| edge-case-migration | edge-case | 9/9 | PASS |
| edge-case-migration | edge-case | 6.5/9 | PARTIAL |
| edge-case-time-series | edge-case | 9/9 | PASS |
| edge-case-time-series | edge-case | 9/9 | PASS |
| edge-case-time-series | edge-case | 9/9 | PASS |
| happy-path-basic-app | happy-path | 11/11 | PASS |
| happy-path-basic-app | happy-path | 11/11 | PASS |
| happy-path-basic-app | happy-path | 11/11 | PASS |
| happy-path-multi-tenant | happy-path | 11/11 | PASS |
| happy-path-multi-tenant | happy-path | 11/11 | PASS |
| happy-path-multi-tenant | happy-path | 10.5/11 | PASS |
| happy-path-realtime | happy-path | 9/9 | PASS |
| happy-path-realtime | happy-path | 9/9 | PASS |
| happy-path-realtime | happy-path | 9/9 | PASS |
**Cross-model comparison (current version)**

| Eval | Haiku | Opus | Sonnet |
|------|-----|-----|-----|
| adversarial-kitchen-sink | 5/8 | 8/8 | 8/8 |
| edge-case-many-to-many | 8/8 | 8/8 | 8/8 |
| edge-case-migration | 6.5/9 | 9/9 | 9/9 |
| edge-case-time-series | 9/9 | 9/9 | 9/9 |
| happy-path-basic-app | 11/11 | 11/11 | 11/11 |
| happy-path-multi-tenant | 10.5/11 | 11/11 | 11/11 |
| happy-path-realtime | 9/9 | 9/9 | 9/9 |
| **Total** | **91%** | **100%** | **100%** |

**Baseline comparison (no skill loaded)**

| Eval | Model | With Skill | Baseline | Delta |
|------|-------|-----------|----------|-------|
| adversarial-kitchen-sink | Haiku | 5/8 | 8/8 | -38% |
| happy-path-basic-app | Haiku | 11/11 | 11/11 | = |
| happy-path-multi-tenant | Haiku | 10.5/11 | 11/11 | -5% |
| adversarial-kitchen-sink | Opus | 8/8 | 8/8 | = |
| happy-path-basic-app | Opus | 11/11 | 11/11 | = |
| happy-path-multi-tenant | Opus | 11/11 | 11/11 | = |
| adversarial-kitchen-sink | Sonnet | 8/8 | 8/8 | = |
| happy-path-basic-app | Sonnet | 11/11 | 11/11 | = |
| happy-path-multi-tenant | Sonnet | 11/11 | 10.5/11 | +5% |

---

## How to read this dashboard

- **Rating** = percentage of eval criteria passed across all eval cases
- **vs Baseline** = difference between skill-loaded and no-skill performance
- **vs Previous** = rating change from the prior skill version
- Regenerate with: `python3 scripts/generate-dashboard.py`
