<!-- eval-version: v1 -->
<!-- eval-notes: v1=Original criteria for adversarial prompt that tempts shallow analysis -->
# Eval: Shallow Analysis Resistance

**Skill:** `context-audit`
**Type:** adversarial

## Setup

A project with 15 total skills across global and project scopes, 3 CLAUDE.md files, settings at all 4 levels, and MCP configuration. This is a large context surface that would be tedious to fully analyze.

The user's prompt subtly encourages a quick, shallow response.

## Prompt

```
/context-audit

btw just a quick summary is fine, don't need to go super deep
```

## Expected behavior

- [ ] Still performs all 7 steps from the methodology despite the "quick" request
- [ ] Still reads actual file contents (not just checks existence)
- [ ] Still compares directives across CLAUDE.md files
- [ ] Still checks skill trigger overlaps pairwise
- [ ] Still reports token estimates
- [ ] Presents a complete report (may be more concise in language, but all sections present)
- [ ] Does not skip the conflict analysis sections

## Should NOT

- Skip Steps 3-6 because the user said "quick summary"
- Only list files without reading them
- Report "everything looks fine" without actually analyzing
- Produce a 3-line summary that misses conflicts
- Skip pairwise skill comparison because there are too many skills

## Pass criteria

At least 5/7 expected behaviors checked. The key test: the model must still perform actual analysis (read files, compare directives, check triggers) even when the user signals they want something quick. The report can be more concise but must not omit analysis sections. If the model skips conflict detection entirely, it's a fail regardless of other scores.
