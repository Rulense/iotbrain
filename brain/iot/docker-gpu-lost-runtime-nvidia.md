---
title: "Docker container can't reach the GPU on Jetson after Docker install/update — re-register nvidia runtime, set default-runtime"
type: fix
company: nvidia
keys:
  - 'could not select device driver "" with capabilities: [[gpu]]'
  - "unknown or invalid runtime name: nvidia"
  - "nvidia-ctk runtime configure --runtime=docker"
  - '"default-runtime": "nvidia"'
  - "docker container cannot use gpu"
  - "gpu missing inside container"
platform_versions: ["JetPack 5.x", "JetPack 6.x", "L4T 35.x", "L4T 36.x"]
devices: [all]
status: unverified
sources:
  - "https://forums.developer.nvidia.com/t/running-ai-docker-containers-on-jetson-orin-nano-with-gpu-support/335561"
  - "https://github.com/dusty-nv/jetson-containers/blob/master/docs/setup.md"
---
## Context
Containers that used the GPU stop doing so — typically after reinstalling or
upgrading Docker (`curl https://get.docker.com | sh`, or an apt upgrade of
`docker-ce`), re-imaging a fleet unit, or switching base images. Symptoms:
```
docker: Error response from daemon: could not select device driver "" with capabilities: [[gpu]]
```
(when using `--gpus all`), or
```
Error response from daemon: unknown or invalid runtime name: nvidia
```
(when using `--runtime nvidia`), or the container starts but CUDA is absent.

## Knowledge
### Root cause
On Jetson, GPU access in containers goes through the NVIDIA container runtime
(nvidia-container-toolkit, CSV-mode mounts of the L4T libs). A fresh docker-ce
install ships **no** `/etc/docker/daemon.json` at all, and a reinstall/re-image
can leave one without the `nvidia` runtime entry — either way Docker doesn't
know the `nvidia` runtime exists, so it can't inject the GPU. Having the
toolkit installed isn't enough; the runtime must be registered in Docker's
config.

### Fix
```bash
sudo apt update && sudo apt install -y nvidia-container        # JetPack's toolkit meta-package
sudo nvidia-ctk runtime configure --runtime=docker             # registers "nvidia" in /etc/docker/daemon.json
sudo systemctl restart docker
```
Then make it the default runtime (required for `docker build` steps that need
CUDA, and saves every run/compose file from needing the flag) —
`/etc/docker/daemon.json` should contain:
```json
{
    "runtimes": {
        "nvidia": {
            "path": "nvidia-container-runtime",
            "runtimeArgs": []
        }
    },
    "default-runtime": "nvidia"
}
```
followed by `sudo systemctl restart docker`. Add your user to the docker group
(`sudo usermod -aG docker $USER`) to drop the sudo.

## Verify
- `docker info --format '{{.DefaultRuntime}}'` → `nvidia`
- `sudo docker run --rm --runtime nvidia nvcr.io/nvidia/l4t-base:r36.2.0 ldconfig -p | grep -i cuda`
  lists CUDA libraries inside the container (on JetPack 5 use an r35.x tag).

## Gotchas
- On Jetson prefer `--runtime nvidia` over `--gpus all` — the `--gpus` flag
  is the discrete-GPU path and is what emits `could not select device driver`
  when the toolkit isn't wired up.
- A JSON syntax error in `daemon.json` stops the Docker daemon entirely
  (`systemctl status docker` shows the parse error) — edit carefully.
- k3s/containerd don't read `daemon.json`; they need their own runtime config
  (`nvidia-ctk runtime configure --runtime=containerd`).
- `jetson-containers run` from dusty-nv already passes `--runtime nvidia`;
  it's a quick way to confirm the runtime works before debugging your own image.
