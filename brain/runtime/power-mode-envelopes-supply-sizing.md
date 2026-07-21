---
title: "Jetson power-mode envelopes vs supply sizing — Orin Nano/NX/AGX Orin/Thor wattage tables, MAXN caveats, devkit adapter limits"
type: matrix
company: nvidia
keys:
  - "nvpmodel -m 0"
  - "MAXN_SUPER"
  - "ADP-240LB"
  - "power mode wattage table"
  - "size the power supply"
  - "jetson power budget"
platform_versions: ["JetPack 6.x", "JetPack 7.x", "L4T 36.x", "L4T 38.x"]
devices: [orin-nano, orin-nx, agx-orin, agx-thor]
status: verified
verified_on: "doc checked 2026-07-21"
sources:
  - "https://docs.nvidia.com/jetson/archives/r36.5/DeveloperGuide/SD/PlatformPowerAndPerformance/JetsonOrinNanoSeriesJetsonOrinNxSeriesAndJetsonAgxOrinSeries.html"
  - "https://docs.nvidia.com/jetson/archives/r38.4/DeveloperGuide/SD/PlatformPowerAndPerformance/JetsonThor.html"
---
## Context
Two recurring engineering mistakes: sizing a product's power supply to a
module's *default* nvpmodel budget (then MAXN browns it out in the field), and
reading MAXN as a guaranteed-performance mode (it's uncapped and throttles
itself). This matrix collects the documented mode envelopes so supply sizing is
done against the real ceiling.

## Knowledge
Documented power-mode budgets per module (mode IDs vary by module/release —
confirm on-unit with `sudo nvpmodel -q` and `/etc/nvpmodel.conf`):

| Module | Modes (default bold) |
|--------|----------------------|
| Orin Nano 4GB | **10W**, 7W_AI, 7W_CPU (+ MAXN SUPER, uncapped, with Super config) |
| Orin Nano 8GB | **15W**, 7W (+ MAXN SUPER, uncapped, with Super config) |
| Orin NX 8/16GB | MAXN, 10W, **15W**, 20–25W (+ MAXN SUPER / 40W-class modes on Super configs) |
| AGX Orin 32GB | 15W, **30W**, 40W, MAXN |
| AGX Orin 64GB | 15W, **30W**, 50W, MAXN |
| AGX Orin Industrial | 15W, **35W**, 60W, MAXN |
| AGX Thor T5000 | MAXN (0), **120W** (1, default), 90W (2), 70W (3) |

MAXN caveats, straight from the docs:
- MAXN/MAXN SUPER is "an unconstrained power mode", and "hardware throttling is
  engaged when the total module power exceeds the TDP budget" — so it does not
  guarantee best sustained performance.
- NVIDIA: "we don't recommend running heavy workloads for prolonged periods in
  this mode."
- Transients exceed the budget label: the instantaneous limit on the
  CPU_CV_GPU_SOC rail summation "is slightly higher than TDP power budget."

Supply sizing rules that follow:
- Size for the *largest mode you'll ever allow* plus carrier board, peripherals
  (USB loads, PCIe/NVMe, cameras) and transient headroom — the table numbers
  are module TDP budgets, not system draw.
- Thor devkit reference point: the bundled ADP-240LB adapter delivers up to
  140 W (28 V x 5 A), and the devkit enforces a 168 W limit specifically to
  avoid tripping the adapter's overcurrent protection — third-party supplies
  need equivalent headroom, not "130 W because the SoC says so".
- Orin Nano devkit under-supply symptoms and the 19 V / 4 A+ guidance live in
  `runtime/over-current-throttling-warning.md`; mode-selection basics in
  `runtime/default-power-mode-caps-performance.md`.

## Verify
`sudo nvpmodel -q` shows the active mode; `sudo tegrastats` under worst-case
load shows rail power (VDD fields) within your supply's continuous rating with
margin; no `oc*_event_cnt` increments (over-current events) during stress.

## Gotchas
- Locking clocks (`jetson_clocks`) inside a small power mode doesn't raise the
  budget — it just pins frequencies within it; switch modes first.
- A supply sized to the default mode "works" until someone runs
  `sudo nvpmodel -m 0` in the field — fix the supply or lock the allowed modes
  in your image.
- Mode tables shift between L4T releases (Super configs added modes on Orin
  Nano/NX; Thor gained 90W/70W by r38.4) — re-check `/etc/nvpmodel.conf` after
  every JetPack upgrade.
