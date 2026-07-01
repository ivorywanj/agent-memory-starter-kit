#!/usr/bin/env python3
"""Public package release checks."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".md", ".mdc", ".py", ".json", ".txt", ".yml", ".yaml"}
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
    "AGENTS.md",
    "CLAUDE.md",
    ".cursorrules",
    ".cursor/rules/journeymem-first-run.mdc",
    ".trae/rules/journeymem-first-run.md",
    "JOURNEYMEM.md",
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
    "docs/releases/v0.1.4.md",
    "docs/releases/v0.1.1.md",
    "docs/releases/v0.1.2.md",
    "docs/releases/v0.1.3.md",
    "docs/first-run-wizard.md",
    "docs/agent-sharing.md",
    "docs/productized-user-flow.md",
    "docs/workflows/memory-new.md",
    "docs/workflows/memory-install.md",
    "docs/workflows/memory-connect.md",
    "docs/workflows/memory-backup.md",
    "docs/workflows/memory-share.md",
)
README_REQUIRED_SNIPPETS = (
    "A local memory library for AI agents.",
    "## Quickstart",
    "copy this whole prompt",
    "Please set up JourneyMem from this GitHub repo:",
    "Do not paste only `git clone` and `cd agent-memory-starter-kit` into an Agent.",
    "Do not add setup analysis, repository summary, or mode/tooling notes.",
    "scripts/memory install --agent all --workspace ./your-project",
    "Type:",
    "memory",
    "memory new",
    "memory connect",
    "memory backup",
    "A fresh clone does not mean the user chose new setup",
    "before running `memory new` or `memory connect`",
    "real `memory` shell command",
    "[$journeymem](<generated-local-skill-path>/SKILL.md)",
    "Manual terminal fallback only:",
    "./scripts/memory new",
    "For first-time setup, the Agent should not explain setup internals or ask where to store the files.",
    "only show the next useful question",
    "Do not show the full questionnaire upfront",
    "Do not ask where to store the memory library during `memory new`; use the default location.",
    "Do you want to create a new memory library, or connect this Agent to an existing memory library?",
    "Fresh clone rule: after `git clone` and `cd agent-memory-starter-kit`, the Agent must ask this two-choice question.",
    "no import is needed",
    "Do you already have a memory library on this computer?",
    "AGENTS.md`, `ONBOARDING.md`, `memory/hot/USER.md`, and `memory/hot/MEMORY.md",
    "use the default backup folder",
    "Backup does not connect, import, restore, switch, or initialize",
    "## Sharing Across Agents",
    "## First-Run Wizard",
    "## Productized Flow Metrics",
    "docs/productized-user-flow.md",
    "folder pointer",
    "## Developer Commands",
    "init -> remember -> recall -> improve -> forget",
    "## Safety",
    "## Validation",
    "## Benchmark Evidence",
    "## V1 Limits",
)
AGENTS_REQUIRED_SNIPPETS = (
    "# JourneyMem Agent Instructions",
    "do not summarize the repository structure",
    "I can help you use JourneyMem.",
    "`memory new` - Create a new memory library",
    "`memory connect` - Connect this Agent to an existing memory library",
    "Do not start `memory new` until the user chooses create/new.",
    "Do not ask \"What should Agents call you?\" before that choice.",
    "Do not add tool mode limitations, execution caveats, or other extra notes to the first response.",
)
AGENT_INSTRUCTION_FILES = (
    "AGENTS.md",
    "CLAUDE.md",
    ".cursorrules",
    ".cursor/rules/journeymem-first-run.mdc",
    ".trae/rules/journeymem-first-run.md",
    "JOURNEYMEM.md",
)
README_FIRST_SCREEN_BLOCKED_TERMS = (
    "runtime",
    "root",
    "bridge",
    "source-of-truth",
    "session cache",
    "deprecated",
    "cli",
    "markdown",
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
    readme = ROOT / "README.md"
    if readme.exists():
        readme_text = readme.read_text(encoding="utf-8", errors="replace")
        for snippet in README_REQUIRED_SNIPPETS:
            if snippet not in readme_text:
                findings.append(f"README.md missing snippet: {snippet}")
        first_screen = readme_text.split("## Developer Commands", 1)[0].lower()
        for term in README_FIRST_SCREEN_BLOCKED_TERMS:
            if term in first_screen:
                findings.append(f"README.md first screen uses internal term: {term}")
        before_fallback = readme_text.split("Manual terminal fallback only:", 1)[0]
        if "./scripts/memory new" in before_fallback:
            findings.append("README.md promotes ./scripts/memory new before fallback")
        before_manual_fallback = readme_text.split("Manual terminal fallback only:", 1)[0]
        if "git clone " in before_manual_fallback:
            findings.append("README.md promotes bare git clone before Agent prompt")
    for rel in AGENT_INSTRUCTION_FILES:
        agents_file = ROOT / rel
        if not agents_file.exists():
            continue
        agents_text = agents_file.read_text(encoding="utf-8", errors="replace")
        for snippet in AGENTS_REQUIRED_SNIPPETS:
            if snippet not in agents_text:
                findings.append(f"{rel} missing snippet: {snippet}")
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
