# Publishing the eval skills to the marketplace + catalog

This directory holds 3 ready-to-ship plugins:
- `eval-methodology/`
- `eval-rebase/`
- `dashboard-management/`

They need to land in **geseib/seibtribemarket** (the marketplace) and be reflected
in **geseib/plugs** (the catalog SPA). The session where they were prepared was
write-scoped to `geseib/myskills` only, so the pushes must happen from a session
scoped to include `seibtribemarket` and `plugs`.

## Target branch: `main` for BOTH repos

The changes must end up on `main` in both `seibtribemarket` and `plugs`:

- `claude plugin marketplace add geseib/seibtribemarket` reads the **default
  branch** (`main`) — plugins are only installable once they're on `main`.
- The catalog page (`index.html` + `data.js`) is served from `main` — the new
  skills only show once `data.js` is on `main`.

If this session assigns a designated `claude/...` working branch (Claude Code on
the web often does), let the work land there and then **merge each PR into `main`**
— one PR per repo. If direct commits to `main` are allowed, push straight to `main`.
Either way, the end state is: changes on `main` in both repos.

(`myskills` is unaffected — it only holds these reference files on its own branch.)

## Fast path — copy the ready-made reference files

`_reference/` holds the exact final artifacts, already built and validated:

- `_reference/marketplace.json` → copy to `seibtribemarket/.claude-plugin/marketplace.json` (11 plugins)
- `_reference/seibtribemarket-README.md` → copy to `seibtribemarket/README.md`
- `_reference/data.js` → copy to `plugs/data.js` (catalog showing only seibtribemarket, 11 plugins incl. the 3 new eval skills)

Plus copy the 3 plugin folders (`eval-methodology/`, `eval-rebase/`,
`dashboard-management/`) into `seibtribemarket/plugins/`. Then commit + push both
repos to `main`. That's the whole job — the detailed steps below are the manual
equivalent if you'd rather rebuild than copy.

---

## Steps for a session scoped to seibtribemarket + plugs (+ myskills)

### 1. Add the 3 plugins to seibtribemarket

Copy the 3 plugin folders from `myskills/marketplace-export/` into
`seibtribemarket/plugins/` (drop `PUBLISH.md` — it doesn't belong in the marketplace):

```
plugins/eval-methodology/{SKILL.md,README.md,.claude-plugin/plugin.json}
plugins/eval-rebase/{SKILL.md,README.md,.claude-plugin/plugin.json}
plugins/dashboard-management/{SKILL.md,README.md,.claude-plugin/plugin.json}
```

### 2. Append 3 entries to seibtribemarket/.claude-plugin/marketplace.json

Add these objects to the `plugins` array (after `vote-overlay`):

```json
{
  "name": "eval-methodology",
  "source": "./plugins/eval-methodology",
  "description": "Fair, reproducible skill evaluations across models and versions. Separates generation from grading, enforces complete coverage, and uses cost-aware tiebreaking.",
  "version": "1.0.0",
  "author": { "name": "myskills" },
  "category": "skill",
  "keywords": ["eval", "testing", "benchmarking", "multi-model", "methodology"]
},
{
  "name": "eval-rebase",
  "source": "./plugins/eval-rebase",
  "description": "Eval versioning and consistency enforcement. Tracks eval lineage so every score is traceable to the exact criteria, skill version, and model that produced it.",
  "version": "1.0.0",
  "author": { "name": "myskills" },
  "category": "skill",
  "keywords": ["eval", "versioning", "lineage", "consistency", "methodology"]
},
{
  "name": "dashboard-management",
  "source": "./plugins/dashboard-management",
  "description": "Auto-generated eval dashboard from JSONL results. Shows cross-model comparisons, version history, skill impact vs baseline, and cost-aware best-for-task rankings.",
  "version": "1.0.0",
  "author": { "name": "myskills" },
  "category": "skill",
  "keywords": ["dashboard", "eval", "reporting", "visualization", "methodology"]
}
```

Also add matching bullet lines to `seibtribemarket/README.md` under `## Plugins`.
Validate: `python3 -c "import json;json.load(open('.claude-plugin/marketplace.json'))"`

### 3. Commit + push seibtribemarket (branch `main`)

### 4. Regenerate the plugs catalog

From the `plugs` repo, pointing at the local seibtribemarket clone:

```bash
node scripts/scan.mjs <path-to-seibtribemarket> --source geseib/seibtribemarket --overwrite
```

`--overwrite` replaces the placeholder `claude-plugins-official` demo data so the
catalog shows only the real 11-plugin seibtribemarket. Drop `--overwrite` to keep
both marketplaces in the catalog instead.

### 5. Commit + push plugs (branch `main`)

Result: marketplace has 11 plugins; catalog `data.js` reflects them.
