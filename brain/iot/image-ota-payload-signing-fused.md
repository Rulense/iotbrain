---
title: "Image-based OTA on fused Jetsons — build the payload with the same PKC/SBK keys the device was fused with"
type: gotcha
company: nvidia
keys:
  - "l4t_generate_ota_package.sh"
  - "ota_payload_package.tar.gz"
  - "nv_ota_start.sh"
  - "--uefi-keys"
  - "ota fails on fused jetson"
  - "signed ota payload"
platform_versions: ["JetPack 6.x", "L4T 36.x"]
devices: [agx-orin, orin-nx, orin-nano]
status: verified
verified_on: "doc checked 2026-07-21"
sources:
  - "https://docs.nvidia.com/jetson/archives/r36.4/DeveloperGuide/SD/SoftwarePackagesAndTheUpdateMechanism.html"
  - "https://forums.developer.nvidia.com/t/what-changes-if-i-specify-the-optional-pkc-key-and-sbk-key-when-generating-the-ota-update-payload-package/209344"
---
## Context
You run image-based OTA (the partition-level update path, not apt) on a fleet
where devices have secure boot fuses burned (PKC, optionally SBK). The OTA
payload generator has optional key flags that are NOT optional for fused
devices — and NVIDIA's tooling deliberately leaves payload-transport security
to you.

## Knowledge
- Generate the payload on the host with the device's root-of-trust keys:
  ```
  sudo -E ./tools/ota_tools/version_upgrade/l4t_generate_ota_package.sh \
      -u <PKC_key_file> -v <SBK_key_file> <target_board> <bsp_version>
  ```
  For both `-u` and `-v` the doc's requirement is that the key "must be the
  same as the file that was used to flash images to the target board" — the
  boot-chain images inside the payload are signed/encrypted for that fused
  root of trust. A payload built without the keys (or with the wrong ones)
  produces images a fused device's boot chain will not accept.
- With UEFI Secure Boot enabled, also pass `--uefi-keys <keys.conf>` (and
  `--uefi-enc` where used): the generator then emits an overlay of "UEFI
  payloads signed and/or encrypted by the specified UEFI keys".
- **Transport verification is your job.** The documented flow is: download
  `ota_payload_package.tar.gz`, then "Validate the downloaded OTA payload
  package and its contents according to your own security requirements",
  then run `sudo ./nv_ota_start.sh /ota/ota_payload_package.tar.gz`. NVIDIA
  signs the boot-chain images inside the payload; it does not authenticate the
  tarball you fetched — add your own signature/hash check (and TLS) in the OTA
  client before unpacking.
- Failure containment: with rootfs A/B, a failed slot falls back; if the update
  fails more than the retry limit, the device boots the recovery kernel.

## Verify
On a fused test unit, apply the signed payload end-to-end: `nv_ota_start.sh`
completes, the device reboots into the new BSP (`cat /etc/nv_tegra_release`),
and the bootloader chain still verifies (device boots without security
warnings). A deliberately unsigned payload on the same unit must fail.

## Gotchas
- Keep one keyset per fleet cohort and record which devices were fused with
  what — an OTA built against the wrong PKC bricks the update (not the device:
  A/B + recovery kernel catch it, but the fleet stays on the old version).
- Unfused dev units accept unsigned payloads, so a pipeline that "works in the
  lab" can still be wrong for production — test against fused hardware.
- Budget target-side space: applying image-based OTA needs roughly 6 GB free
  on the device for the unpacked payload.
- For choosing between apt OTA and image-based OTA in the first place, see
  `iot/fleet-ota-apt-vs-image-based.md`.
