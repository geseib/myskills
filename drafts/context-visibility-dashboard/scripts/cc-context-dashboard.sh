#!/usr/bin/env bash
# cc-context-dashboard.sh — Claude Code Context Visibility Dashboard
#
# Shows all context sources loaded into a Claude Code session in an
# interactive TUI. Uses fzf for browsing with file preview, and supports
# tmux/Ghostty integration for side-by-side viewing.
#
# Usage:
#   cc-context-dashboard.sh                     # Run in current terminal
#   cc-context-dashboard.sh --tmux              # Open in new tmux window
#   cc-context-dashboard.sh --tmux-pane         # Split current tmux pane
#   cc-context-dashboard.sh --ghostty           # Open in new Ghostty window
#   cc-context-dashboard.sh --analyze           # Run conflict analysis
#   cc-context-dashboard.sh --project-dir DIR   # Override project root
#   cc-context-dashboard.sh --dump              # Dump source list to stdout (no TUI)
#
# Dependencies: fzf (required), bat (optional, for syntax highlighting)
# Optional: tmux, ghostty

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"

# --- Argument parsing ---

PROJECT_DIR=""
MODE="dashboard"  # dashboard | analyze | dump | tmux | tmux-pane | ghostty
PREVIEW_POS="right:60%:wrap"  # fzf --preview-window value

while [[ $# -gt 0 ]]; do
    case $1 in
        --analyze)      MODE="analyze"; shift;;
        --dump)         MODE="dump"; shift;;
        --tmux)         MODE="tmux"; shift;;
        --tmux-pane)    MODE="tmux-pane"; shift;;
        --ghostty)      MODE="ghostty"; shift;;
        --preview-top)  PREVIEW_POS="up:60%:wrap"; shift;;
        --project-dir)  PROJECT_DIR="$2"; shift 2;;
        -h|--help)
            sed -n '2,/^$/{ s/^# //; s/^#$//; p }' "$0"
            exit 0
            ;;
        *) echo "Unknown option: $1" >&2; exit 1;;
    esac
done

# --- Project detection ---

if [[ -z "$PROJECT_DIR" ]]; then
    PROJECT_DIR=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
fi

# --- Dependency checks ---

check_deps() {
    if ! command -v fzf >/dev/null 2>&1; then
        echo "ERROR: fzf is required but not installed." >&2
        echo "Install: brew install fzf  OR  apt install fzf" >&2
        exit 1
    fi
}

format_preview() {
    # Use the companion formatter that indents wrapped lines past the gutter
    echo "$SCRIPT_DIR/format-preview.sh"
}

# --- Git info helpers ---

get_worktree_info() {
    local git_dir common_dir
    git_dir=$(git rev-parse --git-dir 2>/dev/null) || { echo "NOT-GIT"; return; }
    common_dir=$(git rev-parse --git-common-dir 2>/dev/null) || { echo "MAIN"; return; }
    if [[ "$(realpath "$git_dir")" != "$(realpath "$common_dir")" ]]; then
        echo "WORKTREE"
    else
        echo "MAIN"
    fi
}

get_branch() {
    git branch --show-current 2>/dev/null || echo "detached"
}

# --- Context source collection ---
#
# Each source is written as a tab-delimited line:
#   REAL_PATH \t DISPLAY_LINE
#
# REAL_PATH is used by fzf for preview; DISPLAY_LINE is what the user sees.
# For missing files, REAL_PATH is set to "MISSING" so the preview can handle it.

