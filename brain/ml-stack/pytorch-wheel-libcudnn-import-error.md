---
title: "ImportError: libcudnn.so after pip-installing PyTorch on Jetson"
type: fix
company: nvidia
keys:
  - "ImportError: libcudnn.so.8: cannot open shared object file"
  - "ImportError: libcudnn.so.9: cannot open shared object file"
  - "pip install torch"
jetpack: ["5.x", "6.x"]
l4t: ["35.x", "36.x"]
devices: [all]
status: verified
verified_on: "AGX Orin, JetPack 6.1, 2026-07-17"
sources: ["https://forums.developer.nvidia.com/t/pytorch-for-jetson/72048"]
---
## Context
You installed PyTorch on a Jetson with plain `pip install torch` (or a wheel built
for a different JetPack) and `import torch` fails with a cuDNN shared-object error —
or imports fine but `torch.cuda.is_available()` is False.

## Knowledge
### Root cause
Generic PyPI aarch64 wheels are CPU-only, and NVIDIA-built wheels are compiled
against the exact CUDA/cuDNN of one JetPack release. A wheel/JetPack mismatch
leaves torch looking for a libcudnn version that isn't on the device.

### Fix
1. Check your JetPack/L4T: `cat /etc/nv_tegra_release`
2. Uninstall the wrong wheel: `pip3 uninstall torch torchvision torchaudio`
3. Install the wheel built for YOUR JetPack from the "PyTorch for Jetson" index
   (see source thread; for JetPack 6/CUDA 12.6 use the jp6/cu126 pip index).
4. Ensure the JetPack ML runtime libs are present:
   `sudo apt install nvidia-jetpack` (or at minimum the cudnn/tensorrt components).

## Verify
`python3 -c "import torch; print(torch.__version__, torch.cuda.is_available())"`
prints a version and `True`.

## Gotchas
- torchvision must be version-paired with torch (pairing table in the source thread);
  mismatch raises `operator torchvision::nms does not exist`.
- A JetPack upgrade (e.g. 6.0 → 6.1) can silently re-break this — reinstall matching wheels.
