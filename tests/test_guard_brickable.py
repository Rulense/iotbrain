# Tests for hooks/guard_brickable.py — the PreToolUse safety gate.
#
# The hook is exercised end-to-end: real PreToolUse JSON payloads are fed to
# the script on stdin via subprocess, exactly as Claude Code invokes it
# (https://code.claude.com/docs/en/hooks).
import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / "hooks" / "guard_brickable.py"
HOOKS_JSON = Path(__file__).resolve().parents[1] / "hooks" / "hooks.json"


def run_hook(stdin_text):
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=stdin_text,
        capture_output=True,
        text=True,
        timeout=30,
    )


def bash_payload(command):
    return json.dumps(
        {
            "session_id": "test-session",
            "transcript_path": "/tmp/transcript.jsonl",
            "cwd": "/tmp",
            "permission_mode": "default",
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": command, "description": "test"},
        }
    )


def assert_ask(command):
    proc = run_hook(bash_payload(command))
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    hso = out["hookSpecificOutput"]
    assert hso["hookEventName"] == "PreToolUse"
    assert hso["permissionDecision"] == "ask"
    assert "iotbrain safety gate" in hso["permissionDecisionReason"]
    return hso["permissionDecisionReason"]


def assert_allow(command):
    proc = run_hook(bash_payload(command))
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "", (
        f"expected silent allow for {command!r}, got: {proc.stdout}"
    )


# --- Dangerous commands must escalate to "ask" -------------------------------

DANGEROUS = [
    # raw disk writes
    "sudo dd if=jetson.img of=/dev/mmcblk0 bs=4M status=progress",
    "gunzip -c backup.img.gz | dd if=/dev/stdin of=/dev/mmcblk0 && sync",
    "ssh jetson 'sudo dd if=/tmp/rootfs.img of=/dev/nvme0n1'",
    "cat rootfs.img > /dev/sdb",
    "sudo blkdiscard /dev/nvme0n1",
    "sudo wipefs -a /dev/sdb",
    "sudo shred -n 3 /dev/sda",
    # partitioning / formatting
    "sudo fdisk /dev/mmcblk0",
    "sudo parted /dev/sda mklabel gpt",
    "sudo parted -s /dev/nvme0n1 mkpart primary ext4 0% 100%",
    "sudo sgdisk -Z /dev/nvme0n1",
    "sudo mkfs.ext4 /dev/mmcblk0p1",
    "ssh orin 'sudo mkfs.vfat /dev/sda1'",
    # device flashing
    "sudo ./flash.sh jetson-orin-nano-devkit mmcblk0p1",
    "sudo ./tools/kernel_flash/l4t_initrd_flash.sh --external-device nvme0n1p1 -c flash_l4t_external.xml jetson-orin-nano-devkit nvme0n1p1",
    "sdkmanager --cli flash --target JETSON_ORIN_NANO_TARGETS",
    "esptool.py --port /dev/ttyUSB0 --baud 460800 write_flash 0x0 firmware.bin",
    "esptool.py erase_flash",
    "esptool erase_region 0x10000 0x100000",
    "sudo dfu-util -a 0 -D firmware.dfu",
    "fastboot flash boot boot.img",
    # fuse / bootloader (irreversible)
    "sudo ./odmfuse.sh -i 0x19 -k rsa_priv.pem",
    "sudo nvbootctrl set-active-boot-slot 1",
    "ssh jetson 'sudo nvbootctrl mark-boot-successful'",
    "sudo efibootmgr -o 0001,0000",
    "sudo efibootmgr -b 0003 -B",
    "espefuse.py --port /dev/ttyUSB0 burn_efuse DIS_USB_JTAG 1",
    # boot-critical file edits
    "echo 'APPEND root=/dev/nvme0n1p1' >> /boot/extlinux/extlinux.conf",
    "echo 'UUID=abcd / ext4 defaults 0 1' | sudo tee -a /etc/fstab",
    "sudo sed -i 's/mmcblk0p1/nvme0n1p1/' /boot/extlinux/extlinux.conf",
    "sh -c 'echo dtoverlay=uart0 >> /boot/firmware/config.txt'",
    "ssh pi 'echo console=serial0 | sudo tee /boot/firmware/cmdline.txt'",
]


