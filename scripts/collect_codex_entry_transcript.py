#!/usr/bin/env python3
"""Collect one real Codex first-response transcript for JourneyMem entry testing."""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path


DEFAULT_CODEX_BIN = Path("/Applications/Codex.app/Contents/Resources/codex")
USAGE_LIMIT_MARKER = "You've hit your usage limit"


def extract_assistant_text(stdout: str) -> str:
    if USAGE_LIMIT_MARKER in stdout:
        return ""
    lines = stdout.splitlines()
    assistant_indexes = [index for index, line in enumerate(lines) if line.strip() == "assistant"]
    if not assistant_indexes:
        return stdout.strip()
    collected: list[str] = []
    for line in lines[assistant_indexes[-1] + 1 :]:
        if line.startswith("--------"):
            break
        collected.append(line)
    return "\n".join(collected).strip()


def build_command(args: argparse.Namespace, raw_output: Path) -> list[str]:
    command = [
        str(args.codex_bin),
        "exec",
        "--ephemeral",
        "--sandbox",
        "read-only",
        "--skip-git-repo-check",
        "-C",
        str(args.workspace),
        "-o",
        str(raw_output),
    ]
    if args.model:
        command.extend(["-m", args.model])
    command.append("-")
    return command


def run_score(root: Path, transcript: Path) -> int:
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
            "codex",
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
    parser = argparse.ArgumentParser(description="Collect a real Codex first-response transcript.")
    parser.add_argument("--trial-pack", type=Path, default=Path("agent-entry-trials"), help="Trial pack directory.")
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Workspace passed to Codex -C.")
    parser.add_argument("--codex-bin", type=Path, default=DEFAULT_CODEX_BIN, help="Codex CLI executable.")
    parser.add_argument("--model", default="", help="Optional Codex model name.")
    parser.add_argument("--timeout", type=int, default=180, help="Codex command timeout in seconds.")
    parser.add_argument("--dry-run", action="store_true", help="Print command without calling Codex.")
    parser.add_argument("--no-score", action="store_true", help="Do not run the transcript scorer after collection.")
    args = parser.parse_args(argv)

    prompt_path = args.trial_pack / "prompts/codex.prompt.txt"
    transcript_path = args.trial_pack / "transcripts/codex-valid-default-1.txt"
    if not prompt_path.exists():
        raise SystemExit(f"missing_prompt: {prompt_path}")
    transcript_path.parent.mkdir(parents=True, exist_ok=True)
    prompt = prompt_path.read_text(encoding="utf-8")

    with tempfile.TemporaryDirectory() as tmp:
        raw_output = Path(tmp) / "codex-output.txt"
        command = build_command(args, raw_output)
        if args.dry_run:
            print("codex_entry_command:")
            print(" ".join(command))
            print(f"prompt: {prompt_path}")
            print(f"transcript: {transcript_path}")
            return 0
        try:
            completed = subprocess.run(
                command,
                input=prompt,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
                timeout=args.timeout,
            )
        except subprocess.TimeoutExpired:
            print("codex_entry_failed: timeout")
            return 1
        except OSError as exc:
            print(f"codex_entry_failed: {exc}")
            return 1

        raw_text = raw_output.read_text(encoding="utf-8", errors="replace").strip() if raw_output.exists() else ""
        transcript = raw_text or extract_assistant_text(completed.stdout)
        if completed.returncode != 0 or not transcript or USAGE_LIMIT_MARKER in completed.stdout:
            print("codex_entry_failed: command did not produce a usable transcript")
            if completed.stdout.strip():
                print(completed.stdout.strip()[:1200])
            return 1
        transcript_path.write_text(transcript.rstrip() + "\n", encoding="utf-8")

    print(f"codex_entry_transcript: {transcript_path}")
    if args.no_score:
        return 0
    return run_score(Path.cwd(), transcript_path)


if __name__ == "__main__":
    raise SystemExit(main())
