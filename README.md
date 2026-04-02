# My Skills

A personal repo for building, experimenting with, evaluating, and sharing Claude Code skills across projects.

## Why this repo exists

Skills scattered across projects get stale, duplicated, and forgotten. This repo is the **single source of truth** — one place to develop, test, and maintain skills, then distribute them to whichever projects need them.

## Structure

```
skills/          Production-ready skills
drafts/          Work-in-progress — experiments, imports, new ideas
evals/           Evaluation guides and cross-cutting test utilities
templates/       Starter scaffolds for new skills
catalog.md       Index of all production skills with tags
```

## Workflows

### Build a new skill

```bash
cp -r templates/basic drafts/my-new-skill
# Edit drafts/my-new-skill/SKILL.md
# Write eval cases in drafts/my-new-skill/evals/
# Test, iterate, refine
# When ready: mv drafts/my-new-skill skills/my-new-skill
# Add to catalog.md
```

### Import a skill from another project

1. Copy the skill into `drafts/`
2. Adapt it to your conventions (triggers, formatting, eval cases)
3. Test it against evals
4. Promote to `skills/` when ready

### Use a skill in another project

**Option A — Reference by path** (skill stays here, always up to date):

In your project's `.claude/settings.json` or CLAUDE.md, reference:
```
~/myskills/skills/<skill-name>/SKILL.md
```

**Option B — Copy into project** (skill is self-contained in that repo):

```bash
cp ~/myskills/skills/<skill-name>/SKILL.md \
   ~/my-project/.claude/skills/<skill-name>.md
```

**Option A** is better for skills you actively maintain here.
**Option B** is better when the project needs a stable snapshot or customization.

### Improve a skill based on real-world use

When you notice a skill underperforming in a project:
1. Bring the improvement back to `drafts/` (or edit directly in `skills/` for small fixes)
2. Update evals to cover the failure case
3. Test and re-promote if needed

## Skill anatomy

Each skill folder contains:

```
<skill-name>/
  SKILL.md        # The prompt — what Claude reads (required)
  README.md       # Human docs: purpose, usage, examples
  evals/          # Test cases for this skill
    eval-*.md     # Individual eval scenarios
```

## Catalog

See [catalog.md](catalog.md) for a searchable index of all production-ready skills.
