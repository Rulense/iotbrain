---
title: "RuntimeError: operator torchvision::nms does not exist — torch/torchvision pairing on Jetson"
type: matrix
company: nvidia
keys:
  - "RuntimeError: operator torchvision::nms does not exist"
  - "operator torchvision::nms does not exist"
  - "torchvision"
platform_versions: ["JetPack 5.x", "JetPack 6.x", "L4T 35.x", "L4T 36.x"]
devices: [all]
status: verified
verified_on: "AGX Orin, JetPack 6.1, 2024-11 (forum thread solved by installing matched jp6/cu126 torch 2.5.0 + torchvision 0.20.0 pair)"
sources:
  - "https://forums.developer.nvidia.com/t/pytorch-and-torvision-version-issue-runtimeerror-operator-torchvision-nms-does-not-exist/312446"
  - "https://forums.developer.nvidia.com/t/pytorch-and-torchvision-version-issue-runtimeerror-operator-torchvision-nms-does-not-exist-jetpack-6-2-1/346005"
  - "https://forums.developer.nvidia.com/t/pytorch-for-jetson/72048"
---
## Context
`import torchvision` (or the first model call, e.g. YOLO/detectron post-processing)
raises `RuntimeError: operator torchvision::nms does not exist`. torch itself imports
fine and often reports CUDA available. Extremely common right after installing a
CUDA torch wheel on Jetson and letting pip pull torchvision separately.

## Knowledge
torchvision's compiled C++ ops are only registered when torchvision was built
against the exact torch it runs with. On Jetson this breaks two ways:

1. `pip install torchvision` after installing an NVIDIA/Jetson CUDA torch wheel —
   pip grabs a generic CPU aarch64 torchvision from PyPI built against a different
   torch, and may even silently replace your CUDA torch to satisfy deps.
2. Manually mixing wheel versions that aren't a released pair.

### Pairing matrix (upstream release pairs)
| torch | torchvision |
|-------|-------------|
| 2.8   | 0.23        |
| 2.7   | 0.22        |
| 2.6   | 0.21        |
| 2.5   | 0.20        |
| 2.4   | 0.19        |
| 2.3   | 0.18        |
| 2.2   | 0.17        |
| 2.1   | 0.16        |
| 2.0   | 0.15        |

### Fix
Install torch AND torchvision together, from the same Jetson wheel index, as a
released pair. For JetPack 6 / CUDA 12.6:

```bash
pip3 uninstall -y torch torchvision torchaudio
pip3 install torch torchvision --index-url https://pypi.jetson-ai-lab.dev/jp6/cu126
```

In the solved thread, NVIDIA support resolved it by installing the matched
`torch-2.5.0` + `torchvision-0.20.0` `cp310 linux_aarch64` wheels from the
jp6/cu126 index (plus cuDNN 9.5 via apt).

## Verify
```bash
python3 -c "import torch, torchvision; print(torch.__version__, torchvision.__version__); \
from torchvision.ops import nms; print('nms ok')"
```
No RuntimeError, and the printed pair matches a row in the matrix.

## Gotchas
- `pip install ultralytics` (and similar) can drag in a PyPI torchvision on top of
  your Jetson torch — reinstall the matched pair afterwards, or install such
  packages with `--no-deps`.
- The same registration failure appears as `Couldn't load custom C++ ops` on some
  versions — same root cause, same fix.
- torchvision built from source must be compiled against the installed torch
  (`python3 setup.py install` on the device) — a wheel built against another
  torch build hits the same error even if version numbers match.
