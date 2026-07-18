---
title: "Fleet OTA on Jetson — apt package OTA vs image-based OTA, and what survives each"
type: matrix
company: nvidia
keys:
  - "repo.download.nvidia.com/jetson"
  - "nvidia-l4t-apt-source.list"
  - "apt dist-upgrade"
  - "l4t_generate_ota_package.sh"
jetpack: ["5.x", "6.x"]
l4t: ["35.x", "36.x"]
devices: [all]
status: verified
verified_on: "Orin family, L4T r36.5 Developer Guide (Software Packages and the Update Mechanism), doc checked 2026-07-17"
sources:
  - "https://docs.nvidia.com/jetson/archives/r36.5/DeveloperGuide/SD/SoftwarePackagesAndTheUpdateMechanism.html"
  - "https://developer.ridgerun.com/wiki/index.php/How_to_Use_A/B_Filesystem_Redundancy_and_OTA_with_NVIDIA_Jetpack"
---
## Context
You have deployed Jetsons and need to ship BSP/JetPack updates over the network.
NVIDIA supports two OTA mechanisms with very different blast radii — choosing
wrong is how fleets end up with hand-reflashed units.

## Knowledge
| | apt (Debian package) OTA | Image-based OTA |
|---|---|---|
| Delivery | NVIDIA apt repo: `deb https://repo.download.nvidia.com/jetson/common <release> main` + `.../jetson/t234 <release> main` (in `/etc/apt/sources.list.d/nvidia-l4t-apt-source.list`) | OTA payload built on a host with `ota_tools` (`l4t_generate_ota_package.sh`), pushed to the device by you/your fleet tool, applied on reboot |
| Scope | Point/minor releases within the same major only (e.g. 36.2 → 36.3: edit `<release>` in the sources list, then `sudo apt dist-upgrade`). **35.x → 36.x is not supported via apt.** | Full BSP partition update; supports major upgrades (e.g. 35.x → 36.x) and partition-layout changes |
| What it updates | Individual debs: kernel, L4T userspace libs, and QSPI **bootloader firmware** | Bootloader, kernel, and rootfs partitions, rewritten from the payload |
| What survives | Everything you didn't install via those debs — user data, your app, configs stay in place | Only what's in the payload's rootfs (or on partitions the payload doesn't touch). User data on the rootfs does **not** survive unless you use A/B rootfs or keep it on a separate data partition |
| Failure mode | Not failsafe: power loss / interrupted `dist-upgrade` can leave the unit unbootable — see [../setup/recover-unbootable-after-apt-ota-upgrade.md](../setup/recover-unbootable-after-apt-ota-upgrade.md) | Failsafe by design: A/B chains — update is written to the inactive slot, roles swap only on success; a failed update can't brick the device |

Rule of thumb: dev benches and small same-major bumps → apt OTA. Real fleets →
image-based OTA from a golden rootfs, with application state on a separate data
partition (or A/B rootfs enabled) so device identity/config survives the swap.

## Verify
- After apt OTA: `cat /etc/nv_tegra_release` shows the new L4T revision and the
  device reboots cleanly.
- After image-based OTA: device boots the new slot; `cat /etc/nv_tegra_release`
  shows the target release; with A/B, `sudo nvbootctrl dump-slots-info` shows
  the expected active slot.

## Gotchas
- Never mix repos: pointing sources at a different `<release>` and doing a
  partial upgrade ("combination of packages from different releases") is
  explicitly advised against and produces half-upgraded, unbootable systems.
- apt OTA updates QSPI bootloader firmware too — don't power-cut during the
  post-install steps (`nv-l4t-bootloader-config` etc.).
- `apt upgrade` handles point releases; moving minor release (36.2 → 36.3)
  requires editing the sources list *and* `apt dist-upgrade`.
- Image-based OTA payloads are built per source-release/target-release/board
  combination — a fleet with mixed starting versions needs multiple payloads.
