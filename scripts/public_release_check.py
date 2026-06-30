#!/usr/bin/env python3
"""Public package release checks."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".md", ".py", ".json", ".txt", ".yml", ".yaml"}
PRIVATE_MARKERS = ("Wan" + "jia", "万" + "家", "Journey" + "Gen", "/Users/" + "wanj", "cowork " + "playground")
SECRET_PATTERNS = (
    ("api_key", re.compile("s" + "k-[A-Za-z0-9_-]{20,}")),
    ("database_url", re.compile("postgres" + r"(?:ql)?://", re.I)),
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("webhook_url", re.compile("https://" + r"[^\s]*(?:webhook|hooks)[^\s]*", re.I)),
)
SECRET_PATTERN_EXEMPT_FILES = {"scripts/memory_guard.py", "scripts/public_release_check.py"}
REQUIRED_FILES = (
    ".github/workflows/ci.yml",
    "README.md",
    "LICENSE",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "scripts/memory",
    "scripts/memory_runtime.py",
    "scripts/memory_guard.py",
    "scripts/public_release_check.py",
    "tests/test_public_package.py",
    "templates/public/answers.example.json",
)


def iter_text_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if ".git" in path.parts or not path.is_file() or path.suffix not in TEXT_SUFFIXES:
            continue
        files.append(path)
    return files


def main() -> int:
    findings: list[str] = []
    for rel in REQUIRED_FILES:
        if not (ROOT / rel).exists():
            findings.append(f"missing required file: {rel}")
    for path in iter_text_files():
        rel = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8", errors="replace")
        for marker in PRIVATE_MARKERS:
            if marker in text:
                findings.append(f"{rel}: private marker")
        if str(rel) in SECRET_PATTERN_EXEMPT_FILES:
            continue
        for name, pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(f"{rel}: {name}")
    if findings:
        print("public_release_check: fail")
        print("\n".join(findings))
        return 1
    print("public_release_check: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
