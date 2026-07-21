#!/usr/bin/env python3
"""iotbrain safety gate — PreToolUse hook for brickable device commands.

Claude Code invokes this hook before every Bash tool call (see
https://code.claude.com/docs/en/hooks). It reads the PreToolUse JSON payload
from stdin and checks the command against a registry of operations that can
brick or wipe an edge device: raw disk writes, partitioning/formatting,
firmware flashing, fuse/bootloader changes, and boot-critical config edits.

On a match it emits the documented JSON with
`hookSpecificOutput.permissionDecision: "ask"` so the user gets an explicit
confirm-with-context prompt — not a silent allow, not a hard deny. On no
match it exits 0 with no output, which lets the normal permission flow
continue.

Matching is regex on the command line (through `sudo`, `ssh host '...'`,
`sh -c`, pipes and `&&`/`;` chains) — deliberately favoring catching too much
over too little, with targeted read-only exemptions per tool (`fdisk -l`,
`parted print`, `esptool.py chip_id`, `nvbootctrl dump-slots-info`, ...).

Stdlib only. Ships with the iotbrain plugin via hooks/hooks.json.
"""

import json
import re
import sys

# Block-device-ish /dev targets, excluding sinks/character devices that are
# harmless to write to.
_DEV_HARMLESS = r"(?!null\b|zero\b|full\b|std|random\b|urandom\b|tty|pts/|ptmx\b|fd/|shm/|snd|input/)"

# Boot-critical files. Full paths for generic names (config.txt is too common
# bare); distinctive names (extlinux.conf, cmdline.txt) also match bare.
_BOOT_FILES = (
    r"(?:extlinux\.conf|/etc/fstab|/boot/firmware/config\.txt"
    r"|/boot/config\.txt|cmdline\.txt)"
)

CATEGORIES = {
    "raw-disk-write": (
        "writes raw data directly to a block device — pointed at the wrong "
        "disk it destroys data or the OS irrecoverably"
    ),
    "partition-format": (
        "repartitions or reformats a disk — existing partitions, filesystems, "
        "and the device's boot layout can be destroyed"
    ),
    "device-flash": (
        "flashes device firmware or an OS image — an interrupted or "
        "wrong-target flash can brick the board"
    ),
    "fuse-bootloader": (
        "programs fuses or changes bootloader/boot-slot state — this can be "
        "IRREVERSIBLE and permanently brick the device"
    ),
    "boot-config": (
        "modifies a boot-critical configuration file — a bad edit can leave "
        "the device unbootable"
    ),
}

