# Context Visibility Dashboard

A two-part tool for understanding and debugging the context loaded into Claude Code sessions.

## The Problem

Claude Code loads context from multiple sources with layered precedence: global CLAUDE.md, project CLAUDE.md, worktree variations, global skills, project skills, settings files, MCP configs, hooks, and agents. When you have 10+ skills globally and 7 in a project, it becomes unclear what's actually active, what takes precedence, and whether instructions conflict.

## Components

### 1. Shell Dashboard (TUI)

An interactive terminal dashboard built with fzf that lets you browse all context sources, preview their contents, and run conflict analysis — without needing Claude.

**Features:**
- Lists every context source Claude Code checks (active or missing)
- Preview pane shows file contents with syntax highlighting
- Token estimation per source and total
- Built-in conflict analysis (Ctrl-A)
- Session summary with precedence info (Ctrl-S)

**Requirements:** `fzf` (required), `bat` (optional, for syntax highlighting)

### 2. Claude-Powered Audit (`/context-audit`)

A user-invocable skill that instructs Claude to read all context sources, analyze them for conflicts, and produce a structured report covering:
- Directive contradictions between CLAUDE.md files
- Overlapping skill triggers
- Settings conflicts across scopes
- Worktree-specific divergence

## Setup

### Shell Dashboard

```bash
# Make scripts executable
chmod +x ~/myskills/drafts/context-visibility-dashboard/scripts/*.sh

# Run directly
~/myskills/drafts/context-visibility-dashboard/scripts/cc-context-dashboard.sh

# Or add an alias to your shell profile
echo 'alias cc-ctx="~/myskills/drafts/context-visibility-dashboard/scripts/cc-context-dashboard.sh"' >> ~/.bashrc
```

### Ghostty Keybinding

Add to `~/.config/ghostty/config`:

```
# Open context dashboard in a new window with Super+Shift+D
keybind = super+shift+d=new_window:bash -c '$HOME/myskills/drafts/context-visibility-dashboard/scripts/cc-context-dashboard.sh'
```

### tmux Integration

```bash
# Open in new tmux window (from inside tmux)
cc-context-dashboard.sh --tmux

# Open as a split pane alongside your current work
cc-context-dashboard.sh --tmux-pane
```

### Claude Code Skill

To use the `/context-audit` skill, reference it in your project's settings:

```json
{
  "permissions": {
    "allow": [
      "Read(~/myskills/drafts/context-visibility-dashboard/**)"
    ]
  }
}
```

## Usage

### Shell Dashboard

```bash
cc-ctx                    # Interactive dashboard
cc-ctx --analyze          # Print conflict analysis to stdout
cc-ctx --dump             # List all sources (non-interactive)
cc-ctx --tmux             # Open in new tmux window
cc-ctx --tmux-pane        # Split current tmux pane
cc-ctx --ghostty          # Open in new Ghostty window
cc-ctx --project-dir /p   # Override project root
```

**Dashboard keybindings:**
| Key    | Action                                    |
|--------|------------------------------------------|
| Up/Down | Navigate source list                    |
| Enter  | Open selected file in $EDITOR            |
| Ctrl-A | Run conflict analysis                    |
| Ctrl-S | Show session summary with token breakdown |
| Esc    | Exit dashboard                           |

### Claude Audit

In a Claude Code session:

```
/context-audit              # Full analysis
/context-audit --brief      # Summary only
/context-audit --skills     # Focus on skill conflicts
```

## What It Checks

### Context Sources (in precedence order)

| Source | Path | Priority |
|--------|------|----------|
| Global CLAUDE.md | `~/.claude/CLAUDE.md` | Lowest |
| Parent CLAUDE.md | `../CLAUDE.md` (walking up) | Medium |
| Project CLAUDE.md | `./CLAUDE.md` | High |
| Project .claude/ CLAUDE.md | `./.claude/CLAUDE.md` | Highest |
| Global settings | `~/.claude/settings.json` | Base |
| Global local settings | `~/.claude/settings.local.json` | Override |
| Project settings | `./.claude/settings.json` | Override |
| Project local settings | `./.claude/settings.local.json` | Override |
| Global skills | `~/.claude/skills/*/SKILL.md` | Auto-loaded |
| Project-ops skills | `./.claude/skills/*/SKILL.md` | Auto-loaded |
| Agents | `./.claude/agents/*.md` | On reference |
| MCP config | `.mcp.json` | Auto-loaded |

### Analysis Checks

1. **Directive contradictions** — NEVER vs ALWAYS on the same topic across files
2. **Skill trigger overlap** — multiple skills matching the same context
3. **Naming collisions** — same skill name at different scopes
4. **Settings conflicts** — permissions/hooks that contradict
5. **Worktree divergence** — config differences from the main working tree
6. **Context budget** — total token estimate with warnings at >50k

## Architecture

```
scripts/
  cc-context-dashboard.sh    # Main TUI entry point
    - Discovers project root (git rev-parse)
    - Collects all context source paths
    - Formats for fzf with preview
    - Manages tmux/Ghostty launch modes

  analyze-context.sh          # Standalone conflict analyzer
    - Source inventory with token estimates
    - CLAUDE.md precedence mapping
    - Directive extraction and cross-file comparison
    - Skill trigger keyword overlap detection
    - Activation mode checking
    - Actionable recommendations
```

## Key Principles

- **Discovery over assumption** — checks actual filesystem paths, not documentation
- **Precedence clarity** — shows exactly which file wins when instructions conflict
- **Token awareness** — estimates context budget impact of each source
- **Two modes** — quick shell browsing (TUI) + deep AI analysis (skill)
- **No dependencies on Claude** — the shell dashboard works standalone
