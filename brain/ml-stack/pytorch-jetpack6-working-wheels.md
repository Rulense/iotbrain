---
title: Known-working PyTorch wheel source for JetPack 6.x (CUDA 12.6)
type: config
company: nvidia
keys:
  - "pypi.jetson-ai-lab"
  - "torch jetpack 6"
  - "cu126"
jetpack: ["6.0", "6.1", "6.2"]
l4t: ["36.x"]
devices: [orin-nano, orin-nx, agx-orin]
status: verified
verified_on: "Orin Nano, JetPack 6.2, 2026-07-17"
sources:
  - "https://forums.developer.nvidia.com/t/pytorch-for-jetson/72048"
  - "https://www.jetson-ai-lab.com/"
---
## Context
You need CUDA-enabled torch/torchvision/torchaudio on JetPack 6.x without
building from source.

## Knowledge
The Jetson AI Lab community index publishes wheels built for JetPack 6 / CUDA 12.6:

```bash
pip3 install torch torchvision torchaudio \
  --index-url https://pypi.jetson-ai-lab.dev/jp6/cu126
```

Wheels there are built per-JetPack-major — do not mix a jp6 wheel onto JetPack 5.

## Verify
`python3 -c "import torch; print(torch.cuda.is_available())"` → `True`.

## Gotchas
- If the index URL is unreachable, fall back to the wheel links in the
  "PyTorch for Jetson" forum thread (source above).
