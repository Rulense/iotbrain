---
name: brain-distill
description: Use after a Jetson learning has been VERIFIED on real hardware — a fix confirmed working, a recipe run end-to-end, a config proven, a gotcha reproduced. Distills it into a Jetson Brain entry, saves it locally, and (with explicit user approval only) opens a community PR.
---

# Brain Distiller

Turn one verified learning into one brain entry. Never batch multiple learnings
into one entry.

## Step 1 — Dedup check

Grep the shipped brain (`<skill-base-dir>/../../brain/`) and the local overlay
(`~/.jetson-brain/local/`) for the entry's would-be keys. If an existing entry
covers the same knowledge, prepare an UPDATE to that file (extend `jetpack`
ranges, revise steps, or set the old entry `status: outdated` with the version
boundary noted in its Gotchas) instead of creating a duplicate.

## Step 2 — Draft the entry

Use the exact template from CONTRIBUTING.md (plugin root). Choose ONE `type`:
`recipe` | `config` | `matrix` | `gotcha` | `fix`. Requirements:
- `keys`: VERBATIM strings — exact error text, package names, GStreamer element
  names. Never paraphrase.
- `company`: the device vendor — `nvidia` for Jetson work.
- `jetpack`/`l4t`/`devices`: from the device facts collected this session.
- `status: verified` + `verified_on: "<device>, JetPack <ver>, <today>"` — this
  skill only runs for verified learnings.
- `sources`: URLs used, or "verified locally" context in the body.

SCRUB before writing: remove usernames, private paths, hostnames, IPs, tokens,
company-internal references, proprietary code. Replace with placeholders like
`<project-dir>`.

## Step 3 — Save to the local overlay immediately

```bash
mkdir -p ~/.jetson-brain/local/<domain>
# write the entry file there
```
The knowledge is now retrievable in future sessions regardless of what happens next.

## Step 4 — User approval gate (MANDATORY)

Show the user the COMPLETE entry content, then ask exactly one question:
"Contribute this entry to the public Jetson Brain repo as a PR?"
- Never open a PR, push, fork, or publish without an explicit yes to the shown
  content. If the user edits it, show the final version again.
- If no: stop here. The entry stays in the local overlay. Do not ask again.

## Step 5 — Open the PR (only after approval)

```bash
gh repo fork <brain-repo-url> --clone /tmp/jetson-brain-pr 2>/dev/null \
  || git clone <fork-url> /tmp/jetson-brain-pr
cd /tmp/jetson-brain-pr
git checkout -b brain/<domain>-<slug>
# copy entry to brain/<domain>/<slug>.md
# add the INDEX.md line: - [<title>](<domain>/<slug>.md) — <type> · JP <range> · <hook>
python3 scripts/lint_brain.py brain        # must pass before committing
git add brain/
git commit -m "brain(<domain>): <title>"
git push -u origin brain/<domain>-<slug>
gh pr create --title "brain(<domain>): <title>" \
  --body "$(cat <<'EOF'
## New brain entry
<one-paragraph summary from the entry's Context>

- Type: <type> · JetPack: <range> · Devices: <list>
- Verified on: <verified_on>
- [ ] Lint passes (`python3 scripts/lint_brain.py brain`)
EOF
)"
```

If `gh` is missing or unauthenticated: tell the user the entry is saved at
`~/.jetson-brain/local/<domain>/<slug>.md` and give them the repo URL to
contribute manually. Do not attempt workarounds.
