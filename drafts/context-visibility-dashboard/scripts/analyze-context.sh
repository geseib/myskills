#!/usr/bin/env bash
# analyze-context.sh — Analyze Claude Code context for conflicts and ambiguity
#
# Scans all active context sources and produces a report covering:
#   1. Source inventory with token estimates
#   2. CLAUDE.md precedence and potential conflicts
#   3. Skill trigger overlap detection
#   4. Directive contradiction detection
#   5. Recommendations
#
# Usage:
#   analyze-context.sh [--project-dir DIR] [--json]

set -euo pipefail

CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
PROJECT_DIR=""
OUTPUT_JSON=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --project-dir)  PROJECT_DIR="$2"; shift 2;;
        --json)         OUTPUT_JSON=true; shift;;
        *) shift;;
    esac
done

if [[ -z "$PROJECT_DIR" ]]; then
    PROJECT_DIR=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
fi

# Colors (when stdout is a terminal or piped to less -R)
if [[ -t 1 ]] || [[ "${LESS:-}" == *R* ]]; then
    BOLD='\033[1m'
    RED='\033[0;31m'
    YELLOW='\033[0;33m'
    GREEN='\033[0;32m'
    CYAN='\033[0;36m'
    DIM='\033[2m'
    RESET='\033[0m'
else
    BOLD='' RED='' YELLOW='' GREEN='' CYAN='' DIM='' RESET=''
fi

# --- Helpers ---

heading() {
    echo ""
    echo -e "${BOLD}${CYAN}$1${RESET}"
    echo -e "${DIM}$(printf '─%.0s' $(seq 1 ${#1}))${RESET}"
    echo ""
}

warn() { echo -e "  ${YELLOW}WARNING:${RESET} $1"; }
info() { echo -e "  ${GREEN}OK:${RESET} $1"; }
issue() { echo -e "  ${RED}CONFLICT:${RESET} $1"; }

file_tokens() {
    local path="$1"
    if [[ -f "$path" ]]; then
        local size
        size=$(wc -c < "$path" | tr -d ' ')
        echo $(( size / 4 ))
    else
        echo 0
    fi
}

# --- Source inventory ---

inventory() {
    heading "1. Context Source Inventory"

    local total_tokens=0
    local sources=()

    # CLAUDE.md files
    for path in \
        "$CLAUDE_HOME/CLAUDE.md" \
        "$PROJECT_DIR/CLAUDE.md" \
        "$PROJECT_DIR/.claude/CLAUDE.md"; do
        if [[ -f "$path" ]]; then
            local t
            t=$(file_tokens "$path")
            total_tokens=$(( total_tokens + t ))
            printf "  ${GREEN}*${RESET} %-14s %-55s ~%5d tokens\n" "[CLAUDE.MD]" "${path/#$HOME/~}" "$t"
            sources+=("$path")
        fi
    done

    # Settings
    for path in \
        "$CLAUDE_HOME/settings.json" \
        "$CLAUDE_HOME/settings.local.json" \
        "$PROJECT_DIR/.claude/settings.json" \
        "$PROJECT_DIR/.claude/settings.local.json"; do
        if [[ -f "$path" ]]; then
            local t
            t=$(file_tokens "$path")
            total_tokens=$(( total_tokens + t ))
            printf "  ${GREEN}*${RESET} %-14s %-55s ~%5d tokens\n" "[SETTINGS]" "${path/#$HOME/~}" "$t"
            sources+=("$path")
        fi
    done

    # Skills
    for base in "$CLAUDE_HOME/skills" "$PROJECT_DIR/.claude/skills" "$PROJECT_DIR/drafts" "$PROJECT_DIR/skills"; do
        [[ -d "$base" ]] || continue
        while IFS= read -r -d '' sf; do
            local t skill_name scope
            t=$(file_tokens "$sf")
            total_tokens=$(( total_tokens + t ))
            skill_name=$(basename "$(dirname "$sf")")
            case "$base" in
                */.claude/skills) scope="Project-Ops";;
                */drafts)         scope="Draft";;
                */skills)         scope="Production";;
                *)                scope="Global";;
            esac
            printf "  ${GREEN}*${RESET} %-14s %-55s ~%5d tokens\n" "[SKILL]" "$scope: $skill_name" "$t"
            sources+=("$sf")
        done < <(find "$base" -maxdepth 2 \( -name "SKILL.md" -o -name "skill.md" \) -print0 2>/dev/null || true)
    done

    # MCP
    for path in "$CLAUDE_HOME/.mcp.json" "$PROJECT_DIR/.mcp.json"; do
        if [[ -f "$path" ]]; then
            local t
            t=$(file_tokens "$path")
            total_tokens=$(( total_tokens + t ))
            printf "  ${GREEN}*${RESET} %-14s %-55s ~%5d tokens\n" "[MCP]" "${path/#$HOME/~}" "$t"
            sources+=("$path")
        fi
    done

    echo ""
    echo -e "  Total active sources: ${BOLD}${#sources[@]}${RESET}"
    echo -e "  Estimated total context: ${BOLD}~${total_tokens} tokens${RESET}"

    # Warn if context is getting large
    if (( total_tokens > 50000 )); then
        echo ""
        warn "Context exceeds ~50k tokens. Large context can slow responses and increase cost."
    fi
}

