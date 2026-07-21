---
title: "Encrypt the Jetson rootfs with LUKS — ROOTFS_ENC=1 flashing, EKB-derived per-device keys, and the unencrypted /boot split"
type: recipe
company: nvidia
keys:
  - "ROOTFS_ENC=1"
  - "disk_enc.key"
  - "APP_ENC"
  - "luks-srv"
  - "encrypt jetson rootfs"
  - "jetson disk encryption"
platform_versions: ["JetPack 6.x", "JetPack 7.x", "L4T 36.x", "L4T 38.x"]
devices: [agx-orin, orin-nx, orin-nano, agx-thor]
status: verified
verified_on: "doc checked 2026-07-21"
sources:
  - "https://docs.nvidia.com/jetson/archives/r38.4/DeveloperGuide/SD/Security/DiskEncryption.html"
  - "https://docs.nvidia.com/jetson/archives/r36.2/DeveloperGuide/SD/Security/DiskEncryption.html"
---
## Context
You need data-at-rest protection on a deployed Jetson (stolen-device scenario).
Jetson Linux ships an official LUKS flow (AES-XTS, 256-bit) where the disk
passphrase is derived per device inside OP-TEE — but it's a flash-time decision
with real key-management homework, not an `apt install` afterthought.

## Knowledge
1. **Key material**: the LUKS master secret rides in the EKB (Encrypted Key
   Blob). Your `disk_enc.key` must match the disk-encryption key (`sym2` /
   second key) inside the `eks_<platform>.img` you build into the BSP.
   Regenerate that image with your own keys via the OP-TEE sources' example
   script — the doc is blunt that the shipped values "are only for reference
   and testing purposes so that you should not use them as given."
2. **Flash with encryption enabled**:
   - AGX Thor (internal): `sudo ROOTFS_ENC=1 ./l4t_initrd_flash.sh -i "./disk_enc.key" jetson-agx-thor-devkit internal`
   - Orin Nano/NX (external NVMe): `sudo ROOTFS_ENC=1 ./l4t_initrd_flash.sh -i ./disk_enc.key jetson-orin-nano-devkit external`
3. **Resulting layout**: the old single `APP` partition is split — `APP` stays
   cleartext and carries only the `/boot` branch (kernel, DTB, initrd, because
   "Bootloader cannot read encrypted files"), while `APP_ENC` holds the rest of
   the rootfs as a LUKS volume.
4. **Unlock path (no passphrase prompt)**: at boot, `nvluks-srv-app` asks the
   OP-TEE `luks-srv` TA, which uses `jetson_user_key_pta` and a NIST SP 800-108
   KDF to derive a per-device key from the EKB disk key + device ECID, then a
   per-disk passphrase (disk UUID as context). Cloned disks therefore don't
   unlock on other units — that's the point.

## Verify
`lsblk -f` shows `APP_ENC` as `crypto_LUKS` with a `dm-crypt` mapping mounted at
`/`; the device boots unattended to a decrypted rootfs; the disk moved to
another Jetson (or a PC) does not unlock.

## Gotchas
- `/boot` is NOT encrypted. Disk encryption gives confidentiality only — pair
  it with secure boot / UEFI secure boot so the cleartext boot chain can't be
  swapped out (see `setup/secure-boot-pkc-fuse-burning-orin.md`).
- Generate production EKB/rootfs images on a secured host — the docs call for
  an HSM-equipped system for manufacturing.
- The boot flow should issue `LUKS_SRV_TA_CMD_SRV_DOWN` once volumes are open
  so nothing can ask OP-TEE for the passphrase again until reboot (documented
  hardening step).
- Because keys derive from the ECID, a reflash that changes EKB contents (or a
  board swap in the field) makes existing encrypted data unrecoverable by
  design — plan data migration accordingly.
