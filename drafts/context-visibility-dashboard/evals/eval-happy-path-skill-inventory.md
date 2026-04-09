<!-- eval-version: v1 -->
<!-- eval-notes: v1=Original criteria for skill inventory and activation mode analysis -->
# Eval: Skill Inventory and Activation Modes

**Skill:** `context-audit`
**Type:** happy-path

## Setup

A project with multiple skills at different scopes:
- Global skills: `~/.claude/skills/session-start-hook/SKILL.md` (auto-trigger)
- Project-ops skills: `./.claude/skills/eval-methodology/SKILL.md`, `./.claude/skills/dashboard-management/SKILL.md`, `./.claude/skills/eval-rebase/SKILL.md` (all auto-trigger)
- Draft skills: `drafts/nodejs-security/skill.md` (auto-trigger), `drafts/csv-to-excel-report/SKILL.md` (auto-trigger)

## Prompt

```
/context-audit --skills
```

## Expected behavior

- [ ] Lists all skills found across all scopes (global, project-ops, drafts, production)
- [ ] Identifies the scope/location of each skill
- [ ] Extracts trigger conditions or descriptions for each skill
- [ ] Checks for naming collisions (same name at different scopes)
- [ ] Checks for trigger keyword overlap between skills
- [ ] Reports activation mode (user-invocable vs auto-trigger) for each skill
- [ ] Flags any skills with ambiguous activation (no explicit trigger or mode)

## Should NOT

- Only check one skill directory and miss others
- Report skill names without checking their trigger conditions
- Skip the trigger overlap analysis
- Confuse project-ops skills (`.claude/skills/`) with subject skills (`drafts/`, `skills/`)

## Pass criteria

All 7 expected behaviors checked. Every skill across all scopes is found and analyzed. Activation modes are correctly identified. Trigger overlap analysis actually compares skills pairwise, not just lists them individually.
