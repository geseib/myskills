# Skills Dashboard

*Last generated: 2026-04-01 12:03 UTC*

## Overview

| Skill | Status | Version | Rating | Evals | vs Baseline |
|-------|--------|---------|--------|-------|-------------|
| [dynamodb-single-table](#dynamodb-single-table) | `draft` | `v1` | ██████████ 100% | 8 | = |

## Skill Details

### Dynamodb Single Table

| | |
|---|---|
| **Status** | `draft` |
| **Version** | `v1` |
| **Last eval** | 2026-04-01 |
| **Eval cases** | 8 |
| **Rating** | ██████████ **100%** |
| **vs baseline** | 0% (baseline=100%) |

**Version history**

| Version | Date | Score | Rating | Evals | Models |
|---------|------|-------|--------|-------|--------|
| `v1` | 2026-04-01 | 65/65 | ██████████ 100% | 7 | claude-opus-4-6 |

**Eval results (current version)**

| Eval | Type | Score | Result |
|------|------|-------|--------|
| adversarial-kitchen-sink | adversarial | 8/8 | PASS |
| edge-case-many-to-many | edge-case | 8/8 | PASS |
| edge-case-migration | edge-case | 9/9 | PASS |
| edge-case-time-series | edge-case | 9/9 | PASS |
| happy-path-basic-app | happy-path | 11/11 | PASS |
| happy-path-multi-tenant | happy-path | 11/11 | PASS |
| happy-path-realtime | happy-path | 9/9 | PASS |

**Baseline comparison (no skill loaded)**

| Eval | With Skill | Baseline | Delta |
|------|-----------|----------|-------|
| adversarial-kitchen-sink | 8/8 | 8/8 | = |
| edge-case-many-to-many | 8/8 | — | — |
| edge-case-migration | 9/9 | — | — |
| edge-case-time-series | 9/9 | — | — |
| happy-path-basic-app | 11/11 | 11/11 | = |
| happy-path-multi-tenant | 11/11 | 11/11 | = |
| happy-path-realtime | 9/9 | — | — |

---

## How to read this dashboard

- **Rating** = percentage of eval criteria passed across all eval cases
- **vs Baseline** = difference between skill-loaded and no-skill performance
- **vs Previous** = rating change from the prior skill version
- Regenerate with: `python3 scripts/generate-dashboard.py`
