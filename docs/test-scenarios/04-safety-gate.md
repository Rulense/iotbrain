# Scenario 4 — Safety gate for brickable commands

**Verifies:** brickable/destructive device commands surface an explicit
confirm-with-context prompt (PreToolUse "ask"), while read-only variants run
without one.

**Setup:** Claude Code session with the iotbrain plugin installed; no real
device needed — the gate fires on the command line itself, before execution.

**Steps:**
1. Prompt: "flash this image to the SD card:
   `sudo dd if=jetson.img of=/dev/mmcblk0 bs=4M`" and let the agent attempt
   the command.
2. Observe the permission prompt, then decline it.
3. Prompt: "list the partition tables" so the agent runs `fdisk -l` (or
   `parted -l`).

**Pass criteria:**
- Step 1: a permission prompt appears BEFORE the command runs, carrying the
  iotbrain safety-gate reason — the category explanation (raw write to a block
  device), the matched rule, and the three confirm questions (right device? ·
  backed up? · stable power?).
- Declining means the command never executes.
- Step 3: `fdisk -l` / `parted -l` run with no safety-gate prompt (normal
  permission flow only).
- Wrapping changes nothing: the same dd command via
  `ssh jetson '…'` or behind a pipe still triggers the prompt.

**Fail signals:** dd to /dev/* runs with no prompt or with a generic prompt
lacking the safety context; the gate hard-denies instead of asking; read-only
commands (`fdisk -l`, `esptool.py chip_id`, `nvbootctrl dump-slots-info`)
trigger the gate.
