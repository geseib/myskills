#!/usr/bin/env python3
"""
Generate dashboard.md from eval-results/ JSONL data.

Usage: python3 scripts/generate-dashboard.py
"""

import json
import os
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
EVAL_RESULTS_DIR = REPO_ROOT / "eval-results"
DRAFTS_DIR = REPO_ROOT / "drafts"
SKILLS_DIR = REPO_ROOT / "skills"
DASHBOARD_PATH = REPO_ROOT / "dashboard.md"


def _short_model(model_name):
    """Shorten model name for display."""
    if "opus" in model_name:
        return "Opus"
    if "sonnet" in model_name:
        return "Sonnet"
    if "haiku" in model_name:
        return "Haiku"
    return model_name


def parse_score(score_str):
    """Parse '9/11' or '6.5/9' into (9, 11) and return as floats."""
    try:
        num, denom = score_str.split("/")
        return float(num), float(denom)
    except (ValueError, AttributeError):
        return 0, 0


def get_skill_version(skill_name):
    """Read skill version from skill.md frontmatter."""
    for base in [DRAFTS_DIR, SKILLS_DIR]:
        skill_file = base / skill_name / "skill.md"
        if skill_file.exists():
            content = skill_file.read_text()
            match = re.search(r"skill-version:\s*(v[\w.]+)", content)
            if match:
                return match.group(1)
    return "unknown"


def get_version_notes(skill_name):
    """Read version notes from skill.md frontmatter.

    Format: <!-- version-notes: v1=Short desc; v2=Short desc -->
    Returns dict like {"v1": "Short desc", "v2": "Short desc"}
    """
    for base in [DRAFTS_DIR, SKILLS_DIR]:
        skill_file = base / skill_name / "skill.md"
        if skill_file.exists():
            content = skill_file.read_text()
            match = re.search(r"version-notes:\s*(.+?)-->", content)
            if match:
                notes_str = match.group(1).strip()
                notes = {}
                for part in notes_str.split(";"):
                    part = part.strip()
                    if "=" in part:
                        ver, desc = part.split("=", 1)
                        notes[ver.strip()] = desc.strip()
                return notes
    return {}


# Model cost tiers (lower = cheaper). Used for "Best for task" ranking.
MODEL_COST_TIER = {
    "haiku": 1,
    "sonnet": 2,
    "opus": 3,
}


def _model_cost(model_name):
    """Return cost tier for a model (lower = cheaper)."""
    short = _short_model(model_name).lower()
    return MODEL_COST_TIER.get(short, 99)


def get_skill_location(skill_name):
    """Check if skill is in drafts/ or skills/."""
    if (SKILLS_DIR / skill_name / "skill.md").exists():
        return "skills"
    if (DRAFTS_DIR / skill_name / "skill.md").exists():
        return "drafts"
    return "unknown"


def count_evals(skill_name):
    """Count eval case files for a skill."""
    count = 0
    for base in [DRAFTS_DIR, SKILLS_DIR]:
        eval_dir = base / skill_name / "evals"
        if eval_dir.exists():
            count = len(list(eval_dir.glob("eval-*.md")))
    return count


def load_results(skill_name):
    """Load all results from a skill's results.jsonl."""
    results_file = EVAL_RESULTS_DIR / skill_name / "results.jsonl"
    if not results_file.exists():
        return []
    results = []
    for line in results_file.read_text().strip().split("\n"):
        if line.strip():
            results.append(json.loads(line))
    return results


