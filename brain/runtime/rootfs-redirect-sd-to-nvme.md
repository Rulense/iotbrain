---
title: "Move a running Jetson's rootfs from SD to NVMe without reflashing — copy rootfs, point extlinux.conf root= at /dev/nvme0n1p1"
type: recipe
company: nvidia
keys:
  - "root=/dev/nvme0n1p1"
  - "/boot/extlinux/extlinux.conf"
  - "APPEND ${cbootargs}"
  - "rootwait"
  - "move rootfs to ssd"
  - "boot from nvme without reflash"
platform_versions: ["JetPack 4.x", "JetPack 5.x", "JetPack 6.x", "L4T 32.x", "L4T 35.x", "L4T 36.x"]
devices: [orin-nano, orin-nx, xavier-nx, agx-xavier]
status: unverified
sources:
  - "https://forums.developer.nvidia.com/t/jetson-orin-nano-flash-microsd-image-to-nvme-ssd/287300"
  - "https://forums.developer.nvidia.com/t/mounting-rootfs-from-nvme-ssd-at-boot/224560"
  - "https://github.com/jetsonhacks/rootOnNVMe"
---
## Context
A Jetson already set up and running from SD card (or eMMC) gets an NVMe SSD,
and you want the rootfs on the fast disk **without** a host PC and reflash.
The no-reflash route: the bootloader keeps loading the kernel from the SD's
`/boot`, and only the root filesystem is redirected via the kernel cmdline.
(For a clean from-scratch install, flashing straight to NVMe is the better
path — see `setup/orin-nano-nvme-initrd-flash.md`.)

## Knowledge
1. Partition and format the SSD (GPT, single ext4 partition), then copy the
   live rootfs:
   ```bash
   sudo mkfs.ext4 /dev/nvme0n1p1
   sudo mount /dev/nvme0n1p1 /mnt
   sudo rsync -axHAWX --numeric-ids --info=progress2 / /mnt
   ```
   (`-x` stays on one filesystem — no /proc, /sys, or the SSD itself.
   jetsonhacks' `rootOnNVMe` scripts automate this copy for Xavier-era boards.)
2. Edit `/boot/extlinux/extlinux.conf` **on the SD card** (the boot device —
   this is the copy the bootloader actually reads). In the `APPEND` line
   change only the root device, e.g.:
   ```
   APPEND ${cbootargs} ... root=/dev/nvme0n1p1 rw rootwait ...
   ```
   Keep everything else identical, and keep `rootwait` — NVMe can enumerate
   after the kernel would otherwise try to mount root.
3. Safer variant: duplicate the whole `LABEL primary` block first, give the
   copy `root=/dev/nvme0n1p1`, and keep the original SD entry as a fallback
   selectable over serial console.
4. Reboot and confirm root moved (step below). Leave the SD card inserted
   permanently: kernel, DTB, initrd, and `extlinux.conf` still live there.

## Verify
```bash
findmnt /          # SOURCE = /dev/nvme0n1p1
lsblk              # nvme0n1p1 mounted at /
```

## Gotchas
- **Kernel updates land on the wrong /boot.** Once root is NVMe, apt writes
  kernel/DTB updates to the NVMe's `/boot`, but the bootloader reads the SD's
  `/boot`. Either mount the SD boot partition over `/boot` via fstab, or copy
  `/boot` back to the SD after kernel/bootloader package updates — otherwise
  the running kernel silently stops matching the installed one.
- The old rootfs is still on the SD; if the cmdline edit is lost (e.g. a
  restored `extlinux.conf`), the board quietly boots the stale SD rootfs —
  check `findmnt /` when the system "forgot" recent changes.
- With two NVMe slots (Orin devkits), the SSD you mean may be `nvme1n1` —
  verify with `lsblk` before writing the cmdline.
- On the original Jetson Nano and Xavier-era CBoot, boot-order quirks apply
  (source thread 224560); Orin's UEFI reads `extlinux.conf` from the SD as
  long as the SD is first in the boot order.
