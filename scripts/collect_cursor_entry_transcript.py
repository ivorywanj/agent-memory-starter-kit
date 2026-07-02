#!/usr/bin/env python3
"""Collect one real Cursor first-response transcript for JourneyMem entry testing."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


DEFAULT_CURSOR_BIN = Path("/usr/local/bin/cursor")
USAGE_LIMIT_MARKER = "You've hit your usage limit"
SCENARIOS = ("valid-default", "skill-trigger", "start-page", "github-fallback")


def build_command(args: argparse.Namespace, prompt: str) -> list[str]:
    command = [
        str(args.cursor_bin),
        "agent",
        "--print",
        "--mode",
        "ask",
        "--sandbox",
        "enabled",
        "--trust",
        "--workspace",
        str(args.workspace),
    ]
    if args.model:
        command.extend(["--model", args.model])
    command.append(prompt)
    return command


def run_score(root: Path, transcript: Path, scenario: str) -> int:
    scorer = root / "scripts/score_agent_entry_transcripts.py"
    if not scorer.exists():
        print(f"score_skipped: missing {scorer}")
        return 0
    completed = subprocess.run(
        [
            sys.executable,
            str(scorer),
            "--input",
            str(transcript),
            "--require-agents",
            "cursor",
            "--require-scenarios",
            scenario.replace("-", "_"),
        ],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    print(completed.stdout.rstrip())
    return completed.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Collect a real Cursor first-response transcript.")
    parser.add_argument("--trial-pack", type=Path, default=Path("agent-entry-trials"), help="Trial pack directory.")
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace passed to Cursor.")
    parser.add_argument("--cursor-bin", type=Path, default=DEFAULT_CURSOR_BIN, help="Cursor CLI executable.")
    parser.add_argument("--model", default="", help="Optional Cursor model name.")
    parser.add_argument("--scenario", choices=SCENARIOS, default="valid-default", help="Prompt scenario to collect.")
    parser.add_argument("--timeout", type=int, default=180, help="Cursor command timeout in seconds.")
    parser.add_argument("--dry-run", action="store_true", help="Print command without calling Cursor.")
    parser.add_argument("--no-score", action="store_true", help="Do not run the transcript scorer after collection.")
    args = parser.parse_args(argv)

    prompt_path = args.trial_pack / f"prompts/cursor-{args.scenario}-1.prompt.txt"
    transcript_path = args.trial_pack / f"transcripts/cursor-{args.scenario}-1.txt"
    if not prompt_path.exists():
        raise SystemExit(f"missing_prompt: {prompt_path}")
    transcript_path.parent.mkdir(parents=True, exist_ok=True)
    prompt = prompt_path.read_text(encoding="utf-8")
    command = build_command(args, prompt)
    if args.dry_run:
        print("cursor_entry_command:")
        print(" ".join(command[:-1]) + " <prompt>")
        print(f"prompt: {prompt_path}")
        print(f"transcript: {transcript_path}")
        return 0

    try:
        completed = subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=args.timeout,
        )
    except subprocess.TimeoutExpired:
        print("cursor_entry_failed: timeout")
        return 1
    except OSError as exc:
        print(f"cursor_entry_failed: {exc}")
        return 1

    transcript = completed.stdout.strip()
    if completed.returncode != 0 or not transcript or USAGE_LIMIT_MARKER in transcript:
        print("cursor_entry_failed: command did not produce a usable transcript")
        if transcript:
            print(transcript[:1200])
        return 1
    transcript_path.write_text(transcript.rstrip() + "\n", encoding="utf-8")
    print(f"cursor_entry_transcript: {transcript_path}")
    if args.no_score:
        return 0
    return run_score(Path.cwd(), transcript_path, args.scenario)


if __name__ == "__main__":
    raise SystemExit(main())
