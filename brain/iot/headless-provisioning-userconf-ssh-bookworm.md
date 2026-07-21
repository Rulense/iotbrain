---
title: "Headless Raspberry Pi provisioning on Bookworm — ssh file + userconf.txt (no default pi user), Imager OS customisation"
type: recipe
company: raspberry-pi
keys:
  - "userconf.txt"
  - "openssl passwd -6"
  - "wpa_supplicant.conf"
  - "no default pi user"
  - "ssh connection refused after flashing"
  - "cannot log in headless"
platform_versions: ["Raspberry Pi OS Bookworm+"]
devices: [all]
status: verified
verified_on: "doc checked 2026-07-21 (raspberrypi.com remote-access.html headless + bullseye-update-april-2022 news)"
sources:
  - "https://www.raspberrypi.com/documentation/computers/remote-access.html#set-up-a-headless-raspberry-pi"
  - "https://www.raspberrypi.com/news/raspberry-pi-bullseye-update-april-2022/"
  - "https://www.raspberrypi.com/documentation/computers/getting-started.html"
---
## Context
Flashing Pi OS for a device that will never see a monitor or keyboard.
Since the April 2022 release there is no default `pi`/`raspberry` login —
an image booted with no user configured is unreachable, and on Bookworm the
old trick of dropping `wpa_supplicant.conf` in the boot partition no longer
configures Wi-Fi (NetworkManager replaced dhcpcd/wpa_supplicant). Applies to
every Pi model (devices: all) — provisioning is an OS mechanism.

## Knowledge
Preferred: Raspberry Pi Imager's OS customisation dialog (offered before
writing) — set hostname, username/password, Wi-Fi SSID/password + country,
and enable SSH (password or public-key only) in one shot.

Manual (image already flashed): put two files in the root of the FAT boot
partition (from another computer: the partition root; on a running Bookworm
Pi: `/boot/firmware/`):

```bash
# 1. enable ssh: empty file named exactly "ssh"
touch ssh

# 2. create the first user: userconf.txt, one line, username:encrypted-password
echo 'mypassword' | openssl passwd -6 -stdin      # → $6$...hash...
echo 'myuser:$6$...hash...' > userconf.txt
```

Both files are consumed on first boot: the user is created, SSH comes up on
port 22, and the files are removed. Wi-Fi cannot be provisioned this way on
Bookworm — use Imager customisation, Ethernet for first boot, or bake
NetworkManager profiles (`/etc/NetworkManager/system-connections/`) into the
image.

## Verify
First boot (give it a minute for the resize + user creation), then:
`ssh myuser@<hostname>.local` — logs in with the password you hashed.
`raspi-config nonint` or `nmcli` can finish device-specific setup from there.

## Gotchas
- `userconf.txt` goes in the boot partition root — putting it in rootfs
  `/boot` on Bookworm does nothing (the live partition is `/boot/firmware/`).
- The hash must be one line, no trailing whitespace; `openssl passwd -6`
  (SHA-512 crypt) is the documented format.
- Imager's saved customisation quietly reapplies old Wi-Fi credentials to
  new cards — recheck the dialog when provisioning for a different site.
- Old fleet scripts that inject `wpa_supplicant.conf` still work on Bullseye
  images but silently do nothing on Bookworm+.
