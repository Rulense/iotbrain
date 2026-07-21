---
title: "nvarguscamerasrc in Docker: mount /tmp/argus_socket — and remount after any nvargus-daemon restart"
type: fix
company: nvidia
keys:
  - "Connecting to nvargus-daemon failed: Connection refused"
  - "Failed to create CameraProvider"
  - "/tmp/argus_socket"
  - "nvarguscamerasrc"
platform_versions: ["all"]
devices: [all]
status: verified
verified_on: "Orin Nano, JetPack 5.x era (version not stated in thread), 2023-11-01 (poster confirmed fix)"
sources:
  - "https://forums.developer.nvidia.com/t/resolving-video-capture-error-in-docker-container-after-restarting-nvargus-daemon/271196"
  - "https://forums.developer.nvidia.com/t/using-nvarguscamerasrc-within-a-docker-container/328246"
---
## Context
A CSI camera pipeline that works on the host fails inside a Docker container
with `Connecting to nvargus-daemon failed: Connection refused` /
`Failed to create CameraProvider` — either from the start, or suddenly after
`nvargus-daemon` was restarted on the host. Mechanism is the same on all
JetPacks: the Argus client/daemon split predates and survives every release.

## Knowledge
### Root cause
`nvarguscamerasrc` inside the container is only a *client*. The camera stack
(`nvargus-daemon`) runs on the host, and the client reaches it through the
Unix socket `/tmp/argus_socket`. If the socket isn't shared into the
container, connection is refused. If you bind-mounted the socket *file* and
then restart the daemon on the host, the daemon creates a **new** socket
inode — the container still holds the stale one, and the same error returns.

### Fix
Share the socket (typical run line):
```
docker run -it --runtime nvidia \
  -v /tmp/argus_socket:/tmp/argus_socket \
  --device /dev/video0 \
  nvcr.io/nvidia/l4t-base:<your-l4t-tag> bash
```
If the daemon may be restarted while containers run, bind-mount the directory
instead so the fresh socket stays visible (the fix confirmed in the source
thread):
```
-v /tmp/:/tmp/
```
Otherwise, after `sudo systemctl restart nvargus-daemon` on the host, restart
or recreate the container.

## Verify
Inside the container:
```
gst-launch-1.0 nvarguscamerasrc num-buffers=10 ! fakesink
```
runs without the `Connecting to nvargus-daemon failed` error.

## Gotchas
- Passing `--device /dev/video0` alone is NOT enough for Argus — device nodes
  serve the V4L2 path; Argus needs the socket.
- The `jetson-containers` run wrapper mounts `/tmp/argus_socket` for you; if
  you hand-roll `docker run`, you must add it yourself (same for DeepStream
  containers).
- Mounting all of `/tmp` is a coarse workaround — fine on a devkit, think
  twice on production images (host `/tmp` becomes visible in the container).
