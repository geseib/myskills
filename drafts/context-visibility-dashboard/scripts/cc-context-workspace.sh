#!/usr/bin/env bash
# cc-context-workspace.sh — Launch Claude Code + Context Dashboard side-by-side
#
# Opens a tmux session with:
#   Left:         Claude Code (for the current project)
#   Right-top:    Document viewer (preview of selected context source)
#   Right-bottom: File navigator (context source list)
#
# Usage:
#   cc-context-workspace.sh                  # Run inside an existing terminal
#   cc-context-workspace.sh --ghostty        # Open in a new Ghostty window
#   cc-context-workspace.sh --project-dir /p # Override project root
#
# Layout:
#   ┌─────────────────────┬─────────────────────┐
#   │                     │    Doc Viewer        │
#   │                     │    (file preview)    │
#   │   Claude Code       │                     │
#   │                     ├─────────────────────┤
#   │                     │    File Nav          │
#   │                     │    (source list)     │
#   └─────────────────────┴─────────────────────┘

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SESSION="cc-ctx-workspace"
PROJECT_DIR=""
GHOSTTY_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --ghostty)      GHOSTTY_MODE=true; shift;;
        --project-dir)  PROJECT_DIR="$2"; shift 2;;
        -h|--help)
            sed -n '2,/^$/{ s/^# //; s/^#$//; p }' "$0"
            exit 0
            ;;
        *) echo "Unknown option: $1" >&2; exit 1;;
    esac
done

if [[ -z "$PROJECT_DIR" ]]; then
    PROJECT_DIR=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
fi

# --- Dependency checks ---

for cmd in tmux fzf; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "ERROR: $cmd is required but not installed." >&2
        exit 1
    fi
done

if ! command -v claude >/dev/null 2>&1; then
    echo "WARNING: 'claude' CLI not found. Left pane will open a shell instead." >&2
fi

# --- Ghostty launch ---

if [[ "$GHOSTTY_MODE" == true ]]; then
    if command -v ghostty >/dev/null 2>&1; then
        ghostty -e "$0" --project-dir "$PROJECT_DIR" &
        disown
        echo "Workspace opened in new Ghostty window."
        exit 0
    else
        echo "Ghostty not found. Running in current terminal." >&2
    fi
fi

# --- Kill existing session if present ---

if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "Session '$SESSION' already exists. Attaching..."
    exec tmux attach -t "$SESSION"
fi

# --- Build the layout ---

DASHBOARD_CMD="$SCRIPT_DIR/cc-context-dashboard.sh --preview-top --project-dir $PROJECT_DIR"

# Determine Claude command
if command -v claude >/dev/null 2>&1; then
    CLAUDE_CMD="cd $PROJECT_DIR && claude"
else
    CLAUDE_CMD="cd $PROJECT_DIR && echo 'Claude Code CLI not found. Install: npm install -g @anthropic-ai/claude-code' && exec \$SHELL"
fi

# Create session: left pane = Claude Code
tmux new-session -d -s "$SESSION" -c "$PROJECT_DIR"

# Send Claude command to the first pane
tmux send-keys -t "$SESSION" "$CLAUDE_CMD" C-m

# Split right pane (45% width) for the context dashboard
tmux split-window -h -t "$SESSION" -p 45 -c "$PROJECT_DIR"

# Run the dashboard with preview-on-top in the right pane
tmux send-keys -t "$SESSION" "$DASHBOARD_CMD" C-m

# Focus the left pane (Claude Code)
tmux select-pane -t "$SESSION:0.0"

# Attach
exec tmux attach -t "$SESSION"