@pytest.mark.parametrize("command", DANGEROUS)
def test_dangerous_commands_ask(command):
    assert_ask(command)


# --- Safe commands must pass through silently ---------------------------------

SAFE = [
    "ls -la /dev/",
    "lsblk -f",
    "fdisk -l",
    "sudo fdisk -l /dev/mmcblk0",
    "parted -l",
    "sudo parted /dev/sda print",
    "sudo sgdisk -p /dev/nvme0n1",
    "esptool.py chip_id",
    "esptool.py --port /dev/ttyUSB0 read_mac",
    "espefuse.py summary",
    "nvbootctrl dump-slots-info",
    "sudo nvbootctrl get-current-slot",
    "efibootmgr -v",
    "dfu-util --list",
    "dd if=/dev/urandom of=./file.bin bs=1M count=10",
    "dd if=/dev/mmcblk0 of=backup.img bs=4M",
    "grep dd file",
    "cat /etc/fstab",
    "grep -r extlinux.conf docs/",
    "sudo wipefs --no-act /dev/sda",
    "echo hello > /tmp/out.txt",
    "echo test > /dev/null",
]


@pytest.mark.parametrize("command", SAFE)
def test_safe_commands_allow(command):
    assert_allow(command)


# --- Reason content ------------------------------------------------------------


def test_reason_names_category_and_pattern():
    reason = assert_ask("sudo dd if=x.img of=/dev/mmcblk0")
    assert "block device" in reason
    assert "matched:" in reason
    assert "right device?" in reason
    assert "backed up?" in reason
    assert "stable power?" in reason


def test_fuse_reason_says_irreversible():
    reason = assert_ask("sudo ./odmfuse.sh -i 0x19")
    assert "IRREVERSIBLE" in reason


# --- Payload robustness ---------------------------------------------------------


def test_non_bash_tool_allowed():
    payload = json.dumps(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": "/dev/sda",
                "content": "dd of=/dev/mmcblk0",
            },
        }
    )
    proc = run_hook(payload)
    assert proc.returncode == 0
    assert proc.stdout.strip() == ""


def test_missing_command_allowed():
    payload = json.dumps({"tool_name": "Bash", "tool_input": {}})
    proc = run_hook(payload)
    assert proc.returncode == 0
    assert proc.stdout.strip() == ""


def test_malformed_json_does_not_crash():
    proc = run_hook("this is not json{{{")
    assert proc.returncode == 0
    assert proc.stdout.strip() == ""


def test_empty_stdin_does_not_crash():
    proc = run_hook("")
    assert proc.returncode == 0
    assert proc.stdout.strip() == ""


def test_ask_output_is_valid_hook_json():
    proc = run_hook(bash_payload("sudo blkdiscard /dev/nvme0n1"))
    out = json.loads(proc.stdout)
    assert set(out.keys()) == {"hookSpecificOutput"}
    assert set(out["hookSpecificOutput"].keys()) == {
        "hookEventName",
        "permissionDecision",
        "permissionDecisionReason",
    }


# --- Plugin wiring ----------------------------------------------------------------


def test_hooks_json_registers_the_gate():
    config = json.loads(HOOKS_JSON.read_text())
    pre = config["hooks"]["PreToolUse"]
    bash_entries = [entry for entry in pre if entry.get("matcher") == "Bash"]
    assert bash_entries, "hooks.json must register a PreToolUse matcher for Bash"
    commands = [
        hook["command"]
        for entry in bash_entries
        for hook in entry["hooks"]
        if hook.get("type") == "command"
    ]
    assert any(
        "${CLAUDE_PLUGIN_ROOT}" in cmd and "guard_brickable.py" in cmd
        for cmd in commands
    )
