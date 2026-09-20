#!/usr/bin/env python3
"""Detect likely secrets in the staged public release without printing values."""

from __future__ import annotations

import argparse
import math
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

SKIP_DIRS = {".git", ".venv", "__pycache__", ".mypy_cache", ".pytest_cache", "node_modules"}
TEXT_SUFFIXES = {".cfg", ".env", ".ini", ".json", ".md", ".py", ".sh", ".template", ".toml", ".txt", ".yaml", ".yml"}
SPECIAL_TEXT_NAMES = {".env.example"}
BLOCKED_NAMES = {".env", "credentials.json", "id_rsa", "id_ed25519"}

PRIVATE_KEY = re.compile(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----")
GITHUB_TOKEN = re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b")
OPENAI_TOKEN = re.compile(r"\bsk[-_](?:proj[-_])?[A-Za-z0-9_-]{16,}\b")
AWS_KEY = re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")
SLACK_WEBHOOK = re.compile(r"https?://hooks[.]slack[.]com/services/", re.IGNORECASE)
DISCORD_WEBHOOK = re.compile(r"https?://(?:canary[.])?discord(?:app)?[.]com/api/webhooks/", re.IGNORECASE)
TELEGRAM_TOKEN = re.compile(r"\b\d{8,12}:[A-Za-z0-9_-]{25,}\b")
CREDENTIAL_ASSIGNMENT = re.compile(
    r"(?i)\b(?:api[_-]?key|secret|token|password|passwd|webhook)\b\s*[:=]\s*['\"][^'\"\s]{8,}"
)
QUOTED_LITERAL = re.compile(r"(['\"])(?P<value>(?:\\.|(?!\1).)*)\1")
PATTERNS = {
    "private_key_material": PRIVATE_KEY,
    "github_token": GITHUB_TOKEN,
    "openai_token": OPENAI_TOKEN,
    "aws_access_key": AWS_KEY,
    "slack_webhook": SLACK_WEBHOOK,
    "discord_webhook": DISCORD_WEBHOOK,
    "telegram_token": TELEGRAM_TOKEN,
    "literal_credential_assignment": CREDENTIAL_ASSIGNMENT,
}


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    kind: str


def shannon_entropy(value: str) -> float:
    if not value:
        return 0.0
    return -sum((value.count(char) / len(value)) * math.log2(value.count(char) / len(value)) for char in set(value))


def is_probable_secret_literal(value: str) -> bool:
    if value.startswith(("http://", "https://")):
        return False
    if len(value) < 32 or not re.fullmatch(r"[A-Za-z0-9_-]+", value):
        return False
    return shannon_entropy(value) >= 4.0


def line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def is_candidate(relative: Path) -> bool:
    return relative.name in SPECIAL_TEXT_NAMES or relative.name in BLOCKED_NAMES or relative.suffix in TEXT_SUFFIXES


def is_skipped(relative: Path) -> bool:
    return any(part in SKIP_DIRS for part in relative.parts)


def scan_text(relative: Path, text: str) -> list[Finding]:
    findings: list[Finding] = []
    if relative.name in BLOCKED_NAMES:
        findings.append(Finding(relative, 1, "blocked_filename"))
    for kind, pattern in PATTERNS.items():
        for match in pattern.finditer(text):
            findings.append(Finding(relative, line_number(text, match.start()), kind))
    for match in QUOTED_LITERAL.finditer(text):
        if is_probable_secret_literal(match.group("value")):
            findings.append(Finding(relative, line_number(text, match.start()), "high_entropy_literal"))
    return findings


def _git_output(root: Path, arguments: list[str]) -> bytes | None:
    result = subprocess.run(
        ["git", "-C", str(root), *arguments],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.stdout if result.returncode == 0 else None


def _git_paths(root: Path, arguments: list[str]) -> list[Path] | None:
    raw = _git_output(root, arguments)
    if raw is None:
        return None
    paths: list[Path] = []
    for entry in raw.split(b"\0"):
        if not entry:
            continue
        try:
            relative = Path(entry.decode("utf-8"))
        except UnicodeDecodeError:
            continue
        if not relative.is_absolute() and is_candidate(relative) and not is_skipped(relative):
            paths.append(relative)
    return paths


def _index_text(root: Path, relative: Path) -> str | None:
    raw = _git_output(root, ["show", f":{relative.as_posix()}"])
    if raw is None:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _disk_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _worktree_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if path.is_file() and is_candidate(relative) and not is_skipped(relative):
            yield relative


def scan(root: Path) -> list[Finding]:
    """Scan staged Git blobs plus nonignored new files, never ignored local config."""

    findings: list[Finding] = []
    indexed = _git_paths(root, ["ls-files", "-z"])
    untracked = _git_paths(root, ["ls-files", "--others", "--exclude-standard", "-z"])
    if indexed is None or untracked is None:
        for relative in _worktree_files(root):
            text = _disk_text(root / relative)
            if text is not None:
                findings.extend(scan_text(relative, text))
    else:
        for relative in indexed:
            text = _index_text(root, relative)
            if text is not None:
                findings.extend(scan_text(relative, text))
        for relative in untracked:
            text = _disk_text(root / relative)
            if text is not None:
                findings.extend(scan_text(relative, text))
    return sorted(set(findings), key=lambda finding: (str(finding.path), finding.line, finding.kind))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan the staged public release without printing suspected secret values.")
    parser.add_argument("root", nargs="?", type=Path, default=Path.cwd())
    parser.add_argument("--strict", action="store_true", help="Fail on all findings. This is the default behavior.")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if not root.is_dir():
        print("Scan root is not a directory", file=sys.stderr)
        return 2
    findings = scan(root)
    if not findings:
        print("Secret scan passed: staged files and nonignored new files contain no likely credentials, webhooks, or blocked files.")
        return 0
    print(f"Secret scan failed: {len(findings)} finding(s). Values are intentionally redacted.")
    for finding in findings:
        print(f"{finding.path}:{finding.line}: {finding.kind}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