def generate_skill_section(skill_name, results):
    """Generate dashboard section for one skill."""
    version = get_skill_version(skill_name)
    location = get_skill_location(skill_name)
    num_evals = count_evals(skill_name)

    # Separate with-skill and baseline results
    skill_results = [r for r in results if r.get("with_skill", True)]
    baseline_results = [r for r in results if not r.get("with_skill", True)]

    # Group by version
    by_version = defaultdict(list)
    for r in skill_results:
        by_version[r.get("skill_version", "unknown")].append(r)

    # Calculate per-version scores
    version_scores = {}
    for ver, ver_results in sorted(by_version.items()):
        total_num = sum(parse_score(r["score"])[0] for r in ver_results)
        total_denom = sum(parse_score(r["score"])[1] for r in ver_results)
        pct = round(total_num / total_denom * 100) if total_denom > 0 else 0
        pass_count = sum(1 for r in ver_results if r["overall"] == "pass")
        fail_count = sum(1 for r in ver_results if r["overall"] == "fail")
        partial_count = sum(1 for r in ver_results if r["overall"] == "partial")
        models = set(r.get("model", "unknown") for r in ver_results)
        dates = [r.get("run_id", "")[:10] for r in ver_results]
        latest_date = max(dates) if dates else "n/a"
        version_scores[ver] = {
            "pct": pct,
            "total_num": total_num,
            "total_denom": total_denom,
            "pass": pass_count,
            "fail": fail_count,
            "partial": partial_count,
            "count": len(ver_results),
            "models": models,
            "date": latest_date,
        }

    # Calculate baseline score
    baseline_pct = None
    if baseline_results:
        bl_num = sum(parse_score(r["score"])[0] for r in baseline_results)
        bl_denom = sum(parse_score(r["score"])[1] for r in baseline_results)
        baseline_pct = round(bl_num / bl_denom * 100) if bl_denom > 0 else 0

    # Current version info
    current = version_scores.get(version, {})
    current_pct = current.get("pct", 0)

    # Calculate delta from previous version
    sorted_versions = sorted(version_scores.keys())
    delta = None
    if len(sorted_versions) >= 2 and version in sorted_versions:
        idx = sorted_versions.index(version)
        if idx > 0:
            prev_ver = sorted_versions[idx - 1]
            delta = current_pct - version_scores[prev_ver]["pct"]

    # Build rating bar
    filled = current_pct // 10
    bar = "█" * filled + "░" * (10 - filled)

    # Status emoji based on location
    status = "draft" if location == "drafts" else "production"

    lines = []
    display_name = skill_name.replace("-", " ").title()

    # Header row
    lines.append(f"### {display_name}")
    lines.append("")
    lines.append(f"| | |")
    lines.append(f"|---|---|")
    lines.append(f"| **Status** | `{status}` |")
    lines.append(f"| **Version** | `{version}` |")
    lines.append(f"| **Last eval** | {current.get('date', 'n/a')} |")
    lines.append(f"| **Eval cases** | {num_evals} |")
    lines.append(f"| **Rating** | {bar} **{current_pct}%** |")

    if delta is not None:
        arrow = "+" if delta > 0 else ""
        lines.append(f"| **vs previous** | {arrow}{delta}% |")

    # Check if current version has incomplete eval coverage vs previous
    sorted_versions = sorted(version_scores.keys())
    if len(sorted_versions) >= 2 and version in sorted_versions:
        idx = sorted_versions.index(version)
        if idx > 0:
            prev_ver = sorted_versions[idx - 1]
            prev_evals = set(r["eval_id"] for r in by_version[prev_ver])
            curr_evals = set(r["eval_id"] for r in by_version[version])
            missing = prev_evals - curr_evals
            if missing:
                lines.append(
                    f"| **Coverage** | ⚠️ Missing {len(missing)} eval(s) vs `{prev_ver}`: {', '.join(sorted(missing))} |"
                )

    if baseline_pct is not None:
        diff = current_pct - baseline_pct
        arrow = "+" if diff > 0 else ""
        lines.append(f"| **vs baseline** | {arrow}{diff}% (baseline={baseline_pct}%) |")

    lines.append("")

    # Version notes
    vnotes = get_version_notes(skill_name)
    if vnotes:
        lines.append("**Version notes**")
        lines.append("")
        for ver in sorted(vnotes.keys()):
            lines.append(f"- `{ver}`: {vnotes[ver]}")
        lines.append("")

    # Version history — per model per version
    if version_scores:
        lines.append("**Version history (per model)**")
        lines.append("")
        lines.append("| Version | Model | Score | Rating | Evals | Best? |")
        lines.append("|---------|-------|-------|--------|-------|-------|")

        # Calculate per-version per-model scores
        best_overall_pct = 0
        best_overall_cost = 999
        best_overall_key = None
        version_model_scores = {}

        for ver in sorted(by_version.keys()):
            if ver == "baseline":
                continue
            ver_results = by_version[ver]
            models_in_ver = sorted(set(r.get("model", "unknown") for r in ver_results))

            for model in models_in_ver:
                model_results = [r for r in ver_results if r.get("model") == model]
                m_num = sum(parse_score(r["score"])[0] for r in model_results)
                m_den = sum(parse_score(r["score"])[1] for r in model_results)
                m_pct = round(m_num / m_den * 100) if m_den > 0 else 0
                version_model_scores[(ver, model)] = m_pct

                cost = _model_cost(model)
                if m_pct > best_overall_pct or (m_pct == best_overall_pct and cost < best_overall_cost):
                    best_overall_pct = m_pct
                    best_overall_cost = cost
                    best_overall_key = (ver, model)

        # Find best version per model and best model per version
        for ver in sorted(by_version.keys()):
            if ver == "baseline":
                continue
            ver_results = by_version[ver]
            models_in_ver = sorted(set(r.get("model", "unknown") for r in ver_results))
            dates = [r.get("run_id", "")[:10] for r in ver_results]
            latest_date = max(dates) if dates else "n/a"

            for model in models_in_ver:
                model_results = [r for r in ver_results if r.get("model") == model]
                m_num = sum(parse_score(r["score"])[0] for r in model_results)
                m_den = sum(parse_score(r["score"])[1] for r in model_results)
                m_pct = round(m_num / m_den * 100) if m_den > 0 else 0
                m_bar = "█" * (m_pct // 10) + "░" * (10 - m_pct // 10)
                tn = int(m_num) if m_num == int(m_num) else m_num
                td = int(m_den) if m_den == int(m_den) else m_den

                is_best = (ver, model) == best_overall_key
                best_str = "⭐" if is_best else ""

                lines.append(
                    f"| `{ver}` | {_short_model(model)} | {tn}/{td} | {m_bar} {m_pct}% | {len(model_results)} | {best_str} |"
                )

        lines.append("")

    # Individual eval results
    lines.append("**Eval results (current version)**")
    lines.append("")
    lines.append("| Eval | Type | Score | Result |")
    lines.append("|------|------|-------|--------|")

    current_results = by_version.get(version, [])
    for r in sorted(current_results, key=lambda x: x["eval_id"]):
        eval_id = r["eval_id"]
        # Infer type from eval_id
        if "happy-path" in eval_id:
            eval_type = "happy-path"
        elif "edge-case" in eval_id:
            eval_type = "edge-case"
        elif "adversarial" in eval_id:
            eval_type = "adversarial"
        elif "regression" in eval_id:
            eval_type = "regression"
        else:
            eval_type = "—"

        result_icon = {"pass": "PASS", "partial": "PARTIAL", "fail": "FAIL"}.get(
            r["overall"], "?"
        )
        lines.append(f"| {eval_id} | {eval_type} | {r['score']} | {result_icon} |")

    # Per-model breakdown
    all_models = sorted(set(r.get("model", "unknown") for r in results))
    if len(all_models) > 1:
        lines.append("**Cross-model comparison (current version)**")
        lines.append("")
        model_headers = " | ".join(f"{_short_model(m)}" for m in all_models)
        lines.append(f"| Eval | {model_headers} |")
        lines.append(f"|------|{'|'.join('-----' for _ in all_models)}|")

        all_eval_ids = sorted(set(r["eval_id"] for r in current_results))
        for eval_id in all_eval_ids:
            cells = []
            for model in all_models:
                match = [r for r in current_results if r["eval_id"] == eval_id and r.get("model") == model]
                if match:
                    cells.append(match[0]["score"])
                else:
                    cells.append("—")
            lines.append(f"| {eval_id} | {' | '.join(cells)} |")

        # Model totals row
        cells = []
        for model in all_models:
            model_results = [r for r in current_results if r.get("model") == model]
            if model_results:
                t_num = sum(parse_score(r["score"])[0] for r in model_results)
                t_den = sum(parse_score(r["score"])[1] for r in model_results)
                t_pct = round(t_num / t_den * 100) if t_den else 0
                cells.append(f"**{t_pct}%**")
            else:
                cells.append("—")
        lines.append(f"| **Total** | {' | '.join(cells)} |")
        lines.append("")

    # Best for task — cheapest model that scores highest per eval
    if len(all_models) > 1 and current_results:
        lines.append("**Best for task** *(highest score, cheapest model as tiebreaker)*")
        lines.append("")
        lines.append("| Eval | Best Model | Score | Why |")
        lines.append("|------|-----------|-------|-----|")

        all_eval_ids = sorted(set(r["eval_id"] for r in current_results))
        for eval_id in all_eval_ids:
            eval_results = [r for r in current_results if r["eval_id"] == eval_id]
            # Score each model: (pct, -cost_tier) so higher pct wins, then cheaper wins
            best = None
            best_pct = -1
            best_cost = 999
            best_score_str = ""
            for r in eval_results:
                n, d = parse_score(r["score"])
                pct = round(n / d * 100) if d else 0
                cost = _model_cost(r.get("model", ""))
                if pct > best_pct or (pct == best_pct and cost < best_cost):
                    best = r
                    best_pct = pct
                    best_cost = cost
                    best_score_str = r["score"]
            if best:
                short = _short_model(best.get("model", ""))
                if best_pct == 100:
                    why = f"All models score 100%; {short} is cheapest"
                    # Check if all models scored 100%
                    all_perfect = all(
                        round(parse_score(r["score"])[0] / parse_score(r["score"])[1] * 100) == 100
                        for r in eval_results if parse_score(r["score"])[1] > 0
                    )
                    if not all_perfect:
                        why = f"Highest score at lowest cost"
                else:
                    why = f"Highest score at lowest cost"
                lines.append(f"| {eval_id} | **{short}** | {best_score_str} | {why} |")

        lines.append("")

    # Skill Impact — does the skill help?
    if baseline_results:
        lines.append("**Skill impact: With Skill vs Without Skill (Baseline)**")
        lines.append("")
        lines.append("*Baseline = same prompt, same model, no skill loaded. Shows whether the skill actually helps.*")
        lines.append("")

        if len(all_models) > 1:
            # Summary table: one row per model showing overall with/without
            lines.append("| Model | With Skill | Without Skill | Skill Impact |")
            lines.append("|-------|-----------|---------------|-------------|")

            for model in all_models:
                model_baseline = [r for r in baseline_results if r.get("model") == model]
                model_skill = [r for r in current_results if r.get("model") == model]

                if model_baseline:
                    # Only compare evals that have both skill and baseline
                    bl_by_eval = {r["eval_id"]: r for r in model_baseline}
                    sk_num = sk_den = bl_num = bl_den = 0
                    for eval_id, bl in bl_by_eval.items():
                        sk_match = [r for r in model_skill if r["eval_id"] == eval_id]
                        if sk_match:
                            sn, sd = parse_score(sk_match[0]["score"])
                            bn, bd = parse_score(bl["score"])
                            sk_num += sn; sk_den += sd
                            bl_num += bn; bl_den += bd

                    sk_pct = round(sk_num / sk_den * 100) if sk_den else 0
                    bl_pct = round(bl_num / bl_den * 100) if bl_den else 0
                    diff = sk_pct - bl_pct
                    arrow = "+" if diff > 0 else ""
                    impact = f"{arrow}{diff}%" if diff != 0 else "="
                    lines.append(f"| {_short_model(model)} | {sk_pct}% | {bl_pct}% | {impact} |")
                else:
                    lines.append(f"| {_short_model(model)} | — | — | — |")

            lines.append("")

            # Detailed breakdown
            lines.append("<details>")
            lines.append("<summary>Per-eval baseline details</summary>")
            lines.append("")
            lines.append("| Eval | Model | With Skill | Without Skill | Delta |")
            lines.append("|------|-------|-----------|---------------|-------|")

            for model in all_models:
                model_baseline = [r for r in baseline_results if r.get("model") == model]
                model_skill = [r for r in current_results if r.get("model") == model]
                bl_by_eval = {r["eval_id"]: r for r in model_baseline}
                sk_by_eval = {r["eval_id"]: r for r in model_skill}

                for eval_id in sorted(bl_by_eval.keys()):
                    sk = sk_by_eval.get(eval_id)
                    bl = bl_by_eval.get(eval_id)
                    sk_score = sk["score"] if sk else "—"
                    bl_score = bl["score"] if bl else "—"

                    if sk and bl:
                        sk_n, sk_d = parse_score(sk["score"])
                        bl_n, bl_d = parse_score(bl["score"])
                        sk_pct = round(sk_n / sk_d * 100) if sk_d else 0
                        bl_pct = round(bl_n / bl_d * 100) if bl_d else 0
                        diff = sk_pct - bl_pct
                        arrow = "+" if diff > 0 else ""
                        delta_str = f"{arrow}{diff}%" if diff != 0 else "="
                    else:
                        delta_str = "—"

                    lines.append(f"| {eval_id} | {_short_model(model)} | {sk_score} | {bl_score} | {delta_str} |")

            lines.append("")
            lines.append("</details>")
        else:
            lines.append("| Eval | With Skill | Without Skill | Delta |")
            lines.append("|------|-----------|---------------|-------|")

            baseline_by_eval = {r["eval_id"]: r for r in baseline_results}
            skill_by_eval = {r["eval_id"]: r for r in current_results}

            all_eval_ids = sorted(
                set(list(baseline_by_eval.keys()) + list(skill_by_eval.keys()))
            )
            for eval_id in all_eval_ids:
                sk = skill_by_eval.get(eval_id)
                bl = baseline_by_eval.get(eval_id)
                sk_score = sk["score"] if sk else "—"
                bl_score = bl["score"] if bl else "—"

                if sk and bl:
                    sk_n, sk_d = parse_score(sk["score"])
                    bl_n, bl_d = parse_score(bl["score"])
                    sk_pct = round(sk_n / sk_d * 100) if sk_d else 0
                    bl_pct = round(bl_n / bl_d * 100) if bl_d else 0
                    diff = sk_pct - bl_pct
                    arrow = "+" if diff > 0 else ""
                    delta_str = f"{arrow}{diff}%" if diff != 0 else "="
                else:
                    delta_str = "—"

                lines.append(f"| {eval_id} | {sk_score} | {bl_score} | {delta_str} |")

    lines.append("")
    return "\n".join(lines)


def generate_dashboard():
    """Generate the full dashboard.md."""
    # Find all skills with eval results
    skill_names = []
    if EVAL_RESULTS_DIR.exists():
        for d in sorted(EVAL_RESULTS_DIR.iterdir()):
            if d.is_dir() and (d / "results.jsonl").exists():
                skill_names.append(d.name)

    # Also find skills without results yet
    for base in [SKILLS_DIR, DRAFTS_DIR]:
        if base.exists():
            for d in sorted(base.iterdir()):
                if d.is_dir() and (d / "skill.md").exists():
                    if d.name not in skill_names:
                        skill_names.append(d.name)

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    lines = []
    lines.append("# Skills Dashboard")
    lines.append("")
    lines.append(f"*Last generated: {now}*")
    lines.append("")

    # Summary table
    lines.append("## Overview")
    lines.append("")
    lines.append(
        "| Skill | Status | Version | Rating | Evals | Skill Impact |"
    )
    lines.append(
        "|-------|--------|---------|--------|-------|-------------|"
    )

    for skill_name in skill_names:
        results = load_results(skill_name)
        version = get_skill_version(skill_name)
        location = get_skill_location(skill_name)
        status = "draft" if location == "drafts" else "prod"
        num_evals = count_evals(skill_name)

        skill_results = [r for r in results if r.get("with_skill", True)]
        baseline_results = [r for r in results if not r.get("with_skill", True)]

        # Current version results
        current_results = [
            r for r in skill_results if r.get("skill_version") == version
        ]
        if current_results:
            total_num = sum(parse_score(r["score"])[0] for r in current_results)
            total_denom = sum(parse_score(r["score"])[1] for r in current_results)
            pct = round(total_num / total_denom * 100) if total_denom > 0 else 0
        else:
            pct = 0

        bar = "█" * (pct // 10) + "░" * (10 - pct // 10)

        # Baseline comparison
        if baseline_results:
            bl_num = sum(parse_score(r["score"])[0] for r in baseline_results)
            bl_denom = sum(parse_score(r["score"])[1] for r in baseline_results)
            bl_pct = round(bl_num / bl_denom * 100) if bl_denom > 0 else 0
            diff = pct - bl_pct
            arrow = "+" if diff > 0 else ""
            baseline_str = f"{arrow}{diff}%" if diff != 0 else "="
        else:
            baseline_str = "—"

        display = f"[{skill_name}](#{skill_name})"
        lines.append(
            f"| {display} | `{status}` | `{version}` | {bar} {pct}% | {num_evals} | {baseline_str} |"
        )

    lines.append("")

    # Detailed sections
    lines.append("## Skill Details")
    lines.append("")

    for skill_name in skill_names:
        results = load_results(skill_name)
        lines.append(generate_skill_section(skill_name, results))
        lines.append("---")
        lines.append("")

    # Footer
    lines.append("## How to read this dashboard")
    lines.append("")
    lines.append("- **Rating** = percentage of eval criteria passed across all eval cases (all models combined)")
    lines.append(
        "- **Skill Impact** = does the skill help? Compares with-skill vs without-skill (baseline) on the same model and evals"
    )
    lines.append(
        "- **Best for task** = cheapest model that achieves the highest score on each eval (score first, cost as tiebreaker)"
    )
    lines.append(
        "- **Cross-model comparison** = how each model performs WITH the skill loaded"
    )
    lines.append(
        "- **Version notes** = brief description of what changed in each version"
    )
    lines.append(
        "- **vs Previous** = rating change from the prior skill version"
    )
    lines.append(
        "- Regenerate with: `python3 scripts/generate-dashboard.py`"
    )
    lines.append("")

    dashboard_content = "\n".join(lines)
    DASHBOARD_PATH.write_text(dashboard_content)
    print(f"Dashboard generated: {DASHBOARD_PATH}")
    print(f"Skills tracked: {len(skill_names)}")


if __name__ == "__main__":
    generate_dashboard()
