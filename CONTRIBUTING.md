# Contributing to iotbrain

The brain only gets smarter if verified knowledge flows back. Two ways to contribute: let the `brain-distill` skill draft an entry + PR for you, or write one by hand using the template below.

## Entry template

One markdown file per entry, in the matching domain directory
(`setup/`, `ml-stack/`, `vision/`, `iot/`, `sdk-dev/`, `runtime/`).
Filename: short kebab-case slug, e.g. `pytorch-wheel-libcudnn-import-error.md`.

```markdown
---
title: <one line, specific, includes key terms>
type: recipe | config | matrix | gotcha | fix     # pick ONE
company: nvidia             # device vendor: nvidia | raspberry-pi | qualcomm | nxp | ...
keys:                       # BOTH kinds required (≥2 keys, lint-enforced):
  - "<exact string an agent would search for>"    # verbatim — error strings, package names, element names
  - "<plain-language symptom phrase>"             # how a human/agent would describe it, lowercase, 2-6 words
platform_versions: ["JetPack 6.1", "L4T 36.x"]   # platform/SDK version scope, or ["all"]
devices: [orin-nano]        # vendor-appropriate slugs — e.g. jetson: orin-nano | orin-nx | agx-orin | xavier-nx | agx-xavier | nano | agx-thor; raspberry-pi: pi-5 | pi-4 | pi-zero-2w | pico-2; or all
status: verified | unverified | outdated
verified_on: "<device>, JetPack <ver>, <YYYY-MM-DD>"   # required when status: verified
reproduced_by: ["<who/context>, <device>, <version>, <YYYY-MM-DD>"]   # optional second confirmations
sources: ["https://..."]    # forum threads, docs, release notes
---
## Context
When this applies / what you were trying to do.

## Knowledge
The recipe steps / working config / version matrix / trap / root cause and fix.
Exact commands. For a `fix`, use subheadings "Root cause" and "Fix".

## Verify
How to confirm it worked (or still holds).

## Gotchas
Near-miss variants, what makes it recur. (Optional but encouraged.)
```

After adding an entry, add one line to `brain/INDEX.md`:

```
- [<title>](<domain>/<slug>.md) — <type> · <version scope> · <one-hook summary>
```

`<version scope>` is a shorthand of the entry's `platform_versions` (e.g.
`JP 6.x` for JetPack entries, `ESP-IDF 5.3`, or `all`).

## The verification bar

A PR is mergeable when the entry:

1. **Worked on real hardware — or doc-verified** — `status: verified` means you (or the cited thread's author, with the resolution confirmed) ran it on a physical Jetson, OR the behavior is stated by current official NVIDIA documentation — in that case cite the doc page in `sources` and use a `verified_on` of the form `"doc checked <YYYY-MM-DD>"`. Otherwise use `status: unverified` — the honest fallback.
2. **Has both kinds of keys** — every entry carries BOTH verbatim machine strings (copy-paste the exact error text / package / element names — paraphrased keys break grep retrieval) AND at least one plain-language symptom phrase as a human or agent would describe the problem ("camera not detected", "build runs out of memory", "boot hangs after flash"): lowercase, 2-6 words, genuinely searchable, not a duplicate of a verbatim key. Minimum 2 keys per entry (lint-enforced).
3. **Is version-scoped** — `platform_versions`, `devices` filled honestly. Each `platform_versions` string is `"<Ecosystem> <range>"` (e.g. `"JetPack 6.x"`, `"ESP-IDF 5.3"`, `"Zephyr 3.7"`). "Works everywhere" claims need `["all"]` and a reason in Context.
4. **Cites sources** — forum thread, GitHub issue, doc page, or "verified locally" plus your `verified_on`.
5. **Is public-safe** — no internal info, secrets, private paths, hostnames, or proprietary code.

## PR checklist

- [ ] `python3 scripts/lint_brain.py brain` passes locally
- [ ] Entry is in the correct domain directory
- [ ] INDEX.md line added
- [ ] Keys: verbatim strings (not paraphrased) plus at least one symptom phrase
- [ ] Sources linked

CI runs the same lint on every PR. `brain/KEYWORDS.md` is generated from the
entries' keys by `scripts/gen_updates.py` — rerun it after adding or editing
an entry so the committed map stays fresh (CI checks staleness).

## Scaling the INDEX

`brain/INDEX.md` is deliberately a single flat file — cheapest possible scan
for agents. That holds up to roughly 250 entries; past that, scanning cost and
merge-conflict rate outweigh the one-file convenience.
`scripts/gen_updates.py --check` prints a WARNING (CI stays green) once the
entry count crosses 250. When it trips, execute this split:

1. Create `brain/<domain>/INDEX.md` per domain, moving each domain's lines
   over unchanged (same one-line format).
2. Reduce the top-level `brain/INDEX.md` to a table of contents: one line per
   domain linking its INDEX plus the domain's entry count.
3. Teach `check_index` in `scripts/lint_brain.py` to read the per-domain
   INDEX files, and update the INDEX instructions here and in the
   `iot-dev` / `brain-distill` skills.
