---
title: jetson-containers — prebuilt CUDA ML containers as the escape hatch for on-device dependency hell
type: recipe
company: nvidia
keys:
  - "jetson-containers"
  - "autotag"
  - "l4t-pytorch"
jetpack: ["6.x", "7.x"]
l4t: ["36.x", "38.x"]
devices: [orin-nano, orin-nx, agx-orin, agx-thor]
status: verified
verified_on: "Orin family, JetPack 6.2 (repo-documented tested/supported config), docs checked 2026-07-17"
sources:
  - "https://github.com/dusty-nv/jetson-containers"
  - "https://www.jetson-ai-lab.com/"
---
## Context
You've burned hours pip-installing torch/onnxruntime/vllm/transformers natively
on a Jetson and every fix breaks something else (CUDA wheel mismatches, source
builds that OOM, cuDNN/TensorRT ABI conflicts). jetson-containers is the
maintained way out: CUDA-enabled container images built per JetPack/L4T, with
the version matrix already solved.

## Knowledge
One-time setup (installs the `jetson-containers` and `autotag` CLI tools):

```bash
git clone https://github.com/dusty-nv/jetson-containers
bash jetson-containers/install.sh
```

Run a stack — `autotag` picks an image compatible with your L4T (local, from
registry, or builds it), and `jetson-containers run` wraps `docker run` with
`--runtime nvidia` and data-cache mounts already set:

```bash
jetson-containers run $(autotag l4t-pytorch)     # torch + torchvision, CUDA
jetson-containers run $(autotag ollama)          # LLM serving
jetson-containers build pytorch:2.6 onnxruntime  # compose a custom image
```

Package families cover ML (pytorch, tensorflow, jax, onnxruntime), LLM (vllm,
ollama, transformers), VLM, ROS/robotics, speech, and diffusion — each package
declares its dependency/version constraints so the build system resolves a
consistent stack for your JetPack instead of you doing it by hand.

Current master is tested/supported on JetPack 6.2 (CUDA 12.6) and JetPack 7
(CUDA 13); older JetPack 4/5 devices should use the older tags/images published
for their L4T.

## Verify
```bash
jetson-containers run $(autotag l4t-pytorch) \
  python3 -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```
Prints a version and `True` inside the container.

## Gotchas
- Containers are still L4T-bound: an image built for another JetPack major won't
  see the GPU properly — let `autotag` choose rather than hard-coding tags.
- First `autotag` of a big stack can pull tens of GB — put docker's data-root on
  NVMe, not the SD card.
- Plain `docker run` without `--runtime nvidia` (or without default-runtime set
  in `/etc/docker/daemon.json`) gives no GPU inside the container — use the
  `jetson-containers run` wrapper.
- The community pip index (`pypi.jetson-ai-lab.dev`) used by the build system
  has had outages; `install.sh --pypi` can host a local cache/mirror for fleets.
