#!/usr/bin/env bash
# Create-or-update a single pinned tracking issue from a report file.
#
# Usage: TITLE="..." INTRO="..." GH_TOKEN=... upsert_issue.sh <report-file>
#   - report file empty  -> close any matching open issue (resolved), exit 0
#   - report file non-empty -> update the open issue titled $TITLE, else
#     create it and (best-effort) pin it.
set -euo pipefail

report_file="$1"
: "${TITLE:?TITLE env var required}"
: "${INTRO:=}"

repo="${GITHUB_REPOSITORY:?GITHUB_REPOSITORY env var required}"

# Exact-title match among open issues (gh --search does fuzzy matching).
number=$(gh issue list --repo "$repo" --state open --limit 100 \
  --json number,title \
  --jq --arg t "$TITLE" '[.[] | select(.title == $t)][0].number // empty')

if [ ! -s "$report_file" ]; then
  echo "report is empty — nothing lacking coverage"
  if [ -n "$number" ]; then
    gh issue close "$number" --repo "$repo" \
      --comment "Weekly check came back clean — closing." || true
  fi
  exit 0
fi

body_file=$(mktemp)
{
  printf '%s\n\n```\n' "$INTRO"
  cat "$report_file"
  printf '```\n\n_Auto-managed by the `freshness` workflow (last run: %s, [run log](%s/%s/actions/runs/%s))._\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "${GITHUB_SERVER_URL:-https://github.com}" "$repo" "${GITHUB_RUN_ID:-0}"
} > "$body_file"

if [ -n "$number" ]; then
  echo "updating existing issue #$number"
  gh issue edit "$number" --repo "$repo" --body-file "$body_file"
else
  echo "creating issue: $TITLE"
  url=$(gh issue create --repo "$repo" --title "$TITLE" --body-file "$body_file")
  number="${url##*/}"
  # Best-effort pin: keeps the tracking issue at the top of the issue list.
  node_id=$(gh api "repos/$repo/issues/$number" --jq .node_id) || true
  if [ -n "${node_id:-}" ]; then
    gh api graphql \
      -f query='mutation($id: ID!) { pinIssue(input: {issueId: $id}) { issue { number } } }' \
      -f id="$node_id" >/dev/null || echo "pinning failed (non-fatal)"
  fi
fi
