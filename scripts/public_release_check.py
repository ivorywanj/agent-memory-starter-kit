#!/usr/bin/env python3
"""Public package release checks."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".html", ".md", ".mdc", ".py", ".json", ".txt", ".yml", ".yaml"}
PRIVATE_MARKERS = ("Wan" + "jia", "万" + "家", "Journey" + "Gen", "/Users/" + "wanj", "cowork " + "playground")
SECRET_PATTERNS = (
    ("api_key", re.compile("s" + "k-[A-Za-z0-9_-]{20,}")),
    ("database_url", re.compile("postgres" + r"(?:ql)?://", re.I)),
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("webhook_url", re.compile("https://" + r"[^\s]*(?:webhook|hooks)[^\s]*", re.I)),
)
SECRET_PATTERN_EXEMPT_FILES = {
    "scripts/memory_guard.py",
    "scripts/public_release_check.py",
    "scripts/save_agent_entry_transcript.py",
}
REQUIRED_FILES = (
    ".github/workflows/ci.yml",
    "AGENTS.md",
    "CLAUDE.md",
    ".cursorrules",
    ".cursor/rules/journeymem-first-run.mdc",
    ".trae/rules/journeymem-first-run.md",
    "JOURNEYMEM.md",
    "index.html",
    "README.md",
    "PRD.md",
    "LICENSE",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "install.sh",
    "docs/install.sh",
    "scripts/memory",
    "scripts/memory_runtime.py",
    "scripts/memory_guard.py",
    "scripts/memory_status.py",
    "scripts/score_agent_entry_transcripts.py",
    "scripts/prd_acceptance_check.py",
    "scripts/prepare_agent_entry_trials.py",
    "scripts/collect_codex_entry_transcript.py",
    "scripts/collect_cursor_entry_transcript.py",
    "scripts/agent_entry_readiness.py",
    "scripts/save_agent_entry_transcript.py",
    "scripts/public_release_check.py",
    "tests/test_public_package.py",
    "templates/public/answers.example.json",
    "templates/public/agent-entry-transcripts.example.jsonl",
    "docs/releases/v0.1.4.md",
    "docs/releases/v0.1.1.md",
    "docs/releases/v0.1.2.md",
    "docs/releases/v0.1.3.md",
    "docs/first-run-wizard.md",
    "docs/index.html",
    "docs/agent-sharing.md",
    "docs/productized-user-flow.md",
    "docs/workflows/memory-new.md",
    "docs/workflows/memory-install.md",
    "docs/workflows/memory-connect.md",
    "docs/workflows/memory-backup.md",
    "docs/workflows/agent-entry-transcripts.md",
    "docs/workflows/memory-share.md",
)
README_REQUIRED_SNIPPETS = (
    "A local memory library for AI agents.",
    "## Quickstart",
    "Start with the JourneyMem menu:",
    "https://ivorywanj.github.io/agent-memory-starter-kit/",
    "The Start Page has copy buttons for Agent-specific prompts.",
    "Users do not write prompts by hand.",
    "curl -fsSL https://ivorywanj.github.io/agent-memory-starter-kit/install.sh | bash",
    "~/.local/bin/memory",
    "~/.local/bin/memory connect",
    "If an Agent is reading this README because you pasted the GitHub link",
    "run the hosted installer above instead of summarizing or cloning the repository",
    "installed local skill",
    "GitHub URL is an install source fallback",
    "detects the current Agent when possible",
    "when it cannot detect one, it installs helpers for all supported Agents",
    "It does not create a personal memory library until the user chooses `memory new`",
    "memory",
    "1. memory new - Create a memory library",
    "2. memory connect - Connect this Agent to an existing memory library",
    "memory new",
    "memory connect",
    "memory backup",
    "JourneyMem's GitHub URL is an install source fallback, not the primary Agent entry.",
    "If `memory` is not found in the current shell, run `~/.local/bin/memory`",
    "real `memory` shell command",
    "[$journeymem](<generated-local-skill-path>/SKILL.md)",
    "./scripts/memory new",
    "For first-time setup, the Agent should not explain setup internals or ask where to store the files.",
    "only show the next useful question",
    "Do not show the full questionnaire upfront",
    "Do not ask where to store the memory library during `memory new`; use the default location.",
    "Do you want to create a new memory library, or connect this Agent to an existing memory library?",
    "Install-source fallback rule: if the JourneyMem GitHub URL appears first",
    "no import is needed",
    "checks `~/.journeymem/registry.json` and the default JourneyMem library path before asking for any folder path",
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
START_PAGE_REQUIRED_SNIPPETS = (
    "JourneyMem Start",
    "Start JourneyMem without making your Agent inspect a repo.",
    "Start with the JourneyMem menu.",
    "1. memory new - Create a memory library",
    "2. memory connect - Connect this Agent to an existing memory library",
    "Other command:",
    "Click a copy button when you need to start from an Agent message.",
    "Copy Codex prompt",
    "Copy TRAE Work prompt",
    "Copy Claude Code prompt",
    "Copy Cursor prompt",
    "data-target=\"codex-prompt\"",
    "navigator.clipboard.writeText",
    "Codex",
    "TRAE Work",
    "Claude Code",
    "Cursor",
    "Other Agent",
    "If the memory command is unavailable, run this installer first:",
    "curl -fsSL https://ivorywanj.github.io/agent-memory-starter-kit/install.sh | bash",
    "~/.local/bin/memory connect",
    "Check the local registry/default path before asking for a folder.",
    "Do not use git clone as the visible setup step.",
    "What do you want to do?",
    "1. memory new - Create a memory library",
    "2. memory connect - Connect this Agent to an existing memory library",
    "memory backup",
)
AGENTS_REQUIRED_SNIPPETS = (
    "# JourneyMem Agent Instructions",
    "install source fallback, not a generic codebase task",
    "If the user says exactly `memory`, `$journeymem`, `/memory`, or asks to use JourneyMem",
    "do not read files, inspect folders, or explain existing memory contents",
    "do not summarize the repository structure",
    "install or activate JourneyMem first",
    "curl -fsSL https://ivorywanj.github.io/agent-memory-starter-kit/install.sh | bash",
    "~/.local/bin/memory connect",
    "checks `~/.journeymem/registry.json` and the default JourneyMem library path before asking for a folder",
    "I can help you use JourneyMem.",
    "`memory new` - Create a new memory library",
    "`memory connect` - Connect this Agent to an existing memory library",
    "Keep the command labels exactly as `memory new`, `memory connect`, and `memory backup`; do not translate or paraphrase them.",
    "Do not start `memory new` until the user chooses create/new.",
    "Do not ask \"What should Agents call you?\" before that choice.",
    "Do not add tool mode limitations, execution caveats, or other extra notes to the first response.",
)
DOC_REQUIRED_SNIPPETS = (
    (
        "docs/productized-user-flow.md",
        (
            "Connect checks the local registry/default path before asking for any folder path",
            "Backup is available separately, not as a main first-use branch",
        ),
    ),
    (
        "docs/first-run-wizard.md",
        (
            "Do not show your internal analysis",
            "Do not run `memory new` until the user chooses option 1.",
            "If exactly one confident local candidate is found, connect automatically and do not ask for a folder path.",
        ),
    ),
    (
        "docs/workflows/memory-new.md",
        (
            "The first user-facing response contains exactly one setup question",
            "Do not show internal analysis, setup strategy, repository status",
        ),
    ),
    (
        "docs/workflows/memory-connect.md",
        (
            "Check `~/.journeymem/registry.json` for an existing default memory library.",
            "The first response does not ask for a folder path when the registry has one valid default library.",
        ),
    ),
    (
        "docs/workflows/agent-entry-transcripts.md",
        (
            "python3 scripts/score_agent_entry_transcripts.py",
            "python3 scripts/prd_acceptance_check.py",
            "python3 scripts/prepare_agent_entry_trials.py",
            "python3 scripts/collect_codex_entry_transcript.py",
            "python3 scripts/collect_cursor_entry_transcript.py",
            "python3 scripts/agent_entry_readiness.py",
            "python3 scripts/save_agent_entry_transcript.py",
            "--run-local-checks",
            "--require-agents codex,trae",
            "--require-scenarios valid_default,skill_trigger,start_page,github_fallback",
            "--require-trae-trials 3",
            "For raw transcript folders:",
            "codex-github-fallback-1.txt",
            "trae-start-page-1.txt",
            "prompt files intentionally imitate realistic user messages",
            "TRAE Work clone/inspect behavior count = 0.",
            "Folder-path prompt on valid default = 0.",
        ),
    ),
)
RUNTIME_REQUIRED_SNIPPETS = (
    "alwaysApply: true",
    "description: Always load JourneyMem",
    "This rule must be active in every new TRAE Work conversation",
    "Do not say you do not know until those files were checked.",
    "This connection file alone is not the memory.",
    "a complete answer requires reading",
    "TRAE_NATIVE_MEMORY_BEGIN",
    "This TRAE native memory file is connected",
    "This block is a bounded startup cache plus pointer",
    "upsert_marked_block",
    "TRAE native memory bridge",
    "{memory_cmd} connect",
    "curl -fsSL https://ivorywanj.github.io/agent-memory-starter-kit/install.sh | bash",
    "~/.local/bin/memory connect",
    "`connect`: run `{memory_cmd} connect`.",
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
        menu_index = readme_text.find("What do you want to do?")
        if menu_index == -1:
            findings.append("README.md missing first-use menu")
        else:
            before_menu = readme_text[:menu_index]
            for blocked_command in ("git clone ", "curl -fsSL", "./install.sh"):
                if blocked_command in before_menu:
                    findings.append(f"README.md promotes {blocked_command.strip()} before first-use menu")
            first_command_positions = [
                index
                for index in (
                    readme_text.find("git clone "),
                    readme_text.find("curl -fsSL"),
                    readme_text.find("./install.sh"),
                )
                if index != -1
            ]
            first_blocked_command = min(first_command_positions) if first_command_positions else len(readme_text)
            for snippet in ("1. memory new - Create a memory library", "2. memory connect - Connect this Agent to an existing memory library"):
                snippet_index = readme_text.find(snippet)
                if snippet_index == -1 or snippet_index > first_blocked_command:
                    findings.append(f"README.md first-use option appears after install/clone command: {snippet}")
        before_troubleshooting = readme_text.split("Then use these troubleshooting commands only when the Agent prompt flow is not available:", 1)[0]
        if "./scripts/memory new" in before_troubleshooting:
            findings.append("README.md promotes ./scripts/memory new before troubleshooting")
        if "git clone https://github.com/ivorywanj/agent-memory-starter-kit.git" in readme_text:
            findings.append("README.md exposes git clone as user-facing JourneyMem fallback")
    for rel in ("index.html", "docs/index.html"):
        start_page = ROOT / rel
        if not start_page.exists():
            findings.append(f"missing Start Page: {rel}")
            continue
        start_text = start_page.read_text(encoding="utf-8", errors="replace")
        for snippet in START_PAGE_REQUIRED_SNIPPETS:
            if snippet not in start_text:
                findings.append(f"{rel} missing snippet: {snippet}")
        first_screen = start_text.split("<!-- first-screen-end -->", 1)[0].lower()
        for term in README_FIRST_SCREEN_BLOCKED_TERMS:
            if term in first_screen:
                findings.append(f"{rel} first screen uses internal term: {term}")
        for snippet in ("1. memory new - create a memory library", "2. memory connect - connect this agent to an existing memory library"):
            if snippet not in first_screen:
                findings.append(f"{rel} first screen missing first-use option: {snippet}")
        for blocked_command in ("git clone ", "curl -fsSL", "./install.sh"):
            if blocked_command in first_screen:
                findings.append(f"{rel} first screen promotes install/clone command: {blocked_command.strip()}")
    for rel in AGENT_INSTRUCTION_FILES:
        agents_file = ROOT / rel
        if not agents_file.exists():
            continue
        agents_text = agents_file.read_text(encoding="utf-8", errors="replace")
        for snippet in AGENTS_REQUIRED_SNIPPETS:
            if snippet not in agents_text:
                findings.append(f"{rel} missing snippet: {snippet}")
    for rel, snippets in DOC_REQUIRED_SNIPPETS:
        doc_file = ROOT / rel
        if not doc_file.exists():
            findings.append(f"missing required doc: {rel}")
            continue
        doc_text = doc_file.read_text(encoding="utf-8", errors="replace")
        for snippet in snippets:
            if snippet not in doc_text:
                findings.append(f"{rel} missing snippet: {snippet}")
    runtime_file = ROOT / "scripts/memory_runtime.py"
    if runtime_file.exists():
        runtime_text = runtime_file.read_text(encoding="utf-8", errors="replace")
        for snippet in RUNTIME_REQUIRED_SNIPPETS:
            if snippet not in runtime_text:
                findings.append(f"scripts/memory_runtime.py missing snippet: {snippet}")
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
