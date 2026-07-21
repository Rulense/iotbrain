---
title: Don't apt-install Ubuntu's nvidia-cuda-toolkit on Jetson — JetPack CUDA lives in /usr/local/cuda
type: gotcha
company: nvidia
keys:
  - "nvidia-cuda-toolkit"
  - "nvcc: command not found"
  - "/usr/local/cuda"
  - "nvidia-jetpack"
platform_versions: ["JetPack 5.x", "JetPack 6.x", "L4T 35.x", "L4T 36.x"]
devices: [all]
status: unverified
sources:
  - "https://forums.developer.nvidia.com/t/nvcc-command-not-found-and-unable-to-install-nvidia-cuda-toolkit-in-the-jetpack-6/275486"
  - "https://developer.nvidia.com/blog/simplifying-cuda-upgrades-for-nvidia-jetson-users/"
  - "https://docs.nvidia.com/jetson/jetpack/install-setup/index.html"
---
## Context
`nvcc` isn't found after flashing, so you run
`sudo apt install nvidia-cuda-toolkit`. That package comes from Ubuntu's
universe repo, not NVIDIA's Jetson repo — on Ubuntu 22.04 it is CUDA 11.5,
built without any knowledge of the JetPack 6 CUDA 12.x stack. Users hit unmet
dependency errors, or end up with two CUDA toolkits where cuDNN/TensorRT were
built against the JetPack one.

## Knowledge
- JetPack's CUDA comes from NVIDIA's L4T apt repo via the `nvidia-jetpack`
  meta-package and installs under `/usr/local/cuda-<ver>` (symlinked from
  `/usr/local/cuda`). The right install command on a flashed device:
  ```bash
  sudo apt update && sudo apt install nvidia-jetpack
  ```
- "nvcc not found" on a healthy JetPack install is a PATH problem, not a missing
  toolkit:
  ```bash
  export PATH=/usr/local/cuda/bin:$PATH
  export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
  ```
  (add to `~/.bashrc`).
- Ubuntu's `nvidia-cuda-toolkit` puts an older `nvcc` in `/usr/bin`, which then
  shadows or conflicts with the JetPack toolkit — remove it if installed:
  `sudo apt purge nvidia-cuda-toolkit`.
- Wanting a NEWER CUDA than JetPack shipped is supported the official way:
  since CUDA 11.8, NVIDIA's CUDA aarch64-jetson repo lets you install a newer
  `cuda-toolkit-X-Y` side-by-side on top of JetPack 5+ without reflashing
  (see the "Simplifying CUDA Upgrades" blog); select via the
  `/usr/local/cuda` symlink or `update-alternatives`.

## Verify
```bash
ls -l /usr/local/cuda           # symlink to the intended cuda-<ver>
which nvcc && nvcc --version    # /usr/local/cuda/bin/nvcc, expected version
dpkg -l | grep -E "cuda-toolkit|nvidia-jetpack"
```
`nvcc --version` matches the CUDA version JetPack shipped (JetPack 6.x → CUDA 12.x).

## Gotchas
- Random PPAs on the device make the wrong `nvidia-cuda-toolkit` candidate win;
  the source thread's dependency errors came from third-party PPAs.
- cuDNN and TensorRT from JetPack are compiled against JetPack's CUDA; pointing
  builds at a mismatched toolkit produces link/runtime version errors even when
  `nvcc` works.
- After installing a newer CUDA from the Jetson repo, per-user PATHs may still
  pick up the old one — check `which nvcc` before rebuilding anything.