collect_sources() {
    local out="$1"

    # -- CLAUDE.md files --
    emit_source "$out" "CLAUDE.MD" "Global (user)"          "$CLAUDE_HOME/CLAUDE.md"
    emit_source "$out" "CLAUDE.MD" "Project root"           "$PROJECT_DIR/CLAUDE.md"
    emit_source "$out" "CLAUDE.MD" "Project .claude/"       "$PROJECT_DIR/.claude/CLAUDE.md"

    # Walk parent directories (monorepo / nested project support)
    local dir
    dir=$(dirname "$PROJECT_DIR")
    while [[ "$dir" != "/" && "$dir" != "$HOME" && "$dir" != "." ]]; do
        emit_source "$out" "CLAUDE.MD" "Parent ($(basename "$dir"))" "$dir/CLAUDE.md"
        emit_source "$out" "CLAUDE.MD" "Parent ($(basename "$dir"))" "$dir/.claude/CLAUDE.md"
        dir=$(dirname "$dir")
    done

    # -- Settings files --
    emit_source "$out" "SETTINGS" "Global"         "$CLAUDE_HOME/settings.json"
    emit_source "$out" "SETTINGS" "Global local"   "$CLAUDE_HOME/settings.local.json"
    emit_source "$out" "SETTINGS" "Project"        "$PROJECT_DIR/.claude/settings.json"
    emit_source "$out" "SETTINGS" "Project local"  "$PROJECT_DIR/.claude/settings.local.json"

    # -- Skills: Global --
    collect_skills "$out" "$CLAUDE_HOME/skills" "Global"

    # -- Skills: Project operational (.claude/skills/) --
    collect_skills "$out" "$PROJECT_DIR/.claude/skills" "Project-Ops"

    # -- Skills: Subject (drafts/ and skills/) --
    collect_skills "$out" "$PROJECT_DIR/drafts" "Draft"
    collect_skills "$out" "$PROJECT_DIR/skills" "Production"

    # -- Agents --
    if [[ -d "$PROJECT_DIR/.claude/agents" ]]; then
        while IFS= read -r -d '' agent_file; do
            local name
            name=$(basename "$agent_file" .md)
            emit_source "$out" "AGENT" "$name" "$agent_file"
        done < <(find "$PROJECT_DIR/.claude/agents" -maxdepth 1 -name "*.md" -print0 2>/dev/null || true)
    fi

    # -- MCP configuration --
    emit_source "$out" "MCP" "Global"   "$CLAUDE_HOME/.mcp.json"
    emit_source "$out" "MCP" "Project"  "$PROJECT_DIR/.mcp.json"

    # -- Hooks (extracted from global settings.json) --
    collect_hooks "$out"
}

collect_skills() {
    local out="$1" base_dir="$2" scope_prefix="$3"
    [[ -d "$base_dir" ]] || return 0

    while IFS= read -r -d '' skill_file; do
        local skill_name
        skill_name=$(basename "$(dirname "$skill_file")")
        emit_source "$out" "SKILL" "$scope_prefix: $skill_name" "$skill_file"
    done < <(find "$base_dir" -maxdepth 2 \( -name "SKILL.md" -o -name "skill.md" \) -print0 2>/dev/null || true)
}

collect_hooks() {
    local out="$1"
    local settings="$CLAUDE_HOME/settings.json"
    [[ -f "$settings" ]] || return 0

    # Extract hook commands using python3 (available on most systems)
    python3 -c "
import json, sys
try:
    with open('$settings') as f:
        s = json.load(f)
    hooks = s.get('hooks', {})
    for event, hook_list in hooks.items():
        if isinstance(hook_list, list):
            for h in hook_list:
                cmd = h.get('command', '') if isinstance(h, dict) else ''
                if cmd:
                    print(f'{event}\t{cmd}')
except Exception:
    pass
" 2>/dev/null | while IFS=$'\t' read -r event cmd; do
        # Write hook entries — path points to settings.json since hooks are defined there
        local display
        display=$(printf "  %-12s %-28s %-52s %s" "[HOOK]" "$event" "$cmd" "active")
        printf '%s\t%s\n' "$settings" "$display" >> "$out"
    done
}

emit_source() {
    local out="$1" type="$2" scope="$3" path="$4"
    local status real_path display_path

    display_path="${path/#$HOME/~}"

    if [[ -f "$path" ]]; then
        local lines size
        lines=$(wc -l < "$path" 2>/dev/null | tr -d ' ')
        size=$(wc -c < "$path" 2>/dev/null | tr -d ' ')
        # Rough token estimate: ~4 chars per token
        local tokens=$(( size / 4 ))
        status="${lines}L ~${tokens}tok"
        real_path="$path"
    else
        status="--"
        real_path="MISSING"
    fi

    local marker
    [[ "$real_path" == "MISSING" ]] && marker="  " || marker="* "

    local display
    display=$(printf "%s%-12s %-28s %-52s %s" "$marker" "[$type]" "$scope" "$display_path" "$status")
    printf '%s\t%s\n' "$real_path" "$display" >> "$out"
}

