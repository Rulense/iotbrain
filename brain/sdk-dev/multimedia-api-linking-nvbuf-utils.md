---
title: "cannot find -lnvbuf_utils — linking against the Jetson Multimedia API (tegra/nvidia lib dirs, JP5 NvBufSurface migration)"
type: fix
company: nvidia
keys:
  - "/usr/bin/ld: cannot find -lnvbuf_utils"
  - "nvidia-l4t-jetson-multimedia-api"
  - "/usr/src/jetson_multimedia_api"
  - "NvBufSurface"
  - "link_directories(/usr/lib/aarch64-linux-gnu/tegra)"
platform_versions: ["JetPack 4.x", "JetPack 5.x", "JetPack 6.x", "L4T 32.x", "L4T 35.x", "L4T 36.x"]
devices: [all]
status: verified
verified_on: "AGX Xavier, JetPack 4.4.1, 2021 (forum thread marked solved: link_directories(/usr/lib/aarch64-linux-gnu/tegra) before add_executable fixed the link)"
sources:
  - "https://forums.developer.nvidia.com/t/cannot-link-usr-bin-ld-cannot-find-lnvbuf-utils/190973"
  - "https://docs.nvidia.com/jetson/l4t-multimedia/mmapi_build.html"
  - "https://github.com/dusty-nv/jetson-utils/issues/169"
---
## Context
You are building an app against the Jetson Multimedia API (V4L2 codecs,
Argus, NvBuffer/NvBufSurface) — either the samples under
`/usr/src/jetson_multimedia_api` or your own CMake project — and the link
step fails with `/usr/bin/ld: cannot find -lnvbuf_utils` (same pattern for
`-lnvargus_socketclient`, `-lnvbufsurface`, ...), or code that used
nvbuf_utils stopped building on JetPack 5.1.2+.

## Knowledge
### Root cause
Two separate traps:
1. **Link path.** Headers/samples come from
   `sudo apt install nvidia-l4t-jetson-multimedia-api`, but the BSP `.so`
   files live outside the default linker search path — in
   `/usr/lib/aarch64-linux-gnu/tegra` (r32) or
   `/usr/lib/aarch64-linux-gnu/nvidia` (newer L4T; check both with `ls`).
   Runtime loading works because those dirs are in `/etc/ld.so.conf.d/`, but
   `ld` at link time does not read ld.so.conf — so `-lnvbuf_utils` fails
   even though the library is right there.
2. **API removal.** `nvbuf_utils` was deprecated in JetPack 5 in favor of the
   NvUtils `NvBufSurface` API, and the library was removed outright in
   JetPack 5.1.2 — on 5.1.2+ no link flag will find it.

### Fix
For the link path (CMake — must appear *before* `add_executable`):

```cmake
link_directories(/usr/lib/aarch64-linux-gnu/tegra)
```

or for plain Makefiles add `-L/usr/lib/aarch64-linux-gnu/tegra`
(use `.../nvidia` on releases where the libs live there).

For JetPack 5.1.2+: port nvbuf_utils calls (NvBufferCreate/dmabuf-fd
handles) to the NvBufSurface API per NVIDIA's "nvbuf_utils to NvUtils"
migration guide, and link `-lnvbufsurface -lnvbufsurftransform`.

## Verify
- `ldconfig -p | grep -e nvbuf_utils -e nvbufsurface` shows which API your
  L4T actually ships.
- The samples build cleanly:
  `cd /usr/src/jetson_multimedia_api/samples/00_video_decode && sudo make`.

## Gotchas
- The official build doc requires a one-time symlink before building samples:
  `cd /usr/lib/aarch64-linux-gnu && sudo ln -sf libv4l2.so.0 libv4l2.so`.
- Building inside an l4t container: install
  `nvidia-l4t-jetson-multimedia-api` *inside* the image too — headers are not
  among the CSV host mounts (see the l4t-base container entry).
- Same code, different boards: a project that linked on one device and not
  another usually means one image had a stale/extra `.so` copy — fix the `-L`
  path instead of copying libraries around.
