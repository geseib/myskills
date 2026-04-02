# CLAUDE.md

This is a **skills repository** — a personal library for building, testing, and sharing Claude Code skills across multiple projects.

## Two types of skills in this repo

**Repo operational skills** (`.claude/skills/`) — govern HOW you work in this repo. These are auto-loaded by Claude Code and enforce processes like eval methodology and dashboard management. They are NOT the product of this repo — they are the tooling.

**Subject skills** (`drafts/` and `skills/`) — the actual skills being developed, tested, and shared. These are the product of this repo. They go through the lifecycle: drafts/ → eval → skills/ → other projects.

Do not confuse these. Operational skills tell you how to build and test subject skills. Subject skills are what you ship to other projects.

## Repo layout

```
.claude/skills/          # Repo operational skills (auto-loaded by Claude Code)
  eval-methodology/
    SKILL.md             # How to run fair, accurate evals
  dashboard-management/
    SKILL.md             # How to manage the dashboard and results
  eval-rebase/
    SKILL.md             # How to handle eval versioning and lineage
skills/                  # Production-ready subject skills, each in its own folder
  <skill-name>/
    SKILL.md             # The skill prompt (required, with YAML frontmatter)
    README.md            # Docs: purpose, usage, examples
    evals/               # Eval cases specific to this skill
drafts/                  # WIP: experiments, imports being adapted, new ideas
  <skill-name>/          # Same folder structure as skills/
    versions/            # Archived previous skill versions (v1.md, v2.md, etc.)
evals/                   # Cross-cutting eval utilities and guides
templates/               # Starter templates for new skills
  basic/                 # Minimal skill scaffold
  user-invocable/        # For slash-command style skills
  auto-trigger/          # For context-triggered skills
eval-results/            # Eval result data (JSONL per skill)
  <skill-name>/
    results.jsonl        # Append-only log of all eval runs
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
 │  - Iterate on SKILL.md                              │
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
 │  - Or copy SKILL.md into project's .claude/skills/  │
 │  - Improvements flow back here                      │
 └─────────────────────────────────────────────────────┘
```

## Conventions

- Every skill lives in its own folder with at minimum a `SKILL.md` file (with YAML frontmatter containing `name:` and `description:`)
- New skills start in `drafts/`, move to `skills/` once tested and reliable
- Skill prompts go in `SKILL.md`, documentation in `README.md`
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

## Skill development process

This is the end-to-end workflow for building, evaluating, and shipping a skill. Follow these steps in order.

### Phase 1: Create the skill

1. **Scaffold** — create `drafts/<skill-name>/` with `SKILL.md`, `README.md`, and `evals/`
2. **Write SKILL.md** with this structure:
   - YAML frontmatter with `name:` and `description:` fields
   - `<!-- skill-version: v1 -->` version tag (below frontmatter)
   - Clear trigger conditions (when to use / when not to use)
   - **Ordered methodology** — a step-by-step process the model must follow (e.g., "Step 1: Threat model FIRST"). This is where skills add the most value — enforcing a consistent methodology that smaller models skip.
   - Concrete code patterns with CORRECT and WRONG examples
   - Anti-patterns to avoid (numbered list)
   - Required output format
3. **Write README.md** — purpose, key principles, sources/influences, eval case summary

### Phase 2: Write eval cases

Create eval files in `drafts/<skill-name>/evals/eval-<type>-<name>.md`:

- **happy-path** evals (2-3): straightforward tasks the skill should ace on all models
- **edge-case** evals (3-4): nuanced scenarios that test specific skill patterns
- **adversarial** evals (1-2): prompts that tempt the model to skip the methodology

Each eval has: prompt, expected behavior (checkbox criteria), "should NOT" list, pass criteria summary.

### Phase 3: Run multi-model evals

Run evals across **three model tiers** to measure where the skill adds value:

| Model | Purpose |
|-------|---------|
| Opus | Ceiling — should score 100% with or without skill |
| Sonnet | Main target — skill should help on edge cases |
| Haiku | Floor — skill should show the most contrast vs baseline |

For each model, run:
1. **With skill** — all eval cases (model reads SKILL.md, then responds to the prompt)
2. **Baseline** (without skill) — 3 representative evals (1 happy-path, 1 edge-case, 1 adversarial) to measure native model capability

**CRITICAL: Separate generation from grading.** See `.claude/skills/eval-methodology/SKILL.md` for the full protocol. Key rules:

- **Generation prompt must NOT include eval criteria.** If the model sees "SELF-EVALUATE against: 1. uses Zod, 2. uses helmet..." it will treat the criteria as requirements and inflate scores. Send only the task prompt.
- **Grade in a separate pass.** After the model generates code, evaluate the output against criteria in a separate agent/conversation. The grader reads the generated code and scores it — the generator never sees the rubric.
- **Version comparisons require complete coverage.** If v1 ran 7 evals, v2 must run the same 7 evals before comparing. The dashboard will flag incomplete coverage with ⚠️.
- **Cost-aware tiebreaking.** When models score equally, the cheaper model gets the ⭐ (score first, cost as tiebreaker).

### Phase 4: Record results

Append results to `eval-results/<skill-name>/results.jsonl`:

```json
{
  "eval_id": "happy-path-rest-api",
  "run_id": "2026-04-01T12:00:00Z",
  "skill_version": "v1",
  "skill_commit": "abc1234",
  "model": "claude-sonnet-4-6",
  "with_skill": true,
  "eval_set_version": "v1",
  "score": "9/11",
  "overall": "pass",
  "notes": "Missed rate limiting on one endpoint."
}
```

Fields: `eval_id`, `run_id` (ISO timestamp), `skill_version` (from frontmatter or "baseline"), `skill_commit`, `model`, `with_skill` (true/false), `eval_set_version`, `score` (X/Y), `overall` (pass/partial/fail), `notes`.

### Phase 5: Regenerate dashboard

```bash
python3 scripts/generate-dashboard.py
```

This reads all `eval-results/*/results.jsonl` files and generates `dashboard.md` with:
- Overview table (skill, status, version, rating, eval count, vs baseline)
- Per-skill sections with version history, individual eval results
- **Cross-model comparison table** (Opus vs Sonnet vs Haiku scores per eval)
- Baseline comparison (with-skill vs without-skill per model)

### Phase 6: Iterate or promote

- If scores are low → revise `SKILL.md`, bump version tag (`v2`), re-run evals
- If passing on all models → promote from `drafts/` to `skills/`, add to `catalog.md`
- Version history is automatically tracked in the dashboard

### Versioning

- Version tag in `SKILL.md`: `<!-- skill-version: v1 -->` (below YAML frontmatter)
- Bump version when changing the skill content, then re-run evals
- Results JSONL captures `skill_version` per result — dashboard shows trends across versions
- Never delete old results — they form the version history
- **Archive previous versions:** When bumping from v1→v2, copy the old SKILL.md to `versions/v1.md`. This allows re-running old version evals without git checkout:

```
drafts/<skill-name>/
  SKILL.md              ← always the latest version
  versions/
    v1.md               ← frozen copy of v1
    v2.md               ← frozen copy of v2 (after v3 is created)
  evals/
```

## Working in this repo

- When asked to **create** a skill: follow Phase 1-2 above
- When asked to **eval** a skill: follow Phase 3-5 above
- When asked to **import** a skill: place in `drafts/`, adapt format, then eval
- When asked to **promote** a skill: move from `drafts/` to `skills/`, update `catalog.md`
- When asked to **deploy** a skill to a project: provide the settings.json config or copy instructions
- When asked to **dashboard** or show skill status: run `python3 scripts/generate-dashboard.py` then show dashboard.md
- After running evals: always append results to `eval-results/<skill>/results.jsonl` and regenerate the dashboard