# --- Summary stats ---

build_summary() {
    local sources_file="$1"
    local total found skills_count
    total=$(wc -l < "$sources_file" | tr -d ' ')
    found=$(grep -cv '^MISSING' "$sources_file" | tr -d ' ' 2>/dev/null || echo 0)
    skills_count=$(grep -c '\[SKILL\]' "$sources_file" | tr -d ' ' 2>/dev/null || echo 0)
    local worktree branch
    worktree=$(get_worktree_info)
    branch=$(get_branch)

    echo "CC Context Dashboard | $(basename "$PROJECT_DIR") @ $branch ($worktree) | $found active / $total checked | Skills: $skills_count"
    echo "Enter: open in \$EDITOR | Ctrl-A: analyze conflicts | Ctrl-S: summary | Esc: quit"
}

# --- Summary pane (Ctrl-S) ---

generate_summary() {
    local sources_file="$1"
    echo "============================================="
    echo "  Claude Code Context — Session Summary"
    echo "============================================="
    echo ""
    echo "Project:   $(basename "$PROJECT_DIR")"
    echo "Path:      $PROJECT_DIR"
    echo "Branch:    $(get_branch)"
    echo "Worktree:  $(get_worktree_info)"
    echo ""
    echo "--- Active Sources ---"
    echo ""

    local total_tokens=0
    while IFS=$'\t' read -r real_path display; do
        if [[ "$real_path" != "MISSING" && -f "$real_path" ]]; then
            local size
            size=$(wc -c < "$real_path" 2>/dev/null | tr -d ' ')
            local tokens=$(( size / 4 ))
            total_tokens=$(( total_tokens + tokens ))
            printf "  %-55s ~%5d tokens\n" "${real_path/#$HOME/~}" "$tokens"
        fi
    done < "$sources_file"

    echo ""
    echo "  Total estimated context: ~${total_tokens} tokens"
    echo ""
    echo "--- Precedence Order (CLAUDE.md) ---"
    echo ""
    echo "  1. Project .claude/CLAUDE.md  (highest priority)"
    echo "  2. Project root CLAUDE.md"
    echo "  3. Parent directory CLAUDE.md files"
    echo "  4. Global ~/.claude/CLAUDE.md  (lowest priority)"
    echo ""
    echo "--- Skill Loading ---"
    echo ""
    echo "  Project-Ops (.claude/skills/): auto-loaded, govern repo behavior"
    echo "  Global (~/.claude/skills/):    auto-loaded, user-wide defaults"
    echo "  Draft/Production (drafts/, skills/): loaded on reference/invocation"
    echo ""
    echo "Press q to return to dashboard."
}

# --- Temp file cleanup ---

_CLEANUP_FILES=()
cleanup() { rm -f "${_CLEANUP_FILES[@]}"; }
trap cleanup EXIT

mktmp() {
    local f
    f=$(mktemp "$1")
    _CLEANUP_FILES+=("$f")
    echo "$f"
}

# --- Launch modes ---

