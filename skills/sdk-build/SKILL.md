---
name: sdk-build
description: Use for building, compiling, and packaging software for edge targets — native vs cross-compilation decisions, toolchain and sysroot setup, ARM/aarch64 and GPU architecture flags, Python wheels for ARM boards, packaging apps as containers, and surviving big builds on-device. Covers boards like NVIDIA Jetson (L4T/aarch64), Raspberry Pi, and other ARM edge targets. Consults the iotbrain before and during the work and distills verified learnings back.
---

# Edge SDK & Build Companion

Compiling and packaging for edge targets without losing days to the wrong
toolchain, wheel, or base image. The stable procedure lives here;
version-specific knowledge lives in the iotbrain at
`${CLAUDE_PLUGIN_ROOT}/brain/` and the user's overlay at `~/.iotbrain/local/`.
Follow the steps in order.

## Step 1 — Device facts first

If the target board, vendor, and OS/SDK version are not already established
this session, run `iot-dev` Step 1 to collect them — never guess. Then add
the build facts: where the build will run (on-device or host), host arch and
OS if cross-building, compiler/CMake/Python versions involved, and the
device's RAM, swap, and free storage if building on it.

## Step 2 — Consult the brain BEFORE building

Grep the `sdk-dev/` and `runtime/` domains in both stores for toolchain
terms, package names, and (when a build fails) VERBATIM compiler/linker
errors — `cannot find -l…`, `no kernel image`, `Killed`:

```bash
grep -ril "sysroot\|CROSS_COMPILE\|wheel\|gencode\|buildx" \
  "${CLAUDE_PLUGIN_ROOT}/brain/sdk-dev/" "${CLAUDE_PLUGIN_ROOT}/brain/runtime/" \
  ~/.iotbrain/local/ 2>/dev/null
```

Read every hit, filter by `company` + version exactly as iot-dev Step 3
describes, and surface matching `gotcha` entries BEFORE the stage that would
hit them — a doomed pip install or wrong base image is cheapest to catch
before it starts.

## Step 3 — The build playbook

1. **Native or cross?** Default to native on-device for small-to-medium
   builds: the sysroot is correct by construction and ABI surprises vanish.
   Go cross (or emulated CI) when the build outgrows the device's RAM or
   hours, when you target many boards, or when the device can't host a
   toolchain. Before abandoning native, apply the survival recipe (stage 6).
2. **Toolchain & sysroot (cross path).** Use an aarch64 toolchain matched to
   the target's OS release and glibc, and a sysroot cloned from the REAL
   target rootfs (or the vendor's sample rootfs) — never the host's headers.
   The brain's Jetson recipe (Bootlin toolchain + L4T sysroot) is the worked
   example. Link against the target's vendor lib dirs; their locations and
   renames are brain knowledge (see the nvbuf_utils linking fix).
3. **Architecture flags.** CPU: `-mcpu` for the exact core when performance
   matters, plain aarch64 baseline for portability. GPU/accelerator arch must
   match the module exactly — a wrong CUDA gencode fails only at first kernel
   launch. Take per-module values from the brain's matrix entry
   (`sdk-dev/cuda-arch-gencode-flags-per-module.md`); never recite sm numbers
   from memory.
4. **Python wheels for ARM.** Before any `pip install`, confirm a matching
   aarch64 wheel exists for the exact CPython tag — no match means pip
   silently builds from source for hours. The brain's gotcha covers the traps
   (piwheels serves 32-bit only). Accelerator wheels come from vendor
   indexes, not PyPI — the brain's `ml-stack/` `config` entries name the
   working indexes per platform release. Pin what works in a constraints file.
5. **Containers as packaging.** Build multi-arch with buildx/QEMU, or build
   on-device when the vendor base image requires it. The base image must
   match the device's BSP/driver userspace — the brain's gotcha: since
   JetPack 5, l4t-base no longer mounts CUDA from the host, so CUDA belongs
   in the image. For ML stacks, prebuilt vendor container ecosystems (the
   brain's jetson-containers recipe) beat resolving dependencies by hand.
6. **On-device build survival.** Big builds OOM-kill compilers and throttle.
   The brain's recipe: swap on fast storage (not zram) sized for the build,
   zram off, power mode and clocks maxed, `-j` capped below the core count —
   and watch thermals on long builds (`runtime/` entries).

Verify the artifact on the target itself: import the wheel, run the binary,
launch the container — a clean build on the host proves nothing yet.

## Step 4 — Defer to specific skills

When a more specific installed skill covers the doing, use it:
`jetson-package` for Jetson-compatible containers and PyPI indexes,
`espdl-operator` / `espdl-quantize` for ESP-DL operator and model builds,
`devicetree` / `hardware-io` for Zephyr targets, and the upstream sets
catalogued in `SKILLS-CATALOG.md` (Qualcomm's aarch64 build skill, the Yocto
skill sets) for their ecosystems. Consult the brain first either way — Steps
2–3 tell you which knowledge applies to this device before the specialist acts.

## Step 5 — Distill verified learnings

When something new was VERIFIED on the actual target — a cross-build that ran
on the device, a wheel combination that imported cleanly, a container that
started with the accelerator visible — invoke the `brain-distill` skill.
Distill working toolchain/sysroot setups as `recipe` entries and known-good
version pairings as `config`/`matrix` entries, not just debug fixes.
