#!/usr/bin/env python3
"""Print a compact status view for the lightweight memory system."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


HOT_TARGETS = {
    "USER.md": 1800,
    "MEMORY.md": 2400,
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def script_dir() -> Path:
    return Path(__file__).resolve().parent


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def file_chars(path: Path) -> int:
    return len(read_text(path))


def char_count(path: Path) -> str:
    if not path.exists():
        return "missing"
    return f"{file_chars(path)} chars"


def count_pending(root: Path) -> int:
    inbox = root / "memory/inbox"
    return len([p for p in inbox.glob("*.md") if p.name != "README.md"])


def hot_status(root: Path) -> tuple[list[str], int]:
    lines: list[str] = []
    warnings = 0
    for filename, target in HOT_TARGETS.items():
        path = root / "memory/hot" / filename
        if not path.exists():
            lines.append(f"  - {filename}: missing")
            warnings += 1
            continue
        chars = file_chars(path)
        state = "ok" if chars <= target else "over target"
        if chars > target:
            warnings += 1
        lines.append(f"  - {filename}: {state}, {chars} chars (target <= {target})")
    return lines, warnings


def startup_path_status(root: Path) -> tuple[str, int]:
    required = [
        "AGENTS.md",
        "ONBOARDING.md",
        "memory/hot/USER.md",
        "memory/hot/MEMORY.md",
    ]
    missing = [item for item in required if not (root / item).exists()]
    if missing:
        return f"missing {', '.join(missing)}", 1
    return "ready: AGENTS.md -> ONBOARDING.md -> memory/hot/USER.md -> memory/hot/MEMORY.md", 0


def baseline_status(root: Path) -> tuple[str, int]:
    pointer = root / "content/data/memory-benchmark/v1-candidate.md"
    if not pointer.exists():
        return "missing v1-candidate pointer", 1
    text = read_text(pointer)
    status_ok = "Status: v1-candidate" in text
    records = root / "content/data/memory-benchmark/runs/20260628-full-codex-post-t06-solved-rerun/benchmark-records.rescored.csv"
    if status_ok and records.exists():
        return f"v1-candidate ({pointer.relative_to(root)}; scored records present)", 0
    problems = []
    if not status_ok:
        problems.append("status marker missing")
    if not records.exists():
        problems.append("rescored CSV missing")
    return f"attention: {', '.join(problems)}", 1


def fusion_status(root: Path) -> tuple[str, int]:
    pointer = root / "content/data/memory-benchmark/fusion-candidate.md"
    if not pointer.exists():
        return "not configured", 0
    text = read_text(pointer)
    status_ok = "Status: **v1-fusion-candidate**" in text
    records = root / "content/data/memory-benchmark/runs/20260629-fusion-post-wrapper-rerun/benchmark-records.rescored.csv"
    if status_ok and records.exists():
        return f"v1-fusion-candidate ({pointer.relative_to(root)}; post-run scored records present)", 0
    problems = []
    if not status_ok:
        problems.append("status marker missing")
    if not records.exists():
        problems.append("post-run rescored CSV missing")
    return f"attention: {', '.join(problems)}", 1


def history_status(root: Path) -> tuple[str, int]:
    history_db = root / "memory/history/runtime/history.sqlite3"
    if history_db.exists():
        return f"present ({history_db.relative_to(root)})", 0
    return "missing (build only when historical recall is needed)", 1


def guard_status(root: Path) -> str:
    result = subprocess.run(
        [sys.executable, str(script_dir() / "memory_guard.py"), "--root", str(root)],
        cwd=script_dir().parent,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    first = result.stdout.strip().splitlines()[0] if result.stdout.strip() else "memory_guard: no output"
    return f"{first} (exit {result.returncode})"


def next_action(blockers: int, warnings: int, pending: int) -> str:
    if blockers:
        return "Fix missing baseline/startup files or safety failures before exporting or calling this v1-ready."
    if pending:
        return "Review meaningful inbox candidates with /memory-promotion-review when there is enough evidence."
    if warnings:
        return "Optional cleanup: compress over-target hot memory with scripts/build_hot_memory.py drafts, then review manually."
    return "No action required; v1 quickstart is ready."


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a compact status view for the lightweight memory system.")
    parser.add_argument("--root", type=Path, default=None, help="Memory library root to inspect. Defaults to this repo.")
    args = parser.parse_args()

    root = args.root.expanduser().resolve() if args.root else repo_root()
    blockers = 0
    warnings = 0
    pending = count_pending(root)
    baseline, baseline_blockers = baseline_status(root)
    fusion, fusion_blockers = fusion_status(root)
    startup_path, startup_blockers = startup_path_status(root)
    hot_lines, hot_warnings = hot_status(root)
    history, history_warnings = history_status(root)
    guard = guard_status(root)
    guard_blocker = 0 if "memory_guard: pass" in guard and "(exit 0)" in guard else 1

    blockers += baseline_blockers + fusion_blockers + startup_blockers + guard_blocker
    warnings += hot_warnings + history_warnings
    overall = "blocked" if blockers else ("ready_with_warnings" if warnings else "ready")

    print("Memory Status")
    print(f"- Overall: {overall}")
    print(f"- V1 baseline: {baseline}")
    print(f"- Codex fusion: {fusion}")
    print(f"- Startup path: {startup_path}")
    print("- Hot memory:")
    for line in hot_lines:
        print(line)
    print(f"- Pending inbox candidates: {pending}")
    print(f"- History index: {history}")
    print(f"- Safety scan: {guard}")
    print(f"- Next action: {next_action(blockers, warnings, pending)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
