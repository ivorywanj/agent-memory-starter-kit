#!/usr/bin/env python3
"""Scan AI memory files for secrets, hidden characters, and prompt injection."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


DEFAULT_PATHS = [
    "AGENTS.md",
    "ONBOARDING.md",
    "README.md",
    "agent",
    "domains",
    "memory",
    "tasks",
    "toolbox",
]

TEXT_SUFFIXES = {".md", ".txt", ".json", ".yml", ".yaml", ".toml", ".csv"}
EXCLUDED_PARTS = {
    ".git",
    ".serena",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
}
EXCLUDED_RELATIVE_PREFIXES = (
    "memory/history/runtime",
    "memory/dreams/runtime",
    "memory/promotions/runtime",
    "memory/sessions",
    "memory/agentmemory-cache",
    "memory/runtime",
)

HIDDEN_CHARS = {
    "\u200b": "ZERO WIDTH SPACE",
    "\u200c": "ZERO WIDTH NON-JOINER",
    "\u200d": "ZERO WIDTH JOINER",
    "\ufeff": "BOM",
    "\u202a": "LEFT-TO-RIGHT EMBEDDING",
    "\u202b": "RIGHT-TO-LEFT EMBEDDING",
    "\u202c": "POP DIRECTIONAL FORMATTING",
    "\u202d": "LEFT-TO-RIGHT OVERRIDE",
    "\u202e": "RIGHT-TO-LEFT OVERRIDE",
    "\u2066": "LEFT-TO-RIGHT ISOLATE",
    "\u2067": "RIGHT-TO-LEFT ISOLATE",
    "\u2068": "FIRST STRONG ISOLATE",
    "\u2069": "POP DIRECTIONAL ISOLATE",
}


@dataclass
class Finding:
    severity: str
    kind: str
    path: str
    line: int
    detail: str
    snippet: str


PATTERNS: list[tuple[str, str, re.Pattern[str]]] = [
    ("block", "openai_api_key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("block", "anthropic_api_key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b")),
    ("block", "github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")),
    ("block", "slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    (
        "block",
        "database_url",
        re.compile(r"\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://[^\s`\"<>]+", re.I),
    ),
    (
        "block",
        "webhook_url",
        re.compile(r"https://[^\s`\"<>]*(?:hooks\.slack\.com|open\.feishu\.cn|discord(?:app)?\.com/api/webhooks)[^\s`\"<>]+", re.I),
    ),
    ("block", "private_key", re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")),
    (
        "block",
        "secret_assignment",
        re.compile(r"\b(?:api[_-]?key|token|secret|password)\b\s*[:=]\s*[\"'][^\"']{12,}[\"']", re.I),
    ),
    (
        "block",
        "prompt_injection",
        re.compile(r"\b(?:ignore|disregard|override)\b.{0,50}\b(?:previous|prior|system|developer)\b.{0,50}\b(?:instruction|instructions|message|prompt)\b", re.I),
    ),
    (
        "block",
        "prompt_injection",
        re.compile(r"\b(?:reveal|print|dump)\b.{0,40}\b(?:system prompt|developer message|secrets?)\b", re.I),
    ),
    ("block", "prompt_injection", re.compile(r"忽略.{0,30}(之前|以上|所有).{0,30}指令")),
    ("block", "prompt_injection", re.compile(r"泄露.{0,30}(系统提示|密钥|secrets?)", re.I)),
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def normalize_rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def is_excluded(path: Path, root: Path) -> bool:
    rel = normalize_rel(path, root)
    if any(part in EXCLUDED_PARTS for part in path.parts):
        return True
    return any(rel == prefix or rel.startswith(prefix + "/") for prefix in EXCLUDED_RELATIVE_PREFIXES)


def iter_files(paths: list[str], root: Path) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        path = (root / raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
        if not path.exists():
            continue
        if path.is_file():
            if path.suffix in TEXT_SUFFIXES and not is_excluded(path, root):
                files.append(path)
            continue
        for item in path.rglob("*"):
            if item.is_file() and item.suffix in TEXT_SUFFIXES and not is_excluded(item, root):
                files.append(item)
    return sorted(set(files))


def redact(value: str) -> str:
    value = value.strip()
    if "PRIVATE KEY" in value:
        return "<redacted private key marker>"
    if len(value) <= 12:
        return "<redacted>"
    return f"{value[:4]}...{value[-4:]}"


def is_negated_safety_line(line: str, start: int) -> bool:
    prefix = line[:start].lower()
    return any(marker in prefix for marker in ("never ", "do not ", "don't ", "must not ", "cannot ", "不要", "不能", "禁止"))


def scan_file(path: Path, root: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        findings.append(Finding("warn", "read_error", normalize_rel(path, root), 0, str(exc), ""))
        return findings

    rel = normalize_rel(path, root)
    for line_no, line in enumerate(lines, 1):
        for char, name in HIDDEN_CHARS.items():
            if char in line:
                findings.append(Finding("block", "hidden_unicode", rel, line_no, name, "<hidden character redacted>"))
        for severity, kind, pattern in PATTERNS:
            for match in pattern.finditer(line):
                if kind == "prompt_injection" and is_negated_safety_line(line, match.start()):
                    continue
                findings.append(Finding(severity, kind, rel, line_no, kind, redact(match.group(0))))
    return findings


def scan(paths: list[str], root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in iter_files(paths, root):
        findings.extend(scan_file(path, root))
    return findings


def print_text(findings: list[Finding]) -> None:
    if not findings:
        print("memory_guard: pass")
        return
    print(f"memory_guard: {len(findings)} finding(s)")
    for finding in findings:
        location = f"{finding.path}:{finding.line}" if finding.line else finding.path
        print(f"- [{finding.severity}] {finding.kind} {location} {finding.snippet}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan memory runtime files for unsafe content.")
    parser.add_argument("paths", nargs="*", help="Optional paths to scan. Defaults to runtime docs.")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    root = repo_root()
    paths = args.paths or DEFAULT_PATHS
    findings = scan(paths, root)

    if args.format == "json":
        print(json.dumps([asdict(item) for item in findings], ensure_ascii=False, indent=2))
    else:
        print_text(findings)

    return 1 if any(item.severity == "block" for item in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
