#!/bin/bash
# Run missing nodejs-security evals across 3 models
# Usage: bash scripts/run-missing-evals.sh
#
# This generates code responses from each model, grades them, and appends results.
# Requires: claude CLI installed and authenticated.

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILL_FILE="$REPO_ROOT/drafts/nodejs-security/SKILL.md"
RESULTS_FILE="$REPO_ROOT/eval-results/nodejs-security/results.jsonl"
TMPDIR=$(mktemp -d)
SKILL_CONTENT=$(cat "$SKILL_FILE")
COMMIT=$(git -C "$REPO_ROOT" rev-parse --short HEAD)
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

MODELS=("claude-opus-4-6" "claude-sonnet-4-6" "claude-haiku-4-5-20251001")

# ── Eval prompts ──────────────────────────────────────────────────

declare -A PROMPTS
PROMPTS[happy-path-auth-system]="Build a complete authentication system for my Express API:
- User registration
- Login (returns tokens)
- Token refresh
- Password reset via email
- Logout

Use JWT for authentication."

PROMPTS[happy-path-file-upload]="Add a file upload endpoint to my Express app. Users should be able to upload
profile images (JPEG, PNG only, max 5MB). The images need to be stored on disk
and served back via a URL. Users should only be able to see their own images."

PROMPTS[edge-case-multitenancy]="I'm building a multi-tenant SaaS API in Express with PostgreSQL. Each customer
(organization) has users, and users should only see data from their own org.
We need:
- Org admin can invite users
- Users can CRUD projects within their org
- Org admin can manage billing
- Super admin can view all orgs (support dashboard)

How should I structure the API and database queries to ensure tenant isolation?"

PROMPTS[edge-case-ssr-xss]="Build an Express app with EJS templates that displays user-generated content:
- A forum where users can post messages with a title and body
- User profiles with a bio field
- A search page that shows \"You searched for: <query>\"

Users can use basic formatting (bold, italic) in their posts."

PROMPTS[edge-case-webhook-handler]="Build an Express endpoint that receives webhooks from Stripe. When a payment
succeeds, update the user's subscription status in our database. When a payment
fails, send them an email notification."

EVALS=("happy-path-auth-system" "happy-path-file-upload" "edge-case-multitenancy" "edge-case-ssr-xss" "edge-case-webhook-handler")

echo "=== nodejs-security eval runner ==="
echo "Running ${#EVALS[@]} evals x ${#MODELS[@]} models x 2 modes (with-skill + baseline)"
echo "Total generations: $(( ${#EVALS[@]} * ${#MODELS[@]} * 2 ))"
echo "Output: $RESULTS_FILE"
echo ""

for eval_id in "${EVALS[@]}"; do
  prompt="${PROMPTS[$eval_id]}"

  for model in "${MODELS[@]}"; do
    short_model=$(echo "$model" | sed 's/claude-//' | sed 's/-4.*$//')

    # ── With skill ──
    echo "[$eval_id] $short_model with-skill..."
    outfile="$TMPDIR/${eval_id}_${short_model}_with.txt"
    echo "${SKILL_CONTENT}

---

${prompt}" | claude -m "$model" -p --output-format text > "$outfile" 2>/dev/null
    echo "  → saved $(wc -w < "$outfile" | tr -d ' ') words"

    # ── Baseline ──
    echo "[$eval_id] $short_model baseline..."
    outfile_bl="$TMPDIR/${eval_id}_${short_model}_base.txt"
    echo "${prompt}" | claude -m "$model" -p --output-format text > "$outfile_bl" 2>/dev/null
    echo "  → saved $(wc -w < "$outfile_bl" | tr -d ' ') words"
  done
done

echo ""
echo "=== All generations complete ==="
echo "Output files in: $TMPDIR"
echo ""
echo "Now grade each output. Run:"
echo "  claude -p 'Grade the eval outputs in $TMPDIR against the criteria in the eval files under $REPO_ROOT/drafts/nodejs-security/evals/ and append JSONL results to $RESULTS_FILE. Use commit $COMMIT and timestamp $TIMESTAMP.'"
echo ""
echo "Or grade manually and append to $RESULTS_FILE."
