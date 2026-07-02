#!/usr/bin/env python3
"""Save a manually collected Agent entry transcript with the correct filename."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis)://[^\s`\"<>]+", re.I),
    re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"),
    re.compile(r"https://[^\s`\"<>]*(?:hooks\.slack\.com|open\.feishu\.cn|discord(?:app)?\.com/api/webhooks)[^\s`\"<>]+", re.I),
)


def transcript_name(agent: str, trial: int) -> str:
    if agent in {"codex", "cursor"}:
        if trial != 1:
            raise SystemExit(f"{agent}_trial_must_be_1")
        return f"{agent}-valid-default-1.txt"
    if agent == "trae":
        if trial not in {1, 2, 3}:
            raise SystemExit("trae_trial_must_be_1_2_or_3")
        return f"trae-valid-default-{trial}.txt"
    raise SystemExit(f"unsupported_agent: {agent}")


def read_text(args: argparse.Namespace) -> str:
    if args.text:
        return args.text
    if args.input:
        return args.input.read_text(encoding="utf-8")
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise SystemExit("missing_transcript_text")


def ensure_safe(text: str) -> None:
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            raise SystemExit("transcript_blocked: secret_like_text")


def run_score(root: Path, transcript: Path, agent: str) -> int:
    scorer = root / "scripts/score_agent_entry_transcripts.py"
    if not scorer.exists():
        print(f"score_skipped: missing {scorer}")
        return 0
    command = [
        sys.executable,
        str(scorer),
        "--input",
        str(transcript),
        "--require-agents",
        agent,
    ]
    if agent == "trae":
        command.extend(["--require-trae-trials", "1"])
    completed = subprocess.run(
        command,
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    print(completed.stdout.rstrip())
    return completed.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Save a real Agent entry transcript for JourneyMem acceptance.")
    parser.add_argument("--trial-pack", type=Path, default=Path("agent-entry-trials"), help="Trial pack directory.")
    parser.add_argument("--agent", choices=("codex", "cursor", "trae"), required=True)
    parser.add_argument("--trial", type=int, default=1, help="Trial number. TRAE requires 1, 2, or 3.")
    parser.add_argument("--input", type=Path, default=None, help="Path to a text file containing the first visible Agent response.")
    parser.add_argument("--text", default="", help="Transcript text. Prefer --input or stdin for multi-line text.")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing transcript file.")
    parser.add_argument("--no-score", action="store_true", help="Do not run the transcript scorer after saving.")
    args = parser.parse_args(argv)

    text = read_text(args).strip()
    if not text:
        raise SystemExit("empty_transcript")
    ensure_safe(text)
    target = args.trial_pack / "transcripts" / transcript_name(args.agent, args.trial)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not args.force:
        raise SystemExit(f"transcript_exists: {target}")
    target.write_text(text.rstrip() + "\n", encoding="utf-8")
    print(f"transcript_saved: {target}")
    if args.no_score:
        return 0
    return run_score(Path.cwd(), target, args.agent)


if __name__ == "__main__":
    raise SystemExit(main())