# Each rule: name (shown to the user), category, pattern (danger match),
# readonly (exemptions: if any matches the same candidate string, the rule
# does not fire for it). `[^|;&]*` keeps a match inside one pipeline segment
# when scanning the whole command line.
RULES = [
    # --- Raw disk writes --------------------------------------------------
    {
        "name": "dd writing to a block device (of=/dev/*)",
        "category": "raw-disk-write",
        "pattern": r"\bdd\b[^|;&]*\bof=[\"']?/dev/" + _DEV_HARMLESS,
    },
    {
        "name": "shell redirect into a block device (> /dev/*)",
        "category": "raw-disk-write",
        "pattern": r">>?\s*[\"']?/dev/" + _DEV_HARMLESS,
    },
    {
        "name": "blkdiscard",
        "category": "raw-disk-write",
        "pattern": r"\bblkdiscard\b",
    },
    {
        "name": "wipefs on a device",
        "category": "raw-disk-write",
        "pattern": r"\bwipefs\b[^|;&]*\s[\"']?/dev/",
        "readonly": [r"\bwipefs\b[^|;&]*(?:\s-n\b|--no-act\b)"],
    },
    {
        "name": "shred on a block device",
        "category": "raw-disk-write",
        "pattern": r"\bshred\b[^|;&]*\s[\"']?/dev/",
    },
    # --- Partitioning / formatting -----------------------------------------
    {
        "name": "fdisk on a device (write mode)",
        "category": "partition-format",
        "pattern": r"\bfdisk\b[^|;&]*\s[\"']?/dev/",
        "readonly": [r"\bfdisk\b\s+(?:-\w+\s+)*(?:-l|--list)\b"],
    },
    {
        "name": "parted on a device (write mode)",
        "category": "partition-format",
        "pattern": r"\bparted\b[^|;&]*\s[\"']?/dev/",
        "readonly": [
            r"\bparted\b[^|;&]*(?:\s-l\b|--list\b)",
            # `print` family only, with no write subcommand in the same segment
            r"\bparted\b(?![^|;&]*(?:mklabel|mktable|mkpart|resizepart"
            r"|\brm\b|\bset\b|disk_set|\bname\b|toggle\b))[^|;&]*\bprint\b",
        ],
    },
    {
        "name": "sgdisk on a device (write mode)",
        "category": "partition-format",
        "pattern": r"\bsgdisk\b[^|;&]*\s[\"']?/dev/",
        "readonly": [
            # Every sgdisk argument is a read-only flag (-p/-i/-v) + the device
            r"\bsgdisk\b\s+(?:(?:-p|--print|-i[= ]?\d*|--info[= ]?\d*|-v|--verify)\s+)*"
            r"(?:-p|--print|-i[= ]?\d*|--info[= ]?\d*|-v|--verify)\s+[\"']?/dev/\S+[\"']?\s*$",
        ],
    },
    {
        "name": "mkfs on a device",
        "category": "partition-format",
        "pattern": r"\bmkfs(?:\.\w+)?\b[^|;&]*\s[\"']?/dev/",
    },
    # --- Device flashing ----------------------------------------------------
    {
        "name": "flash.sh (NVIDIA Jetson flashing)",
        "category": "device-flash",
        "pattern": r"(?:^|[\s/;(&|])flash\.sh\b",
    },
    {
        "name": "l4t_initrd_flash (NVIDIA Jetson initrd flashing)",
        "category": "device-flash",
        "pattern": r"\bl4t_initrd_flash(?:\.sh)?\b",
    },
    {
        "name": "sdkmanager flash",
        "category": "device-flash",
        "pattern": r"\bsdkmanager\b[^|;&]*\bflash\b",
    },
    {
        "name": "esptool write_flash/erase_flash/erase_region",
        "category": "device-flash",
        "pattern": r"\besptool(?:\.py)?\b[^|;&]*\b(?:write_flash|erase_flash|erase_region)\b",
    },
    {
        "name": "dfu-util (device firmware update)",
        "category": "device-flash",
        "pattern": r"\bdfu-util\b",
        "readonly": [r"\bdfu-util\b[^|;&]*(?:\s-l\b|--list\b|\s-U\b|--upload\b)"],
    },
    {
        "name": "fastboot flash/erase/format",
        "category": "device-flash",
        "pattern": r"\bfastboot\b[^|;&]*\b(?:flash|erase|format|flashing)\b",
    },
    # --- Fuse / bootloader (irreversible) ------------------------------------
    {
        "name": "odmfuse.sh (Jetson fuse burning)",
        "category": "fuse-bootloader",
        "pattern": r"\bodmfuse(?:\.sh)?\b",
    },
    {
        "name": "nvbootctrl (boot slot change)",
        "category": "fuse-bootloader",
        "pattern": r"\bnvbootctrl\b",
        "readonly": [
            r"\bnvbootctrl\b(?:\s+-t\s+\S+)?\s+(?:dump-slots-info|get-current-slot"
            r"|get-number-slots|get-slot-status|is-slot-bootable"
            r"|is-slot-marked-successful|get-suffix)\b",
        ],
    },
    {
        "name": "efibootmgr with write flags",
        "category": "fuse-bootloader",
        "pattern": r"\befibootmgr\b[^|;&]*(?:\s-[bBcCoOnNaAtTD]\b"
        r"|--(?:create(?:-only)?|bootorder|delete|bootnext|delete-bootnext"
        r"|delete-bootorder|timeout|delete-timeout|active|inactive|remove-dups)\b)",
    },
    {
        "name": "espefuse (ESP32 efuse burning)",
        "category": "fuse-bootloader",
        "pattern": r"\bespefuse(?:\.py)?\b",
        "readonly": [
            r"\bespefuse(?:\.py)?\b(?![^|;&]*\bburn_)[^|;&]*"
            r"\b(?:summary|dump|check_error|adc_info|get_custom_mac)\b",
        ],
    },
    # --- Boot-critical file edits --------------------------------------------
    {
        "name": "shell redirect into a boot-critical file",
        "category": "boot-config",
        "pattern": r">>?\s*[\"']?\S*" + _BOOT_FILES,
    },
    {
        "name": "tee into a boot-critical file",
        "category": "boot-config",
        "pattern": r"\btee\b\s+(?:-\w+\s+)*[\"']?\S*" + _BOOT_FILES,
    },
    {
        "name": "sed -i on a boot-critical file",
        "category": "boot-config",
        "pattern": r"\bsed\b[^|;&]*\s-i\S*\s[^|;&]*" + _BOOT_FILES,
    },
]

for _rule in RULES:
    _rule["pattern_re"] = re.compile(_rule["pattern"])
    _rule["readonly_re"] = [re.compile(r) for r in _rule.get("readonly", [])]


def split_segments(command):
    """Split a command line on pipes, &&, ||, ; and newlines.

    Naive (does not honor quoting) — but the whole command line is always
    also scanned as one candidate, so quoted separators can't hide a match.
    """
    return [s for s in re.split(r"\s*(?:\|\|?|&&|;|\n)\s*", command) if s]


def evaluate(command):
    """Return the first matching rule for a command line, or None."""
    candidates = [command] + split_segments(command)
    for rule in RULES:
        for candidate in candidates:
            if not rule["pattern_re"].search(candidate):
                continue
            if any(ro.search(candidate) for ro in rule["readonly_re"]):
                continue  # read-only use of this tool in this candidate
            return rule
    return None


def build_reason(rule):
    return (
        "⚠️ iotbrain safety gate: this command "
        + CATEGORIES[rule["category"]]
        + " (matched: "
        + rule["name"]
        + "). Before approving, confirm: right device? (`lsblk`/device facts "
        "checked) · data backed up? · stable power? Approve only if all "
        "three hold."
    )


def main():
    try:
        payload = json.load(sys.stdin)
    except (ValueError, UnicodeDecodeError):
        return 0  # unparseable input — don't break the session, allow normal flow
    if not isinstance(payload, dict) or payload.get("tool_name") != "Bash":
        return 0
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0
    command = tool_input.get("command")
    if not isinstance(command, str) or not command:
        return 0

    rule = evaluate(command)
    if rule is None:
        return 0  # no match: exit 0 with no output → normal permission flow

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": build_reason(rule),
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
