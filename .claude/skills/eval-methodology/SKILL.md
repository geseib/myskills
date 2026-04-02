---
name: eval-methodology
description: Ensures skill evaluations produce fair, comparable results across models and versions. Governs how evals are run, graded, and recorded in this repo.
user-invocable: false
---

# Eval Methodology

Ensure skill evaluations produce fair, comparable results across models and versions. This skill governs HOW evals are run in this repo.

## When to use

TRIGGER when:
- Running evals for any skill (with-skill or baseline)
- Comparing results across skill versions
- Comparing results across models
- Reviewing dashboard accuracy
- Someone asks to "eval", "test", or "benchmark" a skill

## Core principles

1. **Separate generation from grading** — the model being tested must NEVER see the eval criteria during generation
2. **Same evals across versions** — you cannot compare v1 to v2 unless they ran the same eval cases
3. **Same evals across models** — cross-model comparisons require identical eval sets
4. **Cost-aware tiebreaking** — when models score equally, the cheaper model wins
5. **Score what was actually tested** — don't extrapolate from partial coverage

## Eval execution protocol

### Step 1: Generate the response (NO criteria visible)

The prompt sent to the model must contain ONLY:
- The task description (what to build)
- Any context the skill would normally provide (for with-skill runs)
- A request to produce a complete solution

**NEVER include** in the generation prompt:
- The eval criteria or rubric
- The scoring dimensions
- Hints about what will be graded
- "SELF-EVALUATE against these criteria"

WRONG — criteria leaked into prompt:
```
Build an Express API for task management.
After responding, SELF-EVALUATE against these 11 criteria:
1. threat_model — starts with or mentions threat model
2. input_validation — uses Zod/Joi
...
```

RIGHT — clean generation prompt:
```
Build an Express API for task management. Users can:
- Register with email and password
- Login and get a session/token
- Create, list, complete, and delete tasks
Use PostgreSQL for storage.
```

### Step 2: Grade in a separate pass

After the model generates its response, evaluate the output against criteria in a SEPARATE agent or conversation. The grader:
- Reads the generated code
- Scores it against the eval criteria
- Never shares context with the generator

The grader can be:
- A separate agent that reads the generated output and scores it
- Manual review against the rubric
- The same model in a NEW conversation given only the output to grade

### Step 3: Record results

Append to `eval-results/<skill>/results.jsonl` with all required fields:
- `eval_id`, `run_id` (ISO timestamp), `skill_version` (from frontmatter or "baseline"), `skill_commit`, `model`, `with_skill` (true/false), `score` (X/Y), `overall` (pass/partial/fail), `notes`

## Version comparison rules

### Complete coverage required

A version comparison is only valid when:
- Both versions ran the **same set of eval_ids**
- Both versions ran on the **same set of models**

If v2 only ran 4 of 7 evals from v1, the dashboard will:
- Flag the comparison as incomplete (⚠️)
- List which evals are missing

### How to run a fair version comparison

1. Identify all eval_ids from the previous version's results
2. Run ALL of them on the new version
3. Run on the SAME models as the previous version
4. Only then calculate and compare percentages

## Baseline (without-skill) rules

### Clean separation

Baseline runs measure what the model does WITHOUT the skill. They must:
- Use the EXACT same task prompt as the with-skill run
- NOT include the SKILL.md content
- NOT include eval criteria in the prompt
- Be graded by a separate agent/pass using the eval criteria

### Representative sampling

Run baselines on at least:
- 1 happy-path eval
- 1 edge-case eval
- 1 adversarial eval

Per model being compared.

## Red flags to watch for

- A cheaper model outscoring an expensive one on baselines (may indicate criteria leakage)
- A version showing improvement but with fewer evals (cherry-picked results)
- Baseline scores of 100% across all models (criteria may have been in the prompt)
- Large score swings between runs of the same model+eval (eval may be ambiguous)

## Anti-patterns

1. **Criteria in generation prompt** — leaks the rubric, inflates baseline scores
2. **Partial version coverage** — comparing v2 (4 evals) to v1 (7 evals) is misleading. See `eval-rebase.md` for the protocol when evals change
3. **Single-model testing** — can't claim a skill "works" from one model's results
4. **Self-grading** — the model grading its own output tends to be generous; use separate grading
5. **Ignoring cost** — a skill that only helps Opus isn't useful if Haiku can do it natively
6. **Reusing agent artifacts** — eval agents that write files can pollute the repo; use temp dirs and .gitignore
