# tests/test_scrub.py
import importlib.util
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRUB_PATH = REPO_ROOT / "skills" / "brain-distill" / "scripts" / "scrub.py"

_spec = importlib.util.spec_from_file_location("scrub", SCRUB_PATH)
scrub_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(scrub_mod)
scrub = scrub_mod.scrub


# --- Redaction: each category -------------------------------------------------

def test_ipv4_redacted():
    out, report = scrub("device reachable at 10.42.7.19 over eth0")
    assert "10.42.7.19" not in out
    assert "<ip>" in out
    assert any(line.startswith("[ipv4]") for line in report)


def test_ipv6_redacted():
    out, report = scrub("bound to 2001:db8:85a3::8a2e:370:7334 and fe80::1")
    assert "2001:db8:85a3::8a2e:370:7334" not in out
    assert "fe80::1" not in out
    assert out.count("<ipv6>") == 2
    assert sum(line.startswith("[ipv6]") for line in report) == 2


def test_internal_hostname_local_redacted():
    out, report = scrub("ssh into jetson-orin.local before flashing")
    assert "jetson-orin.local" not in out
    assert "<internal-host>" in out
    assert any(line.startswith("[internal-hostname]") for line in report)


def test_internal_hostname_all_suffixes_redacted():
    text = "hosts: build01.corp gw.internal nas.lan wiki.intranet"
    out, report = scrub(text)
    for host in ("build01.corp", "gw.internal", "nas.lan", "wiki.intranet"):
        assert host not in out
    assert out.count("<internal-host>") == 4


def test_aws_key_redacted():
    out, report = scrub("export AWS_ACCESS_KEY_ID value AKIAIOSFODNN7EXAMPLE here")
    assert "AKIAIOSFODNN7EXAMPLE" not in out
    assert "<aws-access-key>" in out
    assert any(line.startswith("[aws-access-key]") for line in report)


def test_github_tokens_redacted():
    text = ("ghp_abcdefghijklmnopqrstuvwxyz012345 and "
            "gho_ABCDEFGHIJKLMNOPQRSTUVWXYZ098765 and "
            "github_pat_11ABCDEFG0123456789_abcdefghijklmnop")
    out, report = scrub(text)
    assert "ghp_" not in out and "gho_" not in out and "github_pat_" not in out
    assert out.count("<github-token>") == 3


def test_bearer_token_redacted():
    out, report = scrub('curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.payload.sig"')
    assert "eyJhbGciOiJIUzI1NiJ9" not in out
    assert "Bearer <token>" in out
    assert any(line.startswith("[bearer-token]") for line in report)


def test_private_key_block_redacted():
    text = ("before\n-----BEGIN RSA PRIVATE KEY-----\n"
            "MIIEpAIBAAKCAQEA7bq0\nmore+key/material==\n"
            "-----END RSA PRIVATE KEY-----\nafter\n")
    out, report = scrub(text)
    assert "MIIEpAIBAAKCAQEA7bq0" not in out
    assert "BEGIN RSA PRIVATE KEY" not in out
    assert "<private-key>" in out
    assert out.startswith("before\n") and out.endswith("\nafter\n")


def test_credential_assignments_redacted():
    out, report = scrub("password=hunter2 API_TOKEN=abc123 client_secret='sh h'")
    assert "hunter2" not in out and "abc123" not in out and "sh h" not in out
    assert "password=<redacted>" in out
    assert "API_TOKEN=<redacted>" in out
    assert "client_secret=<redacted>" in out


def test_email_redacted():
    out, report = scrub("reported by jane.doe@example.com on the forum")
    assert "jane.doe@example.com" not in out
    assert "<email>" in out
    assert any(line.startswith("[email]") for line in report)


def test_home_paths_redacted():
    out, report = scrub("cloned to /Users/jdoe/proj and /home/jdoe/proj")
    assert "/Users/jdoe" not in out and "/home/jdoe" not in out
    assert out == "cloned to <home>/proj and <home>/proj"


# --- Allowlists: each preserved -------------------------------------------------

def test_allowlisted_platform_ips_preserved():
    text = "USB: 192.168.55.1, loopback 127.0.0.1, bind 0.0.0.0, DNS 8.8.8.8"
    out, report = scrub(text)
    assert out == text
    assert report == []


def test_rfc5737_doc_ranges_preserved():
    text = "examples: 192.0.2.7, 198.51.100.20, 203.0.113.9"
    out, report = scrub(text)
    assert out == text
    assert report == []


def test_public_domains_preserved():
    text = "see forums.developer.nvidia.com and docs.espressif.com"
    out, report = scrub(text)
    assert out == text
    assert report == []


def test_allowlisted_emails_preserved():
    text = "Co-authored-by: bot <12345+bot@users.noreply.github.com> noreply@github.com"
    out, report = scrub(text)
    assert out == text
    assert report == []


# --- Pass-through + combined ----------------------------------------------------

def test_clean_entry_passes_through_byte_identical():
    text = (
        "---\n"
        'title: PyTorch 2.5 wheel works on JetPack 6.1\n'
        "type: config\n"
        "company: nvidia\n"
        'platform_versions: ["JetPack 6.1", "L4T 36.x"]\n'
        "devices: [orin-nano]\n"
        'sources: ["https://forums.developer.nvidia.com/t/12345"]\n'
        "---\n"
        "## Context\n"
        "Flash over USB device mode (192.168.55.1), then install into\n"
        "<project-dir>. ESP-IDF 5.3 comparison at docs.espressif.com.\n"
        "## Verify\n"
        "python3 -c 'import torch' exits 0.\n"
    )
    out, report = scrub(text)
    assert out == text
    assert report == []


def test_multi_secret_line_handles_all():
    text = ("password=hunter2 via Bearer abcdef1234567890 from "
            "admin@example.com at 10.0.0.7 on build01.corp "
            "key AKIAIOSFODNN7EXAMPLE in /home/jdoe/secrets")
    out, report = scrub(text)
    assert "hunter2" not in out
    assert "abcdef1234567890" not in out
    assert "admin@example.com" not in out
    assert "10.0.0.7" not in out
    assert "build01.corp" not in out
    assert "AKIAIOSFODNN7EXAMPLE" not in out
    assert "/home/jdoe" not in out
    categories = {line.split("]")[0] + "]" for line in report}
    assert categories == {"[credential-assignment]", "[bearer-token]", "[email]",
                          "[ipv4]", "[internal-hostname]", "[aws-access-key]",
                          "[home-path]"}


def test_scrubbed_output_is_idempotent():
    text = "password=hunter2 at 10.0.0.7 Bearer abcdef1234567890"
    once, report1 = scrub(text)
    twice, report2 = scrub(once)
    assert twice == once
    assert report2 == []


# --- CLI behavior ------------------------------------------------------------------

def test_cli_stdin_stdout_stderr():
    proc = subprocess.run(
        [sys.executable, str(SCRUB_PATH)],
        input="host jetson.local at 10.9.8.7\n",
        capture_output=True, text=True,
    )
    assert proc.returncode == 0
    assert proc.stdout == "host <internal-host> at <ip>\n"
    assert "[internal-hostname] jetson.local" in proc.stderr
    assert "[ipv4] 10.9.8.7" in proc.stderr


def test_cli_file_argument(tmp_path):
    draft = tmp_path / "draft.md"
    draft.write_text("email me at jane@example.com\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(SCRUB_PATH), str(draft)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0
    assert proc.stdout == "email me at <email>\n"
    assert "[email] jane@example.com" in proc.stderr
