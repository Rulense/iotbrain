---
name: brain-distill
description: Use after an edge-IoT learning has been VERIFIED on real hardware — a fix confirmed working, a recipe run end-to-end, a config proven, a gotcha reproduced. Distills it into an iotbrain entry, saves it locally, and (with explicit user approval only) opens a community PR.
---

# Brain Distiller

Turn one verified learning into one brain entry. Never batch multiple learnings
into one entry.

## Step 1 — Dedup check

Grep the shipped brain (`${CLAUDE_PLUGIN_ROOT}/brain/` — `${CLAUDE_PLUGIN_ROOT}`
is the env var Claude Code sets to the plugin's install root) and the local overlay
(`~/.iotbrain/local/`) for the entry's would-be keys. If an existing entry
covers the same knowledge, prepare an UPDATE to that file (extend
`platform_versions` ranges, revise steps, or set the old entry
`status: outdated` with the version
boundary noted in its Gotchas) instead of creating a duplicate.

## Step 2 — Draft the entry

Use the exact template from CONTRIBUTING.md (plugin root). Choose ONE `type`:
`recipe` | `config` | `matrix` | `gotcha` | `fix`. Requirements:
- `keys`: VERBATIM strings — exact error text, package names, GStreamer element
  names. Never paraphrase. PLUS at least one plain-language symptom phrase
  (lowercase, 2-6 words) as a user would say it, e.g. "camera not detected".
- `company`: the device vendor — `nvidia` for Jetson work.
- `platform_versions`/`devices`: from the device facts collected this session.
- `status: verified` + `verified_on: "<device>, JetPack <ver>, <today>"` — this
  skill only runs for verified learnings.
- `sources`: URLs used, or "verified locally" context in the body.

SCRUB before writing — mechanical pass first, then manual:
1. Run the auto-scrubber on the draft and review its stderr redaction report
   (one line per redaction):
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/brain-distill/scripts/scrub.py" < draft.md
```
2. Then the manual scrub pass — the mechanical scrub is a floor, not a
   replacement: remove usernames, private paths, hostnames, IPs, tokens,
   company-internal references, proprietary code. Replace with placeholders
   like `<project-dir>`.

## Step 3 — Save to the local overlay immediately

If `~/.iotbrain/local/` is missing, initialize it first:
`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/init_overlay.py"`.

```bash
mkdir -p ~/.iotbrain/local/<domain>
# write the entry file there
```
The knowledge is now retrievable in future sessions regardless of what happens next.

## Step 4 — User approval gate (MANDATORY)

Show the user the COMPLETE entry content, then ask exactly one question:
"Contribute this entry to the public iotbrain repo as a PR?"
- Never open a PR, push, fork, or publish without an explicit yes to the shown
  content. If the user edits it, show the final version again.
- If no: stop here. The entry stays in the local overlay. Do not ask again.

## Step 5 — Open the PR (only after approval)

`<brain-repo-url>` below resolves to the public iotbrain repo URL once it is
published.

```bash
workdir=$(mktemp -d)
gh repo fork <brain-repo-url> --clone -- "$workdir/iotbrain" \
  || git clone <your-fork-url> "$workdir/iotbrain"
cd "$workdir/iotbrain"
git checkout -b brain/<domain>-<slug>
# copy entry to brain/<domain>/<slug>.md
# add the INDEX.md line: - [<title>](<domain>/<slug>.md) — <type> · <version scope> · <hook>
python3 scripts/lint_brain.py brain        # must pass before committing
git add brain/
git commit -m "brain(<domain>): <title>"
git push -u origin brain/<domain>-<slug>
gh pr create --title "brain(<domain>): <title>" \
  --body "$(cat <<'EOF'
## New brain entry
<one-paragraph summary from the entry's Context>

- Type: <type> · Platform versions: <range> · Devices: <list>
- Verified on: <verified_on>
- [ ] Lint passes (`python3 scripts/lint_brain.py brain`)
EOF
)"
```

If `gh` is missing or unauthenticated: tell the user the entry is saved at
`~/.iotbrain/local/<domain>/<slug>.md` and give them the repo URL to
contribute manually. Do not attempt workarounds.
