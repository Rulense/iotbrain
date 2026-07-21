---
title: "Illegal instruction (core dumped) importing numpy/torch on Jetson — OPENBLAS_CORETYPE=ARMV8"
type: fix
company: nvidia
keys:
  - "Illegal instruction (core dumped)"
  - "OPENBLAS_CORETYPE=ARMV8"
  - "numpy==1.19.5"
platform_versions: ["JetPack 4.x", "L4T 32.x"]
devices: [nano, xavier-nx, agx-xavier]
status: verified
verified_on: "TX2 / Xavier / Nano, JetPack 4.4.1-4.5.1, 2021-01 (forum thread: multiple users confirmed both fixes)"
sources:
  - "https://forums.developer.nvidia.com/t/illegal-instruction-core-dumped/165488"
  - "https://github.com/numpy/numpy/issues/18131"
---
## Context
`import numpy` (or anything that imports it — torch, cv2, pandas, jupyter) kills
python instantly with `Illegal instruction (core dumped)` on a Jetson running
JetPack 4.x / Ubuntu 18.04. Started after a `pip install -U numpy` pulled
numpy 1.19.5.

## Knowledge
### Root cause
numpy 1.19.5 bundles an OpenBLAS with a CPU-detection bug on these ARMv8 cores
(Cortex-A57 / Denver2 / Carmel): it selects a kernel using instructions the core
doesn't support, so the process dies on an illegal instruction at import time.
Not a JetPack bug — a numpy/OpenBLAS regression that Jetson's CPUs trip over
(tracked upstream in numpy issue #18131).

### Fix
Either one works (both confirmed by multiple users in the source thread):

1. Force the generic ARMv8 OpenBLAS kernel:
   ```bash
   export OPENBLAS_CORETYPE=ARMV8
   ```
   Add it to `~/.bashrc` to make it stick.
2. Pin the last good numpy:
   ```bash
   pip3 install numpy==1.19.4
   ```

## Verify
```bash
OPENBLAS_CORETYPE=ARMV8 python3 -c "import numpy; print(numpy.__version__)"
```
Prints a version instead of dying with `Illegal instruction`.

## Gotchas
- `sudo python3 ...` drops the env var — use `sudo -E`, and systemd services
  need `Environment=OPENBLAS_CORETYPE=ARMV8` in the unit file.
- Shows up as a torch/cv2/pandas "crash" because they import numpy first —
  check numpy alone before blaming the bigger package.
- Any `pip install -U` or requirements.txt that re-pulls numpy 1.19.5 brings it
  back; pin `numpy==1.19.4` (or upgrade to a numpy release with the fixed
  OpenBLAS) in requirements.
- JetPack 5/6 (Ubuntu 20.04/22.04, newer numpy) are not affected unless an old
  requirements pin drags numpy 1.19.5 back in.
