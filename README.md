# My Skills

A personal repo for building, experimenting with, evaluating, and sharing Claude Code skills.

## Structure

```
skills/       # Production-ready skills, each in its own folder
drafts/       # Work-in-progress skills — experiments, imports, rough ideas
evals/        # Evaluation prompts and expected outputs for testing skills
templates/    # Starter templates for new skills
```

## Quick start

### Create a new skill

Copy a template to `drafts/` and start iterating:

```bash
cp -r templates/basic drafts/my-new-skill
```

### Promote a draft to production

Once a skill is tested and ready, move it to `skills/`:

```bash
mv drafts/my-new-skill skills/my-new-skill
```

### Import a skill from another project

Drop it in `drafts/`, adapt it, eval it, then promote.

## Skill folder layout

Each skill folder contains:

- `skill.md` — The skill prompt (required)
- `README.md` — What it does, when to use it, any setup notes
- `evals/` — Optional eval cases specific to this skill

## Using skills

Reference skills from this repo in your projects by adding them to your project's `.claude/settings.json`:

```json
{
  "skills": [
    "/path/to/myskills/skills/my-skill/skill.md"
  ]
}
```

Or symlink individual skills into a project's `.claude/skills/` directory.
