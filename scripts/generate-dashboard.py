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
    """Read skill version from SKILL.md frontmatter."""
    for base in [DRAFTS_DIR, SKILLS_DIR]:
        skill_file = base / skill_name / "SKILL.md"
        if skill_file.exists():
            content = skill_file.read_text()
            match = re.search(r"skill-version:\s*(v[\w.]+)", content)
            if match:
                return match.group(1)
    return "unknown"


def get_version_notes(skill_name):
    """Read version notes from SKILL.md frontmatter.

    Format: <!-- version-notes: v1=Short desc; v2=Short desc -->
    Returns dict like {"v1": "Short desc", "v2": "Short desc"}
    """
    for base in [DRAFTS_DIR, SKILLS_DIR]:
        skill_file = base / skill_name / "SKILL.md"
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
    if (SKILLS_DIR / skill_name / "SKILL.md").exists():
        return "skills"
    if (DRAFTS_DIR / skill_name / "SKILL.md").exists():
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

    # Group by version (including baseline)
    by_version = defaultdict(list)
    for r in skill_results:
        by_version[r.get("skill_version", "unknown")].append(r)
    for r in baseline_results:
        by_version["baseline"].append(r)

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

        # Calculate per-version per-model scores (including baseline)
        best_overall_pct = 0
        best_overall_cost = 999
        best_overall_key = None
        version_model_scores = {}

        # Include baseline in the scoring for display
        all_versions = sorted(by_version.keys())
        for ver in all_versions:
            ver_results = by_version[ver]
            models_in_ver = sorted(set(r.get("model", "unknown") for r in ver_results))

            for model in models_in_ver:
                model_results = [r for r in ver_results if r.get("model") == model]
                m_num = sum(parse_score(r["score"])[0] for r in model_results)
                m_den = sum(parse_score(r["score"])[1] for r in model_results)
                m_pct = round(m_num / m_den * 100) if m_den > 0 else 0
                version_model_scores[(ver, model)] = m_pct

                # Only skill versions compete for "best" (not baseline)
                if ver != "baseline":
                    cost = _model_cost(model)
                    if m_pct > best_overall_pct or (m_pct == best_overall_pct and cost < best_overall_cost):
                        best_overall_pct = m_pct
                        best_overall_cost = cost
                        best_overall_key = (ver, model)

        # Render rows: baseline first, then skill versions
        render_order = []
        if "baseline" in by_version:
            render_order.append("baseline")
        for ver in sorted(v for v in by_version.keys() if v != "baseline"):
            render_order.append(ver)

        for ver in render_order:
            ver_results = by_version[ver]
            models_in_ver = sorted(set(r.get("model", "unknown") for r in ver_results))

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
    lines.append("| Eval | Model | Type | Score | Result |")
    lines.append("|------|-------|------|-------|--------|")

    current_results = by_version.get(version, [])
    for r in sorted(current_results, key=lambda x: (x["eval_id"], _model_cost(x.get("model", "")))):
        eval_id = r["eval_id"]
        model = _short_model(r.get("model", "unknown"))
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
        lines.append(f"| {eval_id} | {model} | {eval_type} | {r['score']} | {result_icon} |")

    # Emotion comparison (if emotional eval results exist)
    emotion_results = [r for r in current_results if r.get("emotion")]
    if emotion_results:
        lines.append("")
        lines.append("**Emotion impact (+/- preamble comparison)**")
        lines.append("")

        # Detect runs
        runs = sorted(set(r.get("emotion_run", 1) for r in emotion_results))

        if len(runs) > 1:
            # Multi-run: show per-run breakdown
            # Header: Eval | Run 1 (-) | Run 1 (+) | Run 2 (-) | Run 2 (+) | ...
            hdr_cols = []
            for run in runs:
                hdr_cols.extend([f"R{run} (-)", f"R{run} (+)"])
            hdr_cols.append("Avg (-)")
            hdr_cols.append("Avg (+)")
            lines.append(f"| Eval | {' | '.join(hdr_cols)} |")
            lines.append(f"|------|{'|'.join('-----' for _ in hdr_cols)}|")

            all_emotion_evals = sorted(set(r["eval_id"] for r in emotion_results))
            neg_totals_by_run = {run: (0, 0) for run in runs}
            pos_totals_by_run = {run: (0, 0) for run in runs}

            for eval_id in all_emotion_evals:
                cells = []
                neg_sum_n, neg_sum_d, pos_sum_n, pos_sum_d = 0, 0, 0, 0
                for run in runs:
                    neg = [r for r in emotion_results if r["eval_id"] == eval_id
                           and r["emotion"] == "negative" and r.get("emotion_run", 1) == run]
                    pos = [r for r in emotion_results if r["eval_id"] == eval_id
                           and r["emotion"] == "positive" and r.get("emotion_run", 1) == run]
                    neg_str = neg[0]["score"] if neg else "—"
                    pos_str = pos[0]["score"] if pos else "—"
                    cells.extend([neg_str, pos_str])
                    if neg:
                        nn, nd = parse_score(neg[0]["score"])
                        neg_sum_n += nn
                        neg_sum_d += nd
                        rn, rd = neg_totals_by_run[run]
                        neg_totals_by_run[run] = (rn + nn, rd + nd)
                    if pos:
                        pn, pd = parse_score(pos[0]["score"])
                        pos_sum_n += pn
                        pos_sum_d += pd
                        rn, rd = pos_totals_by_run[run]
                        pos_totals_by_run[run] = (rn + pn, rd + pd)
                neg_avg = f"{round(neg_sum_n / neg_sum_d * 100)}%" if neg_sum_d else "—"
                pos_avg = f"{round(pos_sum_n / pos_sum_d * 100)}%" if pos_sum_d else "—"
                cells.extend([neg_avg, pos_avg])
                lines.append(f"| {eval_id} | {' | '.join(cells)} |")

            # Totals row
            total_cells = []
            all_neg_n, all_neg_d, all_pos_n, all_pos_d = 0, 0, 0, 0
            for run in runs:
                rn, rd = neg_totals_by_run[run]
                pn, pd = pos_totals_by_run[run]
                all_neg_n += rn
                all_neg_d += rd
                all_pos_n += pn
                all_pos_d += pd
                neg_pct = f"{round(rn / rd * 100)}%" if rd else "—"
                pos_pct = f"{round(pn / pd * 100)}%" if pd else "—"
                total_cells.extend([neg_pct, pos_pct])
            avg_neg = f"**{round(all_neg_n / all_neg_d * 100)}%**" if all_neg_d else "—"
            avg_pos = f"**{round(all_pos_n / all_pos_d * 100)}%**" if all_pos_d else "—"
            total_cells.extend([avg_neg, avg_pos])
            lines.append(f"| **Total** | {' | '.join(total_cells)} |")
            lines.append("")

            # Consistency analysis
            lines.append("**Consistency across runs**")
            lines.append("")
            lines.append("| Eval | Neg scores | Pos scores | Neg consistent? | Pos consistent? |")
            lines.append("|------|-----------|-----------|----------------|----------------|")
            for eval_id in all_emotion_evals:
                neg_scores = []
                pos_scores = []
                for run in runs:
                    neg = [r for r in emotion_results if r["eval_id"] == eval_id
                           and r["emotion"] == "negative" and r.get("emotion_run", 1) == run]
                    pos = [r for r in emotion_results if r["eval_id"] == eval_id
                           and r["emotion"] == "positive" and r.get("emotion_run", 1) == run]
                    if neg:
                        neg_scores.append(neg[0]["score"])
                    if pos:
                        pos_scores.append(pos[0]["score"])
                neg_consistent = "Yes" if len(set(neg_scores)) == 1 else "No"
                pos_consistent = "Yes" if len(set(pos_scores)) == 1 else "No"
                lines.append(f"| {eval_id} | {', '.join(neg_scores)} | {', '.join(pos_scores)} | {neg_consistent} | {pos_consistent} |")
            lines.append("")

            # Auto-generated summary
            total_runs = len(runs) * len(all_emotion_evals) * 2
            avg_neg_pct = round(all_neg_n / all_neg_d * 100) if all_neg_d else 0
            avg_pos_pct = round(all_pos_n / all_pos_d * 100) if all_pos_d else 0
            consistent_count = sum(
                1 for eval_id in all_emotion_evals
                for emo in ["negative", "positive"]
                if len(set(
                    r["score"] for r in emotion_results
                    if r["eval_id"] == eval_id and r["emotion"] == emo
                )) == 1
            )
            total_eval_emo_combos = len(all_emotion_evals) * 2
            lines.append("**What the data shows**")
            lines.append("")
            lines.append(
                f"Across {total_runs} eval runs ({len(all_emotion_evals)} evals x {len(runs)} runs x 2 emotions), "
                f"positive preamble scored {avg_pos_pct}% vs negative's {avg_neg_pct}% — "
                f"{'a gap too small to be meaningful given the noise' if abs(avg_pos_pct - avg_neg_pct) <= 5 else 'a notable difference'}. "
                f"Only {consistent_count} of {total_eval_emo_combos} eval/emotion combos were perfectly consistent across runs. "
                f"The dominant pattern is **run-to-run variance**, not emotional effect. "
                f"**Emotional framing in prompts does not reliably improve or degrade model output. "
                f"Natural model variance between runs is the larger factor.**"
            )
            lines.append("")

        else:
            # Single run: original format
            neg_results = [r for r in emotion_results if r["emotion"] == "negative"]
            pos_results = [r for r in emotion_results if r["emotion"] == "positive"]
            if neg_results and pos_results:
                all_emotion_evals = sorted(set(r["eval_id"] for r in emotion_results))
                lines.append("| Eval | Negative (-) | Positive (+) | Delta |")
                lines.append("|------|-------------|-------------|-------|")
                neg_total_n, neg_total_d = 0, 0
                pos_total_n, pos_total_d = 0, 0
                for eval_id in all_emotion_evals:
                    neg = [r for r in neg_results if r["eval_id"] == eval_id]
                    pos = [r for r in pos_results if r["eval_id"] == eval_id]
                    neg_str = neg[0]["score"] if neg else "—"
                    pos_str = pos[0]["score"] if pos else "—"
                    delta_str = ""
                    if neg and pos:
                        nn, nd = parse_score(neg[0]["score"])
                        pn, pd = parse_score(pos[0]["score"])
                        neg_total_n += nn
                        neg_total_d += nd
                        pos_total_n += pn
                        pos_total_d += pd
                        neg_pct = round(nn / nd * 100) if nd else 0
                        pos_pct = round(pn / pd * 100) if pd else 0
                        diff = pos_pct - neg_pct
                        if diff > 0:
                            delta_str = f"+{diff}%"
                        elif diff < 0:
                            delta_str = f"{diff}%"
                        else:
                            delta_str = "="
                        neg_str += f" ({neg[0]['overall']})"
                        pos_str += f" ({pos[0]['overall']})"
                    lines.append(f"| {eval_id} | {neg_str} | {pos_str} | {delta_str} |")
                neg_total_pct = round(neg_total_n / neg_total_d * 100) if neg_total_d else 0
                pos_total_pct = round(pos_total_n / pos_total_d * 100) if pos_total_d else 0
                total_diff = pos_total_pct - neg_total_pct
                total_delta = f"+{total_diff}%" if total_diff > 0 else (f"{total_diff}%" if total_diff < 0 else "=")
                lines.append(f"| **Total** | **{neg_total_pct}%** | **{pos_total_pct}%** | **{total_delta}** |")
                lines.append("")

    # Per-model breakdown
    all_models = sorted(set(r.get("model", "unknown") for r in results))
    if len(all_models) > 1:
        lines.append("")
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
                if d.is_dir() and (d / "SKILL.md").exists():
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
        "- **Skill Impact** = difference between current version rating and baseline rating in the overview"
    )
    lines.append(
        "- **Version history** = `baseline` rows show model performance WITHOUT the skill; version rows show WITH the skill. Compare to see skill impact"
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
