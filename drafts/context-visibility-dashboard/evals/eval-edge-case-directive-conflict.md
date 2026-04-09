<!-- eval-version: v1 -->
<!-- eval-notes: v1=Original criteria for detecting directive contradictions across CLAUDE.md files -->
# Eval: Directive Contradiction Detection

**Skill:** `context-audit`
**Type:** edge-case

## Setup

A project with contradictory directives across CLAUDE.md files:

`~/.claude/CLAUDE.md`:
```
ALWAYS add comprehensive error handling to every function.
NEVER use abbreviations in variable names.
MUST include JSDoc comments on all public functions.
```

`./CLAUDE.md`:
```
DO NOT add error handling unless explicitly requested - keep code minimal.
ALWAYS use short, concise variable names. Abbreviations are fine.
NEVER add comments unless the logic is non-obvious.
```

Additionally, both a global skill and a project skill have triggers that match "when writing JavaScript functions".

## Prompt

```
/context-audit
```

## Expected behavior

- [ ] Reads both CLAUDE.md files completely (not just headers)
- [ ] Identifies the "error handling" contradiction (ALWAYS add vs DO NOT add)
- [ ] Identifies the "variable naming" contradiction (NEVER abbreviate vs abbreviations fine)
- [ ] Identifies the "comments" contradiction (MUST JSDoc vs NEVER comments)
- [ ] Reports which file takes precedence (project overrides global)
- [ ] Flags that the user may not realize global directives are being overridden
- [ ] Identifies the skill trigger overlap for JavaScript functions
- [ ] Provides specific recommendations for resolving each conflict

## Should NOT

- Report "no conflicts" without actually comparing directive content
- Only check for exact string matches (should understand semantic contradictions)
- Miss contradictions because the wording differs (e.g., "NEVER abbreviate" vs "abbreviations are fine")
- Fail to explain the precedence implications

## Pass criteria

At least 6/8 expected behaviors checked. The model must identify at least 2 of the 3 directive contradictions with specific references to the conflicting lines. Generic "review your files" advice without identifying specific conflicts is a fail.
