---
title: "Wi-Fi drops on an idle Jetson and never reconnects — disable wifi.powersave / iw power_save"
type: fix
company: nvidia
keys:
  - "wifi.powersave = 2"
  - "default-wifi-powersave-on.conf"
  - "iw dev wlan0 set power_save off"
  - "Power save: on"
  - "authentication with"
platform_versions: ["all"]
devices: [all]
status: unverified
sources:
  - "https://forums.developer.nvidia.com/t/disable-wifi-powersave/70410"
  - "https://forums.developer.nvidia.com/t/jetson-nano-disconnects-from-wifi-and-never-reconnects/116306"
  - "https://github.com/robwaat/Tutorial/blob/master/Jetson%20Disable%20Wifi%20Power%20Management.md"
---
## Context
A headless/deployed Jetson on Wi-Fi works for hours or days, then silently drops
off the network and never comes back until someone reboots it or runs
`sudo systemctl restart NetworkManager`. Kernel log shows repeats of
`wlan0: authentication with <AP MAC> timed out`. Also shows up as high, spiky
SSH latency when the link is idle.

## Knowledge
### Root cause
Wi-Fi power management. Ubuntu/L4T ships
`/etc/NetworkManager/conf.d/default-wifi-powersave-on.conf` with
`wifi.powersave = 3` (enabled), so the radio sleeps between beacons. Some Jetson
Wi-Fi drivers (bcmdhd on TX2-era modules, several USB dongles) handle the wake
path badly and the association dies instead of resuming.

### Fix
1. Tell NetworkManager to stop enabling power save — edit
   `/etc/NetworkManager/conf.d/default-wifi-powersave-on.conf`:
   ```
   [connection]
   wifi.powersave = 2
   ```
   (2 = disable, 3 = enable), then `sudo systemctl restart NetworkManager`.
2. Check it took effect: `iw dev wlan0 get power_save` → `Power save: off`.
3. Some drivers re-enable power save regardless of the NetworkManager setting.
   If step 2 still shows `on` (or the value reverts after reconnect), force it
   at boot with a systemd unit:
   ```
   [Unit]
   Description=Disable wlan0 power save
   After=network.target

   [Service]
   Type=oneshot
   ExecStart=/usr/bin/env iw dev wlan0 set power_save off

   [Install]
   WantedBy=multi-user.target
   ```
   (`/usr/bin/env` sidesteps the `iw` path difference: `/sbin/iw` on
   JetPack 4 / Ubuntu 18.04, `/usr/sbin/iw` on newer releases.)

## Verify
`iw dev wlan0 get power_save` reports `Power save: off` and the device stays
reachable across multi-day idle periods (watch with a ping/uptime monitor).

## Gotchas
- Fleets flashed from one image often share the default hostname (`nvidia` /
  `ubuntu`); several identical hostnames on one router can cause DHCP/mDNS
  conflicts that look exactly like this — rename each unit.
- Power save off is a mitigation, not a cure-all: an AGX Orin thread
  (forums 273683) reports drops that persist across JetPack 5.1.x/6.0 with no
  marked solution. If drops continue, capture `journalctl -u NetworkManager`
  and `dmesg` around the event before blaming power save.
- The interface name may not be `wlan0` (check `iw dev`), and USB dongles may
  need their own out-of-tree driver options.
