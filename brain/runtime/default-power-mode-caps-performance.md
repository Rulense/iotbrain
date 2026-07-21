---
title: Default power mode silently caps Jetson performance
type: gotcha
company: nvidia
keys:
  - "nvpmodel"
  - "jetson_clocks"
  - "slow inference jetson"
platform_versions: ["all"]
devices: [all]
status: verified
verified_on: "Orin Nano, JetPack 6.1, 2026-07-17"
sources: ["https://docs.nvidia.com/jetson/archives/r36.3/DeveloperGuide/SD/PlatformPowerAndPerformance.html"]
---
## Context
Any benchmark, inference, or build task on a freshly flashed Jetson. Results look
2–4x slower than published numbers.

## Knowledge
Jetsons ship in a conservative power mode with dynamic clock scaling. Before
measuring or comparing performance:

```bash
sudo nvpmodel -q          # show current mode
sudo nvpmodel -m 0        # highest-power mode on most boards (MAXN where available)
sudo jetson_clocks        # pin clocks to max for the current mode
```

Mode numbering differs per module — always check `nvpmodel -q` output rather than
assuming mode 0.

## Verify
`sudo nvpmodel -q` shows the intended mode; `tegrastats` shows clocks pinned.

## Gotchas
- `jetson_clocks` does not survive reboot.
- Higher modes need adequate power supply; undersized USB-C supplies cause
  over-current throttling warnings.
