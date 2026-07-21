---
title: "Run vLLM on Jetson AGX Thor — use the NVIDIA Thor containers; old images fail with 'no kernel image' or missing model support"
type: config
company: nvidia
keys:
  - "ghcr.io/nvidia-ai-iot/vllm:latest-jetson-thor"
  - "nvcr.io/nvidia/vllm"
  - "vllm serve"
  - "no kernel image is available for execution on the device"
  - "vllm fails on thor"
platform_versions: ["JetPack 7.x", "L4T 38.x", "CUDA 13.x"]
devices: [agx-thor]
status: verified
verified_on: "doc checked 2026-07-21"
sources:
  - "https://www.jetson-ai-lab.com/tutorials/genai-on-jetson-llms-vlms/"
  - "https://forums.developer.nvidia.com/t/vllm-0-12-x-container-for-jetson-thor/355316"
  - "https://forums.developer.nvidia.com/t/thor-vllm/348244"
---
## Context
You want an OpenAI-compatible LLM server (vLLM) on an AGX Thor. Building vLLM
on-device or reusing an Orin-era (r36/cu126) image is the failure path — Thor
is sm_110/CUDA 13, so mismatched builds die at kernel launch with
`no kernel image is available for execution on the device`, and early Thor
containers (vLLM 0.9.x, 25.08) lack support for newer model formats (FP4
quantization, GPT-OSS).

## Knowledge
Two maintained container lines run vLLM on Thor:

1. **Jetson AI Lab image** (official tutorial):
   ```
   docker run --rm -it --runtime nvidia --network host \
     -v ~/.cache/huggingface:/root/.cache/huggingface \
     ghcr.io/nvidia-ai-iot/vllm:latest-jetson-thor \
     vllm serve <model>
   ```
   (On Orin the same tutorial uses `ghcr.io/nvidia-ai-iot/vllm:latest-jetson-orin`
   — the tags are per-device, don't cross them.)
2. **NGC vLLM releases** — `nvcr.io/nvidia/vllm:<yy.mm>-py3`, updated monthly;
   newer tags track upstream vLLM (e.g. the 25.12.post1 tag carries vLLM 0.12,
   which the source thread confirms adds speculative decoding / EAGLE-3 for
   Qwen-family vision models). The Triton variant
   `nvcr.io/nvidia/tritonserver:<yy.mm>-vllm-python-py3` bundles the same stack.

For benchmarking, NVIDIA staff recommend maxing the device first:
`sudo nvpmodel -m 0 && sudo jetson_clocks`.

## Verify
The server starts and `curl http://localhost:8000/v1/models` lists your model;
no `no kernel image` errors in the container log.

## Gotchas
- Model-support gaps are usually the container being too old, not Thor — e.g.
  vLLM 0.9.2-era images had no FP4/GPT-OSS support; pull the current monthly tag
  before filing bugs.
- Large models are memory-bandwidth-bound on Thor's unified memory — flat
  tokens/s across concurrency levels (observed with a 32B FP8 model) is the
  hardware envelope, not a config error.
- `--network host` plus the HF cache mount matter: without the cache volume
  every container restart re-downloads tens of GB.
- The jetson-containers framework also builds vLLM for JetPack 7.x if you need
  a custom stack (see `ml-stack/jetson-containers-dependency-escape-hatch.md`).
