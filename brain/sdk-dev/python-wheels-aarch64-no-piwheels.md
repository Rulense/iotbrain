---
title: "Python wheels on Jetson (aarch64) — piwheels doesn't serve you, cp-tag mismatches, and pip's silent source builds"
type: gotcha
company: nvidia
keys:
  - "is not a supported wheel on this platform"
  - "piwheels"
  - "manylinux2014_aarch64"
  - "linux_aarch64.whl"
  - "Building wheel for"
jetpack: ["all"]
l4t: ["all"]
devices: [all]
status: verified
verified_on: "Xavier NX, JetPack 4.6.1, 2022 (forum thread: cp36 wheel refused by conda Python 3.7; resolved by installing under the JetPack default Python)"
sources:
  - "https://www.piwheels.org/faq.html"
  - "https://forums.developer.nvidia.com/t/error-torch-1-6-0-cp36-cp36m-linux-aarch64-whl-is-not-asupported-wheel-on-this-platform/220881"
  - "https://forums.developer.nvidia.com/t/pytorch-for-jetson/72048"
  - "https://elinux.org/Jetson_Zoo"
---
## Context
You are installing or packaging Python dependencies on a Jetson and either
pip refuses a wheel (`ERROR: ... .whl is not a supported wheel on this
platform`), or `pip install` unexpectedly spends hours in
`Building wheel for ...`. Jetson is aarch64 Linux, which sits in a gap in the
prebuilt-wheel ecosystem. Applies to all JetPack versions.

## Knowledge
- **piwheels is useless on Jetson.** piwheels.org builds only 32-bit
  `armv6l`/`armv7l` wheels for Raspberry Pi OS (its FAQ: no aarch64 support,
  no guarantees off Raspberry Pi). Adding the piwheels index to a Jetson
  buys you nothing: its compiled wheels are armv6l/armv7l-tagged and can't
  match aarch64, and its pure-Python `py3-none-any` wheels are the same
  ones PyPI already serves.
- **PyPI aarch64 coverage is partial.** Most pure-Python and CPU packages now
  ship `manylinux2014_aarch64`/`manylinux_2_28_aarch64` wheels, but
  CUDA-touching packages are the exception: they're CPU-only builds, missing
  entirely, or built without Jetson's sm_87/sm_72 kernels (see the
  arch-flags entry).
- **Wheels are Python-minor-specific.** `torch-*-cp36-*.whl` on a Python 3.7+
  interpreter → `is not a supported wheel on this platform`. NVIDIA builds
  Jetson wheels only for the JetPack default Python (JP4=3.6, JP5=3.8,
  JP6=3.10); use that interpreter or rebuild from source for yours.
- **No wheel match = source build.** pip falls back to the sdist and compiles
  on-device — hours for scipy/grpcio-class packages, and it can OOM (see the
  on-device-builds entry for swap).
- **Where Jetson wheels actually live:** the community jp-specific index
  (`pip3 install ... --index-url https://pypi.jetson-ai-lab.dev/jp6/cu126`
  for JP6/CUDA 12.6) and the Jetson Zoo wheel list on elinux.org.
- **Packaging your own:** build on the target (or inside a matching
  jetson-containers image), which yields `linux_aarch64` tags; host them on
  an internal index/wheelhouse. Any wheel that links JetPack libs
  (CUDA/cuDNN/TensorRT) is tied to that JetPack line — version your index per
  JetPack, like NVIDIA's jp6/cu126 layout does.

## Verify
`pip3 debug --verbose | grep -m5 aarch64` lists the platform/cp tags your
interpreter accepts — a candidate wheel installs only if its filename tags
are in that list. `pip3 install --only-binary :all: <pkg>` fails fast instead
of silently source-building.

## Gotchas
- `uname -m` says `aarch64`, but a conda-forge or pyenv Python changes the cp
  tag pip accepts — the classic "worked outside conda" trap from the source
  thread.
- Wheels built on an x86 host without a proper cross toolchain get tagged
  `linux_x86_64` and are rejected on device; build on aarch64 (device, or
  qemu/native arm64 CI).
- `pip install torch` from plain PyPI succeeds on Jetson but is CPU-only —
  a successful install is not evidence you got CUDA (see the ml-stack
  libcudnn entry).
