# Contributing to Jetson Brain

The brain only gets smarter if verified knowledge flows back. Two ways to contribute: let the `brain-distill` skill draft an entry + PR for you, or write one by hand using the template below.

## Entry template

One markdown file per entry, in the matching domain directory
(`setup/`, `ml-stack/`, `vision/`, `iot/`, `sdk-dev/`, `runtime/`).
Filename: short kebab-case slug, e.g. `pytorch-wheel-libcudnn-import-error.md`.

```markdown
---
title: <one line, specific, includes key terms>
type: recipe | config | matrix | gotcha | fix     # pick ONE
keys:                       # verbatim grep targets — error strings, package names, element names
  - "<exact string an agent would search for>"
jetpack: ["6.1"]            # applicable JetPack versions, or ["all"]
l4t: ["36.x"]               # applicable L4T versions, or ["all"]
devices: [orin-nano]        # orin-nano | orin-nx | agx-orin | xavier-nx | agx-xavier | nano | agx-thor | all
status: verified | unverified | outdated
verified_on: "<device>, JetPack <ver>, <YYYY-MM-DD>"   # required when status: verified
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
- [<title>](<domain>/<slug>.md) — <type> · JP <range> · <one-hook summary>
```

## The verification bar

A PR is mergeable when the entry:

1. **Worked on real hardware** — `status: verified` means you (or the cited thread's author, confirmed resolved) ran it on a physical Jetson. Otherwise use `status: unverified`.
2. **Has verbatim keys** — copy-paste the exact error text / package / element names. Paraphrased keys break grep retrieval.
3. **Is version-scoped** — `jetpack`, `l4t`, `devices` filled honestly. "Works everywhere" claims need `["all"]` and a reason in Context.
4. **Cites sources** — forum thread, GitHub issue, doc page, or "verified locally" plus your `verified_on`.
5. **Is public-safe** — no internal info, secrets, private paths, hostnames, or proprietary code.

## PR checklist

- [ ] `python3 scripts/lint_brain.py brain` passes locally
- [ ] Entry is in the correct domain directory
- [ ] INDEX.md line added
- [ ] Keys are verbatim, not paraphrased
- [ ] Sources linked

CI runs the same lint on every PR.
