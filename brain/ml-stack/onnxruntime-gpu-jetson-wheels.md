---
title: onnxruntime-gpu wheels for Jetson — PyPI installs are CPU-only, use Jetson AI Lab / Jetson Zoo wheels
type: config
company: nvidia
keys:
  - "onnxruntime_gpu"
  - "CUDAExecutionProvider"
  - "TensorrtExecutionProvider"
  - "pip install onnxruntime"
jetpack: ["5.x", "6.x"]
l4t: ["35.x", "36.x"]
devices: [all]
status: verified
verified_on: "Orin Nano, JetPack 6.2, 2025-03 (forum thread solved: jp6/cu126 onnxruntime_gpu 1.20.2 wheel exposed CUDA/TensorRT providers)"
sources:
  - "https://forums.developer.nvidia.com/t/onnx-runtime-gpu/327411"
  - "https://forums.developer.nvidia.com/t/jetpack-6-0-onnxruntime-gpu/307053"
  - "https://www.elinux.org/Jetson_Zoo#ONNX_Runtime"
---
## Context
You `pip install onnxruntime` (or `onnxruntime-gpu`) on a Jetson and
`onnxruntime.get_available_providers()` only lists `AzureExecutionProvider` and
`CPUExecutionProvider` — no CUDA. PyPI has no CUDA-enabled aarch64/Jetson build
of onnxruntime-gpu; the generic wheel is CPU-only.

## Knowledge
Install a Jetson-built `onnxruntime_gpu` wheel matching your JetPack:

- **JetPack 6.x (CUDA 12.6):** Jetson AI Lab pip index —
  ```bash
  pip3 uninstall -y onnxruntime onnxruntime-gpu
  pip3 install onnxruntime-gpu --index-url https://pypi.jetson-ai-lab.dev/jp6/cu126
  ```
  (In the solved thread NVIDIA support pointed at the exact wheel
  `onnxruntime_gpu-1.20.2-cp310-cp310-linux_aarch64.whl` from that index.)
- **JetPack 4.x/5.x:** prebuilt GPU-enabled wheels are listed per JetPack version
  in the Jetson Zoo (elinux.org, "ONNX Runtime" section) — pick the wheel built
  for YOUR JetPack and Python version. Per NVIDIA support, "the onnxruntime
  package in Jetson Zoo has GPU enabled already."

These wheels include the `CUDAExecutionProvider` and `TensorrtExecutionProvider`
(TensorRT EP links against the JetPack TensorRT, so JetPack version must match).

## Verify
```python
import onnxruntime as ort
print(ort.get_available_providers())
# expect ['TensorrtExecutionProvider', 'CUDAExecutionProvider', 'CPUExecutionProvider']
```
Then create an InferenceSession with `providers=['CUDAExecutionProvider']` and
confirm no fallback warning is logged.

## Gotchas
- Package name differs: PyPI uses `onnxruntime-gpu`, the wheel file/module is
  `onnxruntime_gpu` — but you still `import onnxruntime`.
- Having plain `onnxruntime` installed alongside `onnxruntime_gpu` shadows the
  GPU build — uninstall both, then install only the GPU wheel.
- Wheel availability lags new JetPack minors (e.g. gaps around 6.1/6.2 releases);
  if the index has no build for your combo, building from source with
  `--use_cuda --use_tensorrt` is the documented fallback (onnxruntime build docs).
- A wheel built for a different JetPack fails at import or at provider init with
  missing `libcudnn`/`libnvinfer` versions — same class of problem as torch wheels.
