---
title: TensorRT engine plan files are not portable — rebuild per device and per TensorRT version
type: gotcha
company: nvidia
keys:
  - "The engine plan file is not compatible with this version of TensorRT"
  - "please rebuild"
  - "Using an engine plan file across different models of devices is not recommended"
  - "trtexec --saveEngine"
  - "engine fails on another device"
  - "tensorrt engine version mismatch"
platform_versions: ["all"]
devices: [all]
status: verified
verified_on: "all Jetson (TensorRT Developer Guide, Engine Compatibility section), doc checked 2026-07-17"
sources:
  - "https://docs.nvidia.com/deeplearning/tensorrt/latest/inference-library/engine-compatibility.html"
  - "https://forums.developer.nvidia.com/t/the-engine-plan-file-is-not-compatible-with-this-version-of-tensorrt-8-4-1-5-got-8-4-2-4-please-rebuild/223809"
  - "https://github.com/NVIDIA/TensorRT/issues/574"
---
## Context
You copied a serialized `.engine` / `.plan` / `.trt` file from another machine
(x86 build box, a different Jetson model, or the same Jetson before a JetPack
upgrade) and deserialization fails with
`The engine plan file is not compatible with this version of TensorRT,
expecting library version X got Y, please rebuild.` — or it loads but warns
about running on a different device.

## Knowledge
Per the TensorRT docs: "By default, TensorRT engines are compatible only with
the version of TensorRT used to build them" and "only compatible with the type
of device where they were built". TensorRT records the compute capability in
the plan and checks it at load time. Concretely for Jetson:

- An engine built on x86 (dGPU) never runs on Jetson, and vice versa.
- An engine built on Xavier (sm_72) won't load on Orin (sm_87).
- A JetPack upgrade usually bumps TensorRT → every cached engine on the device
  must be rebuilt (this is why DeepStream/jetson-inference regenerate engines
  on first run after an upgrade).
- Hardware-compatibility mode (`kAMPERE_PLUS`) is explicitly "not supported on
  NVIDIA DRIVE OS or JetPack" — the dGPU escape hatch does not apply here.
- DLA-enabled engines are additionally tied to the DLA of the device that built them.

The workflow that works: ship the ONNX (or the builder script), build the
engine on each target device:

```bash
/usr/src/tensorrt/bin/trtexec --onnx=model.onnx --saveEngine=model.engine --fp16
```

## Verify
```bash
dpkg -l | grep nvinfer   # TensorRT version on this device
/usr/src/tensorrt/bin/trtexec --loadEngine=model.engine
```
Engine deserializes and runs inference without the "not compatible / please
rebuild" error.

## Gotchas
- Even identical TensorRT versions on different GPU models are not portable —
  the version match in the error message is necessary, not sufficient.
- Version mismatch down to build number matters ("8.4.1.5 got 8.4.2.4" fails);
  matching major.minor is not enough for plan files.
- INT8 calibration caches are more portable than engines (reusable within a
  major version) — cache the calibration, not the engine.
- Engine build on Orin Nano can take minutes and lots of RAM; do it once at
  provision time, not at app startup, and key the cache filename by device +
  TensorRT version.
