<!-- eval-version: v1 -->
<!-- eval-notes: v1=Original criteria for worktree-specific context divergence detection -->
# Eval: Worktree Context Divergence

**Skill:** `context-audit`
**Type:** edge-case

## Setup

The user is working in a git worktree where CLAUDE.md has been modified differently from the main working tree:
- Main tree: `/home/user/project/` with CLAUDE.md containing "ALWAYS use TypeScript"
- Worktree: `/home/user/project-feature/` with CLAUDE.md containing "NEVER use TypeScript, use JavaScript"
- The worktree has an additional skill in `.claude/skills/` not present in main

## Prompt

```
/context-audit
```

## Expected behavior

- [ ] Detects that the current project is a git worktree (not the main working tree)
- [ ] Reports the path to the main working tree
- [ ] Notes that CLAUDE.md may differ from the main tree's version
- [ ] Flags the directive contradiction if both versions are readable
- [ ] Notes additional skills present only in the worktree
- [ ] Includes worktree status in the report header

## Should NOT

- Assume worktree and main tree always have identical configs
- Skip worktree detection (the user might not know they're in a worktree)
- Only check the worktree's files without acknowledging the main tree
- Ignore the potential for divergent CLAUDE.md content

## Pass criteria

At least 5/6 expected behaviors checked. The report explicitly identifies worktree status and flags potential configuration divergence. The user should understand that their context may differ from what they'd get in the main working tree.
