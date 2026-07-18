---
title: "Big on-device builds on Jetson — cc1plus killed by OOM: disable zram, add NVMe swap, max clocks, lower -j"
type: recipe
company: nvidia
keys:
  - "internal compiler error: Killed (program cc1plus)"
  - "fatal error: Killed signal terminated program cc1plus"
  - "sudo systemctl disable nvzramconfig"
  - "fallocate -l 16G"
  - "jetson_clocks"
jetpack: ["all"]
l4t: ["all"]
devices: [all]
status: verified
verified_on: "AGX Orin / Orin Nano, JetPack 6.x (Jetson AI Lab RAM-optimization tutorial publishes these exact commands for Orin), doc checked 2026-07-17"
sources:
  - "https://www.jetson-ai-lab.com/tutorials/ram-optimization/"
  - "https://jetsonhacks.com/2019/04/14/jetson-nano-use-more-memory/"
  - "https://jetsonhacks.com/2019/11/28/jetson-nano-even-more-swap/"
---
## Context
Compiling anything large on the Jetson itself (OpenCV, PyTorch extensions,
big CMake projects) dies partway with the compiler killed by the OOM killer —
`internal compiler error: Killed (program cc1plus)` or
`fatal error: Killed signal terminated program cc1plus` — or crawls for
hours. Jetson RAM is unified (CPU+GPU share it) and the default swap is
compressed zram carved out of that same RAM, which does not help compiles.
Applies to all JetPack releases; zram via `nvzramconfig` is the default
throughout.

## Knowledge
1. Replace zram with real swap on fast storage (NVMe preferred, per the
   Jetson AI Lab tutorial; adjust the path to your mount):

   ```bash
   sudo systemctl disable nvzramconfig
   sudo fallocate -l 16G /ssd/16GB.swap
   sudo mkswap /ssd/16GB.swap
   sudo swapon /ssd/16GB.swap
   ```

   Persist in `/etc/fstab`:

   ```
   /ssd/16GB.swap  none  swap  sw 0  0
   ```

2. Max clocks so the build uses the hardware you have:

   ```bash
   sudo nvpmodel -m 0        # check modes first: sudo nvpmodel -q --verbose
   sudo jetson_clocks
   ```

3. Cap build parallelism to fit RAM: each C++ compile job can take 1–2+ GB,
   so on an 8 GB Orin Nano use `make -j4` (or less for template-heavy code)
   instead of `make -j$(nproc)`.

4. Optionally free ~800 MB by dropping the desktop for the duration:
   `sudo systemctl set-default multi-user.target` and reboot
   (revert with `sudo systemctl set-default graphical.target`).

## Verify
`swapon --show` lists your file swap (and no /dev/zram* after a reboot);
`free -h` shows the new swap total; the previously failing build completes.

## Gotchas
- zram is the right default for *runtime* memory pressure — it compresses in
  RAM. It is the wrong tool for builds, which need real spill space. For
  inference workloads you may want it back afterwards
  (`sudo systemctl enable nvzramconfig`).
- Put the swapfile on NVMe, not the SD card: SD swap is painfully slow and
  wears the card.
- `fallocate` size is not the limit — some PyTorch/OpenCV builds want
  more than 8 GB of swap on 8 GB boards; 16 GB is the tutorial default.
- Linker steps (`ld` on large static archives) OOM too; `-j1` for the link
  or `gold`/`lld` can be the difference.
