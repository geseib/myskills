# CLAUDE.md

This is a **skills repository** — a personal library for building, testing, and sharing Claude Code skills across multiple projects.

## Repo layout

```
skills/                  # Production-ready skills, each in its own folder
  <skill-name>/
    skill.md             # The skill prompt (required)
    README.md            # Docs: purpose, usage, examples
    evals/               # Eval cases specific to this skill
drafts/                  # WIP: experiments, imports being adapted, new ideas
  <skill-name>/          # Same folder structure as skills/
evals/                   # Cross-cutting eval utilities and guides
templates/               # Starter templates for new skills
  basic/                 # Minimal skill scaffold
  user-invocable/        # For slash-command style skills
  auto-trigger/          # For context-triggered skills
catalog.md               # Index of all production skills with tags and summaries
dashboard.md             # Auto-generated eval dashboard (run scripts/generate-dashboard.py)
scripts/
  generate-dashboard.py  # Reads eval-results/ JSONL, outputs dashboard.md
```

## Skill lifecycle

```
 ┌─────────────────────────────────────────────────────┐
 │  SOURCES                                            │
 │  - New idea → templates/ → drafts/                  │
 │  - Import from another project → drafts/            │
 │  - External/community skill → drafts/               │
 └──────────────────────┬──────────────────────────────┘
                        ▼
 ┌─────────────────────────────────────────────────────┐
 │  drafts/<skill-name>/                               │
 │  - Iterate on skill.md                              │
 │  - Write evals, test against them                   │
 │  - Refine until it reliably does what you want      │
 └──────────────────────┬──────────────────────────────┘
                        ▼
 ┌─────────────────────────────────────────────────────┐
 │  skills/<skill-name>/                               │
 │  - Promoted after passing evals                     │
 │  - Listed in catalog.md                             │
 │  - Available for use in other projects              │
 └──────────────────────┬──────────────────────────────┘
                        ▼
 ┌─────────────────────────────────────────────────────┐
 │  OTHER PROJECTS                                     │
 │  - Reference via path in project settings.json      │
 │  - Or copy skill.md into project's .claude/skills/  │
 │  - Improvements flow back here                      │
 └─────────────────────────────────────────────────────┘
```

## Conventions

- Every skill lives in its own folder with at minimum a `skill.md` file
- New skills start in `drafts/`, move to `skills/` once tested and reliable
- Skill prompts go in `skill.md`, documentation in `README.md`
- Keep skills focused — one clear purpose per skill
- When importing from another project, drop in `drafts/` first to adapt and test
- When a skill is promoted to `skills/`, add it to `catalog.md`
- Tag skills in catalog.md for easy discovery (e.g., `code-quality`, `git`, `testing`)

## Connecting to other projects

To use a skill from this repo in another project, add to that project's `.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Read(~/myskills/skills/**)"
    ]
  }
}
```

And reference it in the project's CLAUDE.md or `.claude/skills/` directory.

## Working in this repo

- When asked to **create** a skill: scaffold in `drafts/` using a template
- When asked to **import** a skill: place in `drafts/`, adapt for personal conventions
- When asked to **eval** a skill: run its eval cases, report pass/fail
- When asked to **promote** a skill: move from `drafts/` to `skills/`, update `catalog.md`
- When asked to **deploy** a skill to a project: provide the settings.json config or copy instructions
- When asked to **dashboard** or show skill status: run `python3 scripts/generate-dashboard.py` then show dashboard.md
- After running evals: append results to `eval-results/<skill>/results.jsonl` and regenerate the dashboard
