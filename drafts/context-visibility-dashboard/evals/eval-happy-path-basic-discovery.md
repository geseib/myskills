<!-- eval-version: v1 -->
<!-- eval-notes: v1=Original criteria for basic context source discovery -->
# Eval: Basic Context Source Discovery

**Skill:** `context-audit`
**Type:** happy-path

## Setup

A project with a standard Claude Code configuration:
- `~/.claude/CLAUDE.md` exists (global)
- `./CLAUDE.md` exists (project)
- `~/.claude/settings.json` exists (global)
- `./.claude/settings.json` exists (project)
- `~/.claude/skills/` has 2 skills
- `./.claude/skills/` has 3 skills

## Prompt

```
/context-audit
```

## Expected behavior

- [ ] Checks `~/.claude/CLAUDE.md` and reports whether it exists
- [ ] Checks `./CLAUDE.md` and reports whether it exists
- [ ] Checks `./.claude/CLAUDE.md` and reports whether it exists
- [ ] Checks global and project settings.json files
- [ ] Scans `~/.claude/skills/` for skill files
- [ ] Scans `./.claude/skills/` for skill files
- [ ] Reports token estimates per source
- [ ] Reports total estimated context tokens
- [ ] Presents findings in the structured output format from the skill
- [ ] Lists precedence order for CLAUDE.md files

## Should NOT

- Skip checking any of the documented context source paths
- Report a file as "active" without actually reading it
- Omit token estimation
- Present an unstructured wall of text instead of the specified format

## Pass criteria

All 10 expected behaviors are checked. The report follows the output format defined in the skill (inventory table, sections for each analysis area). Every context source path documented in the skill is checked, not just the ones that happen to exist.
