#!/usr/bin/env python3
"""Mechanical scrub pass for brain-distill draft entries.

Reads a draft entry from stdin (or a file argument), writes the scrubbed
draft to stdout, and writes a redaction report to stderr — one line per
redaction: `[category] <what was replaced>`. Clean input passes through
byte-identical.

This is a floor, not a replacement for the manual scrub pass in
brain-distill Step 2.

Usage:
  python3 scrub.py < draft.md > scrubbed.md
  python3 scrub.py draft.md > scrubbed.md

Stdlib only.
"""
from __future__ import annotations

import re
import sys

# --- Allowlists ---------------------------------------------------------------
# Documented platform constants that MUST survive scrubbing: the Jetson USB
# device-mode address, loopback/wildcard, the classic public DNS example, and
# the RFC 5737 documentation ranges (safe by definition in docs/examples).
ALLOWED_IPS = {"192.168.55.1", "127.0.0.1", "0.0.0.0", "8.8.8.8"}
ALLOWED_IP_PREFIXES = ("192.0.2.", "198.51.100.", "203.0.113.")

# Emails that are public-by-design and safe to keep.
ALLOWED_EMAIL_SUFFIXES = ("@users.noreply.github.com",)
ALLOWED_EMAIL_PREFIXES = ("noreply@",)

# Internal-only hostname suffixes. Public domains are kept.
INTERNAL_TLDS = ("local", "corp", "internal", "lan", "intranet")

REPORT_SNIPPET_LEN = 60

# --- Patterns -------------------------------------------------------------------
PRIVATE_KEY_RE = re.compile(
    r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?-----END [A-Z0-9 ]*PRIVATE KEY-----",
    re.DOTALL,
)
# key=value assignments for credential-ish keys (incl. prefixed: API_TOKEN,
# client_secret, DB_PASSWORD). The key is kept; the value is redacted.
ASSIGNMENT_RE = re.compile(
    r"\b([\w-]*(?:password|passwd|token|secret))(\s*=\s*)"
    r"(?!<redacted>)(\"[^\"\n]+\"|'[^'\n]+'|[^\s\"']+)",
    re.IGNORECASE,
)
AWS_KEY_RE = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
GH_TOKEN_RE = re.compile(r"\b(?:ghp|gho)_[A-Za-z0-9]{16,}\b|\bgithub_pat_[A-Za-z0-9_]{16,}\b")
BEARER_RE = re.compile(r"\bBearer\s+(?!<token>)[A-Za-z0-9._~+/=-]{8,}")
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
HOME_PATH_RE = re.compile(r"(?:/Users|/home)/[A-Za-z0-9._-]+")
HOSTNAME_RE = re.compile(
    r"\b[A-Za-z0-9][\w-]*(?:\.[\w-]+)*\.(?:%s)\b(?!\.\w)" % "|".join(INTERNAL_TLDS)
)
IPV4_RE = re.compile(
    r"\b(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\b"
)
IPV6_RE = re.compile(
    r"(?<![\w:.])"
    r"(?:(?:[0-9A-Fa-f]{1,4}:){7}[0-9A-Fa-f]{1,4}"      # full form
    r"|(?:[0-9A-Fa-f]{1,4}:)+:(?:[0-9A-Fa-f]{1,4}:?)*[0-9A-Fa-f]{0,4}"  # a::b
    r"|::(?:[0-9A-Fa-f]{1,4}(?::[0-9A-Fa-f]{1,4})*))"   # ::1
    r"(?![\w:])"
)


def _snippet(text: str) -> str:
    text = " ".join(text.split())
    if len(text) > REPORT_SNIPPET_LEN:
        text = text[:REPORT_SNIPPET_LEN] + "…"
    return text


def scrub(text: str) -> "tuple[str, list[str]]":
    """Return (scrubbed_text, report_lines)."""
    report: "list[str]" = []

    def redact(category: str, replaced: str) -> None:
        report.append("[%s] %s" % (category, _snippet(replaced)))

    def sub(pattern: "re.Pattern[str]", category: str, replacement, keep=None):
        nonlocal text

        def _repl(m: "re.Match[str]") -> str:
            if keep is not None and keep(m):
                return m.group(0)
            new = replacement(m) if callable(replacement) else replacement
            redact(category, m.group(0))
            return new

        text = pattern.sub(_repl, text)

    # Order matters: secrets before generic patterns so a token inside an
    # assignment is reported once, emails before hostnames, home paths intact.
    sub(PRIVATE_KEY_RE, "private-key", "<private-key>")
    sub(ASSIGNMENT_RE, "credential-assignment",
        lambda m: "%s%s<redacted>" % (m.group(1), m.group(2)))
    sub(AWS_KEY_RE, "aws-access-key", "<aws-access-key>")
    sub(GH_TOKEN_RE, "github-token", "<github-token>")
    sub(BEARER_RE, "bearer-token", "Bearer <token>")
    sub(EMAIL_RE, "email", "<email>",
        keep=lambda m: m.group(0).lower().endswith(ALLOWED_EMAIL_SUFFIXES)
        or m.group(0).lower().startswith(ALLOWED_EMAIL_PREFIXES))
    sub(HOME_PATH_RE, "home-path", "<home>")
    sub(HOSTNAME_RE, "internal-hostname", "<internal-host>")
    sub(IPV4_RE, "ipv4", "<ip>",
        keep=lambda m: m.group(0) in ALLOWED_IPS
        or m.group(0).startswith(ALLOWED_IP_PREFIXES))
    sub(IPV6_RE, "ipv6", "<ipv6>")
    return text, report


def main(argv: "list[str]") -> int:
    if len(argv) > 1:
        print("usage: scrub.py [draft-file]  (default: stdin)", file=sys.stderr)
        return 2
    if argv:
        with open(argv[0], encoding="utf-8") as fh:
            raw = fh.read()
    else:
        raw = sys.stdin.read()
    scrubbed, report = scrub(raw)
    sys.stdout.write(scrubbed)
    for line in report:
        print(line, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
