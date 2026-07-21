---
title: "Bookworm moved the Raspberry Pi boot partition to /boot/firmware — edits to /boot/config.txt are silently ignored"
type: gotcha
company: raspberry-pi
keys:
  - "/boot/firmware/config.txt"
  - "/boot/firmware/cmdline.txt"
  - "/boot/config.txt"
  - "config.txt changes have no effect"
  - "old guide edits wrong file"
platform_versions: ["Raspberry Pi OS Bookworm+"]
devices: [all]
status: verified
verified_on: "doc checked 2026-07-21 (raspberrypi.com config_txt.html: boot partition located at /boot/firmware/)"
sources:
  - "https://www.raspberrypi.com/documentation/computers/config_txt.html"
  - "https://www.raspberrypi.com/news/bookworm-the-new-version-of-raspberry-pi-os/"
---
## Context
You followed a pre-2023 guide ("add dtoverlay=... to /boot/config.txt",
"edit /boot/cmdline.txt") on Raspberry Pi OS Bookworm or later and nothing
changed after reboot. Since Bookworm (October 2023), the FAT boot partition
is mounted at `/boot/firmware/`; `/boot` is now just a directory on the ext4
rootfs. Applies to every Pi model running Bookworm+ (hence devices: all).

## Knowledge
The firmware reads `config.txt` and `cmdline.txt` from the FAT boot
partition. On Bookworm+ that partition is mounted at `/boot/firmware/`, so
the live files are:

```
/boot/firmware/config.txt
/boot/firmware/cmdline.txt
```

Writing to `/boot/config.txt` on Bookworm creates a plain file on the rootfs
that the firmware never sees — the edit "takes" but has no effect. The same
applies to anything a guide says to drop into "the boot partition": `ssh`,
`userconf.txt`, `custom.toml` all belong in `/boot/firmware/` on a running
system (or the root of the FAT partition when the SD/SSD is mounted on
another computer — that part is unchanged).

Confirm the layout on any system:

```bash
findmnt /boot/firmware   # Bookworm+: the FAT vfat partition
ls -l /boot/config.txt   # if this exists on Bookworm, it's an orphan copy
```

## Verify
After moving the change into `/boot/firmware/config.txt` and rebooting,
`vcgencmd get_config <name>` (or the overlay's effect, e.g.
`rpicam-hello --list-cameras`) reflects it.

## Gotchas
- Same-era trap: Bookworm also switched networking to NetworkManager —
  `/etc/dhcpcd.conf` static-IP guides and boot-partition
  `wpa_supplicant.conf` provisioning no longer work either.
- Scripts that hardcode `/boot/config.txt` may run fine on Bullseye devices
  in the same fleet — a fleet-wide script needs to pick the path by checking
  which file is on the vfat mount.
- Delete any orphan `/boot/config.txt` you created; the next person to debug
  the box will read the wrong file.