# --- CLAUDE.md precedence analysis ---

claudemd_analysis() {
    heading "2. CLAUDE.md Precedence Analysis"

    local files=()
    local labels=()

    if [[ -f "$CLAUDE_HOME/CLAUDE.md" ]]; then
        files+=("$CLAUDE_HOME/CLAUDE.md")
        labels+=("Global (~/.claude/CLAUDE.md)")
    fi
    if [[ -f "$PROJECT_DIR/CLAUDE.md" ]]; then
        files+=("$PROJECT_DIR/CLAUDE.md")
        labels+=("Project root (CLAUDE.md)")
    fi
    if [[ -f "$PROJECT_DIR/.claude/CLAUDE.md" ]]; then
        files+=("$PROJECT_DIR/.claude/CLAUDE.md")
        labels+=("Project .claude/ (.claude/CLAUDE.md)")
    fi

    if [[ ${#files[@]} -eq 0 ]]; then
        info "No CLAUDE.md files found."
        return
    fi

    echo "  Load order (last wins on conflicts):"
    for i in "${!files[@]}"; do
        echo -e "    $(( i + 1 )). ${labels[$i]}"
    done

    if [[ ${#files[@]} -gt 1 ]]; then
        echo ""
        echo "  Scanning for directive conflicts..."
        echo ""

        # Extract strong directives from each file
        local -A directives_by_file
        for i in "${!files[@]}"; do
            local f="${files[$i]}"
            # Look for lines with NEVER, ALWAYS, MUST, DO NOT, IMPORTANT
            local directives
            directives=$(grep -inE '(^|\s)(NEVER|ALWAYS|MUST|DO NOT|IMPORTANT|CRITICAL|REQUIRED|FORBIDDEN|OVERRIDE)(\s|:)' "$f" 2>/dev/null | head -20 || true)
            if [[ -n "$directives" ]]; then
                echo -e "  ${BOLD}${labels[$i]}:${RESET}"
                while IFS= read -r line; do
                    echo -e "    ${DIM}$line${RESET}"
                done <<< "$directives"
                echo ""
            fi
        done

        # Check for direct contradictions between files
        echo "  Cross-file contradiction check:"
        local found_contradiction=false
        for (( i=0; i<${#files[@]}; i++ )); do
            for (( j=i+1; j<${#files[@]}; j++ )); do
                # Look for cases where one says NEVER and the other says ALWAYS about the same topic
                local nevers_i alwayses_j
                nevers_i=$(grep -ioP '(?:NEVER|DO NOT|FORBIDDEN)\s+\K\w+(\s+\w+){0,3}' "${files[$i]}" 2>/dev/null | tr '[:upper:]' '[:lower:]' | sort -u || true)
                alwayses_j=$(grep -ioP '(?:ALWAYS|MUST|REQUIRED)\s+\K\w+(\s+\w+){0,3}' "${files[$j]}" 2>/dev/null | tr '[:upper:]' '[:lower:]' | sort -u || true)

                if [[ -n "$nevers_i" && -n "$alwayses_j" ]]; then
                    # Find common words that might indicate contradiction
                    local common
                    common=$(comm -12 <(echo "$nevers_i" | tr ' ' '\n' | sort -u) <(echo "$alwayses_j" | tr ' ' '\n' | sort -u) 2>/dev/null || true)
                    if [[ -n "$common" ]]; then
                        issue "Possible contradiction between ${labels[$i]} and ${labels[$j]}"
                        echo -e "    Keywords in both NEVER/DO NOT and ALWAYS/MUST: ${YELLOW}$(echo "$common" | tr '\n' ', ')${RESET}"
                        echo "    Review these files manually to confirm."
                        found_contradiction=true
                    fi
                fi
            done
        done

        if [[ "$found_contradiction" == false ]]; then
            info "No obvious directive contradictions detected."
        fi
    else
        info "Only one CLAUDE.md file — no conflict possible."
    fi
}

# --- Skill trigger overlap ---

skill_trigger_analysis() {
    heading "3. Skill Trigger Overlap Analysis"

    local skill_files=()
    local skill_names=()
    local skill_triggers=()

    # Collect all skills with their triggers
    for base in "$CLAUDE_HOME/skills" "$PROJECT_DIR/.claude/skills" "$PROJECT_DIR/drafts" "$PROJECT_DIR/skills"; do
        [[ -d "$base" ]] || continue
        while IFS= read -r -d '' sf; do
            local name trigger_line description_line
            name=$(basename "$(dirname "$sf")")
            skill_files+=("$sf")
            skill_names+=("$name")

            # Extract trigger conditions from near the top of the file (first 40 lines)
            # Only match lines that START with trigger-like patterns, not instructional references
            trigger_line=$(head -40 "$sf" 2>/dev/null | grep -iP '^\s*(TRIGGER\s*(when|:)|DO NOT TRIGGER|When to use|Use this when|Activate when)' 2>/dev/null | head -3 || true)

            # Fall back to description from frontmatter
            if [[ -z "$trigger_line" ]]; then
                description_line=$(grep -m1 '^description:' "$sf" 2>/dev/null | sed 's/^description:\s*//' || true)
                trigger_line="${description_line:-[no explicit trigger found]}"
            fi

            skill_triggers+=("$trigger_line")
        done < <(find "$base" -maxdepth 2 \( -name "SKILL.md" -o -name "skill.md" \) -print0 2>/dev/null || true)
    done

    if [[ ${#skill_files[@]} -eq 0 ]]; then
        info "No skills found."
        return
    fi

    echo "  Found ${#skill_files[@]} skills:"
    echo ""
    for i in "${!skill_names[@]}"; do
        echo -e "  ${BOLD}${skill_names[$i]}${RESET}"
        echo -e "    ${DIM}${skill_triggers[$i]}${RESET}"
        echo ""
    done

    # Check for similar names
    echo "  Checking for naming collisions..."
    local found_collision=false
    for (( i=0; i<${#skill_names[@]}; i++ )); do
        for (( j=i+1; j<${#skill_names[@]}; j++ )); do
            if [[ "${skill_names[$i]}" == "${skill_names[$j]}" ]]; then
                issue "Duplicate skill name: '${skill_names[$i]}'"
                echo "    File 1: ${skill_files[$i]/#$HOME/~}"
                echo "    File 2: ${skill_files[$j]/#$HOME/~}"
                found_collision=true
            fi
        done
    done
    if [[ "$found_collision" == false ]]; then
        info "No skill naming collisions."
    fi

    # Check for keyword overlap in triggers
    echo ""
    echo "  Checking for trigger keyword overlap..."
    local found_overlap=false
    for (( i=0; i<${#skill_names[@]}; i++ )); do
        for (( j=i+1; j<${#skill_names[@]}; j++ )); do
            local words_i words_j common
            words_i=$(echo "${skill_triggers[$i]}" | tr '[:upper:]' '[:lower:]' | grep -oP '\b[a-z]{4,}\b' | sort -u || true)
            words_j=$(echo "${skill_triggers[$j]}" | tr '[:upper:]' '[:lower:]' | grep -oP '\b[a-z]{4,}\b' | sort -u || true)

            if [[ -n "$words_i" && -n "$words_j" ]]; then
                common=$(comm -12 <(echo "$words_i") <(echo "$words_j") 2>/dev/null || true)
                # Filter out very common words
                common=$(echo "$common" | grep -vE '^(this|that|with|from|when|then|have|will|been|code|file|used|using|make|also|each|into|more|some|than|them|they|what|your)$' || true)
                local count
                count=$(echo "$common" | grep -c . 2>/dev/null || echo 0)
                if (( count >= 3 )); then
                    warn "Trigger overlap between '${skill_names[$i]}' and '${skill_names[$j]}'"
                    echo -e "    Shared keywords: ${YELLOW}$(echo "$common" | tr '\n' ', ' | sed 's/,$//')${RESET}"
                    found_overlap=true
                fi
            fi
        done
    done
    if [[ "$found_overlap" == false ]]; then
        info "No significant trigger overlaps detected."
    fi
}

# --- User-invocable vs auto-trigger check ---

skill_invocability_check() {
    heading "4. Skill Activation Mode Check"

    for base in "$CLAUDE_HOME/skills" "$PROJECT_DIR/.claude/skills" "$PROJECT_DIR/drafts" "$PROJECT_DIR/skills"; do
        [[ -d "$base" ]] || continue
        while IFS= read -r -d '' sf; do
            local name mode
            name=$(basename "$(dirname "$sf")")

            # Check frontmatter for user-invocable field
            if grep -q 'user-invocable:\s*true' "$sf" 2>/dev/null; then
                mode="user-invocable (slash command)"
            elif grep -q 'user-invocable:\s*false' "$sf" 2>/dev/null; then
                mode="auto-trigger"
            elif grep -qi 'TRIGGER when' "$sf" 2>/dev/null; then
                mode="auto-trigger (inferred from TRIGGER pattern)"
            else
                mode="unknown (no explicit mode set)"
            fi

            printf "  %-30s %s\n" "$name" "$mode"
        done < <(find "$base" -maxdepth 2 \( -name "SKILL.md" -o -name "skill.md" \) -print0 2>/dev/null || true)
    done
}

# --- Recommendations ---

recommendations() {
    heading "5. Recommendations"

    local has_recs=false

    # Check for missing project CLAUDE.md
    if [[ ! -f "$PROJECT_DIR/CLAUDE.md" && ! -f "$PROJECT_DIR/.claude/CLAUDE.md" ]]; then
        warn "No project-level CLAUDE.md found. Consider adding one for project-specific instructions."
        has_recs=true
    fi

    # Check for both CLAUDE.md locations (potential confusion)
    if [[ -f "$PROJECT_DIR/CLAUDE.md" && -f "$PROJECT_DIR/.claude/CLAUDE.md" ]]; then
        warn "Both CLAUDE.md and .claude/CLAUDE.md exist in project root."
        echo "    Both are loaded. Ensure they don't have conflicting instructions."
        has_recs=true
    fi

    # Check for worktree
    local wt
    wt=$(git rev-parse --git-dir 2>/dev/null || echo "")
    local common
    common=$(git rev-parse --git-common-dir 2>/dev/null || echo "")
    if [[ -n "$wt" && -n "$common" && "$(realpath "$wt" 2>/dev/null)" != "$(realpath "$common" 2>/dev/null)" ]]; then
        warn "Running in a git worktree. CLAUDE.md may differ from the main working tree."
        echo "    Main tree: $(dirname "$(realpath "$common")")"
        echo "    This worktree: $PROJECT_DIR"
        has_recs=true
    fi

    # Check for settings.local.json (may be gitignored = invisible to teammates)
    if [[ -f "$PROJECT_DIR/.claude/settings.local.json" ]]; then
        warn "Project has settings.local.json (typically gitignored). These overrides are invisible to collaborators."
        has_recs=true
    fi

    if [[ "$has_recs" == false ]]; then
        info "No issues detected. Context configuration looks clean."
    fi
}

# --- Main ---

echo -e "${BOLD}Claude Code Context Analysis Report${RESET}"
echo -e "${DIM}Project: $PROJECT_DIR${RESET}"
echo -e "${DIM}Date: $(date -Iseconds)${RESET}"

inventory
claudemd_analysis
skill_trigger_analysis
skill_invocability_check
recommendations

echo ""
echo -e "${DIM}---${RESET}"
echo -e "${DIM}For deeper AI-powered analysis, run /context-audit in a Claude Code session.${RESET}"
