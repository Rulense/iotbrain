---
title: "Process 'Killed' loading a model on Jetson — GPU shares system RAM (unified memory): swap strategy, GUI off, zram trade-offs"
type: gotcha
company: nvidia
keys:
  - "Out of memory: Killed process"
  - "invoked oom-killer"
  - "nvzramconfig"
  - "systemctl set-default multi-user.target"
  - "process killed loading model"
  - "runs out of memory loading model"
platform_versions: ["all"]
devices: [all]
status: unverified
sources:
  - "https://www.jetson-ai-lab.com/tutorials/ram-optimization/"
  - "https://forums.developer.nvidia.com/t/how-jetson-allocate-memory-for-gpu/356364"
---
## Context
Loading an LLM/vision model, the process dies with a bare `Killed` in the
terminal, or CUDA reports out-of-memory while `free` looked fine moments
before. Worst on Orin Nano 8GB/4GB. Applies to **all** Jetsons because the
architecture is universal: there is no dedicated VRAM — CPU and GPU share the
same LPDDR pool, so "GPU memory" and "system RAM" are one budget.

## Knowledge
### Root cause
Model weights + CUDA context + OS + desktop all come out of one RAM pool.
When it's exhausted the kernel OOM killer picks your process; the shell shows
only `Killed` — the real record is in the kernel log:
```bash
sudo dmesg -T | grep -Ei "oom|Killed process"
# "... invoked oom-killer ...", "Out of memory: Killed process <pid> (python3)"
```

### Reclaiming headroom (jetson-ai-lab RAM-optimization recipe)
1. **Disable the desktop GUI** (~800 MB back):
   ```bash
   sudo init 3                                    # try it now
   sudo systemctl set-default multi-user.target   # persist (graphical.target to undo)
   ```
2. **Swap zram for real NVMe swap.** Default L4T zram (`nvzramconfig`) carves
   compressed swap out of RAM itself — no help when a big model is the
   problem. Prefer disk swap on NVMe:
   ```bash
   sudo systemctl disable nvzramconfig
   sudo fallocate -l 16G /ssd/16GB.swap
   sudo mkswap /ssd/16GB.swap
   sudo swapon /ssd/16GB.swap
   echo "/ssd/16GB.swap  none  swap  sw 0  0" | sudo tee -a /etc/fstab
   ```
3. **Disable unused services**, e.g. `sudo systemctl disable nvargus-daemon.service`
   when no camera is attached.
4. **Right-size the model** — swap only pages out ordinary CPU-side memory;
   CUDA/pinned GPU allocations cannot be swapped. Swap stops the OOM killer
   and helps loading/conversion phases, but it will not make an oversized
   model's working set fit — use a smaller quantization instead.

## Verify
`free -h` shows the reclaimed RAM; `swapon --show` lists the NVMe swapfile;
the model loads without `Killed` and `sudo dmesg | grep -i oom` stays clean.

## Gotchas
- `tegrastats` `RAM` includes GPU allocations — watch it during model load to
  see the true budget (`runtime/tegrastats-fields-decoder.md`).
- Frameworks splitting layers between CPU and GPU (e.g. ollama offload) is the
  same budget problem wearing a different hat.
- Same recipe fixes `cc1plus` deaths during big compiles — covered from the
  build angle in `sdk-dev/on-device-builds-swap-and-clocks.md`.
- Swap on SD card works but is painfully slow and wears the card; use NVMe.
