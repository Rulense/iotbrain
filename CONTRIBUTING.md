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
keys:                       # verbatim grep targets — error strings, package names, element names
  - "<exact string an agent would search for>"
platform_versions: ["JetPack 6.1", "L4T 36.x"]   # platform/SDK version scope, or ["all"]
devices: [orin-nano]        # orin-nano | orin-nx | agx-orin | xavier-nx | agx-xavier | nano | agx-thor | all
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
2. **Has verbatim keys** — copy-paste the exact error text / package / element names. Paraphrased keys break grep retrieval.
3. **Is version-scoped** — `platform_versions`, `devices` filled honestly. Each `platform_versions` string is `"<Ecosystem> <range>"` (e.g. `"JetPack 6.x"`, `"ESP-IDF 5.3"`, `"Zephyr 3.7"`). "Works everywhere" claims need `["all"]` and a reason in Context.
4. **Cites sources** — forum thread, GitHub issue, doc page, or "verified locally" plus your `verified_on`.
5. **Is public-safe** — no internal info, secrets, private paths, hostnames, or proprietary code.

## PR checklist

- [ ] `python3 scripts/lint_brain.py brain` passes locally
- [ ] Entry is in the correct domain directory
- [ ] INDEX.md line added
- [ ] Keys are verbatim, not paraphrased
- [ ] Sources linked

CI runs the same lint on every PR.