launch_dashboard() {
    check_deps

    local sources_file
    sources_file=$(mktmp /tmp/cc-ctx-sources.XXXXXX)
    local summary_script
    summary_script=$(mktmp /tmp/cc-ctx-summary.XXXXXX.sh)
    local summary_txt="${summary_script%.sh}.txt"
    _CLEANUP_FILES+=("$summary_txt")

    collect_sources "$sources_file"

    # Build header
    local header
    header=$(build_summary "$sources_file")

    # Write summary for Ctrl-S
    generate_summary "$sources_file" > "$summary_txt"

    local fmt
    fmt=$(format_preview)

    # Sort: active (*) first, missing (space) second
    local sorted_file
    sorted_file=$(mktmp /tmp/cc-ctx-sorted.XXXXXX)

    # Extract just display column and sort active-first
    sort -t$'\t' -k2,2 -r "$sources_file" > "$sorted_file"

    # Launch fzf
    cut -f2 "$sorted_file" | fzf \
        --ansi \
        --header="$header" \
        --no-mouse \
        --preview="
            line=\$(grep -nF {} '$sorted_file' | head -1 | cut -d: -f1)
            filepath=\$(sed -n \"\${line}p\" '$sorted_file' | cut -f1)
            if [ \"\$filepath\" = 'MISSING' ]; then
                echo 'File not found / not configured'
                echo ''
                echo 'This context source does not exist at the expected path.'
                echo 'It will not contribute to your Claude Code session.'
            elif [ -f \"\$filepath\" ]; then
                echo \"--- \$filepath ---\"
                echo \"Size: \$(wc -c < \"\$filepath\" | tr -d ' ') bytes, \$(wc -l < \"\$filepath\" | tr -d ' ') lines\"
                echo \"Est. tokens: \$(( \$(wc -c < \"\$filepath\" | tr -d ' ') / 4 ))\"
                echo '---'
                echo ''
                $fmt \"\$filepath\" \"\$FZF_PREVIEW_COLUMNS\" 2>/dev/null || cat -n \"\$filepath\"
            else
                echo \"Cannot read: \$filepath\"
            fi
        " \
        --preview-window="$PREVIEW_POS" \
        --bind="enter:execute(
            line=\$(grep -nF {} '$sorted_file' | head -1 | cut -d: -f1)
            filepath=\$(sed -n \"\${line}p\" '$sorted_file' | cut -f1)
            if [ -f \"\$filepath\" ]; then
                \${EDITOR:-less} \"\$filepath\"
            else
                echo 'File not found' | less
            fi
        )" \
        --bind="ctrl-a:execute($SCRIPT_DIR/analyze-context.sh --project-dir '$PROJECT_DIR' 2>&1 | less)" \
        --bind="ctrl-s:execute(less '$summary_txt')" \
        || true  # Don't fail on Esc
}

launch_dump() {
    local sources_file
    sources_file=$(mktmp /tmp/cc-ctx-sources.XXXXXX)

    collect_sources "$sources_file"

    echo "Claude Code Context Sources — $(basename "$PROJECT_DIR") @ $(get_branch) ($(get_worktree_info))"
    echo "$(printf '=%.0s' {1..80})"
    echo ""
    while IFS=$'\t' read -r _ display; do
        echo "$display"
    done < "$sources_file"
    echo ""

    local total found
    total=$(wc -l < "$sources_file" | tr -d ' ')
    found=$(grep -cv '^MISSING' "$sources_file" | tr -d ' ' 2>/dev/null || echo 0)
    echo "$found active sources out of $total checked."
}

launch_in_tmux_window() {
    if ! command -v tmux >/dev/null 2>&1; then
        echo "tmux not found. Running in current terminal." >&2
        launch_dashboard
        return
    fi
    if [[ -z "${TMUX:-}" ]]; then
        # Not inside tmux — create a new session
        tmux new-session -s cc-context -d "$0 --project-dir $PROJECT_DIR"
        tmux attach -t cc-context
    else
        tmux new-window -n "cc-context" "$0 --project-dir $PROJECT_DIR"
    fi
}

launch_in_tmux_pane() {
    if ! command -v tmux >/dev/null 2>&1 || [[ -z "${TMUX:-}" ]]; then
        echo "Not inside a tmux session. Use --tmux instead." >&2
        exit 1
    fi
    tmux split-window -h -p 50 "$0 --project-dir $PROJECT_DIR"
}

launch_in_ghostty() {
    if ! command -v ghostty >/dev/null 2>&1; then
        echo "Ghostty not found. Running in current terminal." >&2
        launch_dashboard
        return
    fi
    ghostty -e "$0" --project-dir "$PROJECT_DIR" &
    disown
    echo "Dashboard opened in new Ghostty window."
}

# --- Main ---

case "$MODE" in
    dashboard)  check_deps; launch_dashboard;;
    analyze)    exec "$SCRIPT_DIR/analyze-context.sh" --project-dir "$PROJECT_DIR";;
    dump)       launch_dump;;
    tmux)       launch_in_tmux_window;;
    tmux-pane)  launch_in_tmux_pane;;
    ghostty)    launch_in_ghostty;;
esac
