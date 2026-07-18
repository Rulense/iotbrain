---
title: "Change the Jetson Orin fan profile (quiet vs cool) — edit /etc/nvfancontrol.conf AND delete /var/lib/nvfancontrol/status"
type: config
company: nvidia
keys:
  - "nvfancontrol"
  - "FAN_DEFAULT_PROFILE"
  - "/var/lib/nvfancontrol/status"
  - "jetson_clocks --fan"
jetpack: ["5.x", "6.x"]
l4t: ["35.x", "36.x"]
devices: [orin-nano, orin-nx, agx-orin]
status: verified
verified_on: "Procedure per NVIDIA L4T r36.5 Developer Guide (Platform Power and Performance, Orin series); same steps discussed on Orin Nano forum thread 304599; docs retrieved 2026-07-18"
sources:
  - "https://docs.nvidia.com/jetson/archives/r36.5/DeveloperGuide/SD/PlatformPowerAndPerformance/JetsonOrinNanoSeriesJetsonOrinNxSeriesAndJetsonAgxOrinSeries.html"
  - "https://forums.developer.nvidia.com/t/how-to-modify-etc-nvfancontrol-conf-for-fan-speed-control/304599"
---
## Context
The fan feels too passive under load (device runs hot, throttles) or too loud
at idle. On Orin-family boards the `nvfancontrol` daemon owns the fan; it ships
two profiles — `quiet` and `cool` — and the default differs by module:
**Orin Nano / Orin NX default to `quiet`**, AGX Orin defaults to `cool`.

## Knowledge
Profiles live in `/etc/nvfancontrol.conf` as temperature→PWM/RPM step tables:
```
FAN_PROFILE <name> {
    #TEMP  HYST  PWM  RPM
    ...
}
```
`FAN_DEFAULT_PROFILE` selects the active one. To switch (e.g. to `cool` so the
fan ramps earlier and harder):

```bash
sudo systemctl stop nvfancontrol
sudo sed -i 's/FAN_DEFAULT_PROFILE quiet/FAN_DEFAULT_PROFILE cool/' /etc/nvfancontrol.conf
sudo rm /var/lib/nvfancontrol/status      # REQUIRED — cached state overrides the conf
sudo systemctl start nvfancontrol
```

The `rm /var/lib/nvfancontrol/status` step is the one everyone misses: the
daemon persists its last profile there (it survives reboots and SC7), so
editing the conf alone appears to do nothing.

Other controls:
- `sudo nvfancontrol -q` — query the currently active profile.
- `sudo jetson_clocks --fan` — pin the fan to 100% (not persistent; gone at
  reboot, and nvfancontrol resumes control when restarted).
- Manual PWM (for testing only): stop the daemon first, then
  `echo 255 | sudo tee /sys/devices/platform/pwm-fan/hwmon/hwmon*/pwm1`.

## Verify
`sudo nvfancontrol -q` reports the new profile; under a sustained load the fan
audibly ramps earlier and `tegrastats` temps plateau lower than before.

## Gotchas
- Edited the conf, no change after reboot → you skipped deleting
  `/var/lib/nvfancontrol/status`.
- Two control loops exist: open-loop uses the PWM column (RPM ignored),
  closed-loop targets the RPM column (PWM ignored) — set values in the column
  your `FAN_CONTROL` mode actually reads.
- If the fan still can't hold temps below the throttle point, the problem is
  thermal budget, not the profile — see
  `runtime/thermal-throttling-trip-points.md`.
