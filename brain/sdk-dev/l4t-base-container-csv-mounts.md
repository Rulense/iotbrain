---
title: "Shipping Jetson apps as containers — since JetPack 5, l4t-base no longer mounts CUDA from the host (l4t.csv mounts BSP only)"
type: gotcha
company: nvidia
keys:
  - "l4t.csv"
  - "/etc/nvidia-container-runtime/host-files-for-container.d"
  - "l4t-base"
  - "l4t-jetpack"
  - "csv-mounts"
jetpack: ["4.x", "5.x", "6.x"]
l4t: ["32.x", "35.x", "36.x"]
devices: [all]
status: verified
verified_on: "Orin/Xavier family, JetPack 5.0+ (NGC l4t-base catalog page states the r34.1 behavior change), doc checked 2026-07-17"
sources:
  - "https://catalog.ngc.nvidia.com/orgs/nvidia/containers/l4t-base"
  - "https://nvidia.github.io/container-wiki/toolkit/jetson.html"
  - "https://github.com/NVIDIA/nvidia-container-toolkit/issues/119"
---
## Context
You are packaging a Jetson app as a Docker container (l4t-base or derived)
and either designing what goes in the image vs what comes from the host, or
debugging why an image that worked on JetPack 4 has no `/usr/local/cuda`,
`nvcc`, or TensorRT on a JetPack 5/6 host. Container GPU access on Jetson
works differently from desktop: the nvidia runtime bind-mounts host files
listed in CSV files, not driver-store discovery.

## Knowledge
- With `--runtime nvidia`, the runtime reads CSV files under
  `/etc/nvidia-container-runtime/host-files-for-container.d/` and bind-mounts
  every listed lib/dir/device/symlink from the host into the container
  (BSP/driver userspace like `libnvbufsurface`, Argus/camera stack, plus
  `/dev/nvhost-*` device nodes).
- **JetPack 4:** that directory held `cuda.csv`, `cudnn.csv`, `tensorrt.csv`,
  `l4t.csv` — so tiny l4t-base images got CUDA/cuDNN/TensorRT injected from
  the host (and were therefore tied to whatever the host had installed).
- **JetPack 5+ (L4T r34.1 on):** per the NGC page, "the l4t-base will not
  bring CUDA, CuDNN and TensorRT from the host file system." Only the BSP
  pieces in `l4t.csv` are still mounted. CUDA/cuDNN/TensorRT must now be
  *inside* the image: base on `nvcr.io/nvidia/l4t-cuda`,
  `nvcr.io/nvidia/l4t-tensorrt` (runtime variants), or the full
  `nvcr.io/nvidia/l4t-jetpack`, or use dusty-nv/jetson-containers images.
- Distribution consequences: images are bigger but self-contained and
  reproducible across hosts of the same JetPack line. Match the image's L4T
  major to the host (r36.x image on a JP6/L4T 36.x host); driver libs still
  come from the host mount, so containers don't paper over a JetPack-major
  gap.

## Verify
- `ls /etc/nvidia-container-runtime/host-files-for-container.d/` on the host:
  JP5/6 shows `l4t.csv` (no cuda/cudnn/tensorrt CSVs).
- `docker run --rm --runtime nvidia nvcr.io/nvidia/l4t-jetpack:r36.3.0 nvcc --version`
  works; the same probe on plain l4t-base shows no nvcc on a JP5+ host.

## Gotchas
- Forgetting `--runtime nvidia` (or `default-runtime` in
  `/etc/docker/daemon.json`) skips ALL csv mounts — even l4t-base then lacks
  GPU device nodes. See the iot/docker-gpu entry.
- Old JP4-era tutorials that rely on host-mounted CUDA silently break on
  JP5/6; this migration was never loudly documented (see the
  nvidia-container-toolkit issue).
- You can extend the mounts by dropping your own `.csv` in
  `host-files-for-container.d/` (e.g. extra camera libs), but anything you
  add from the host re-couples your image to host state — prefer baking it in.
- Headers are not mounted: compiling inside a container needs the dev
  packages installed in the image (e.g. `nvidia-l4t-jetson-multimedia-api`).
