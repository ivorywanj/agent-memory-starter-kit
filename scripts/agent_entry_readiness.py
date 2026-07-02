#!/usr/bin/env python3
"""Explain readiness for JourneyMem real Agent entry acceptance."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


REQUIRED_TRANSCRIPTS = (
    "codex-valid-default-1.txt",
    "trae-valid-default-1.txt",
    "trae-valid-default-2.txt",
    "trae-valid-default-3.txt",
)


def executable(path: str) -> bool:
    return bool(shutil.which(path))


def codex_available() -> bool:
    return executable("codex") or Path("/Applications/Codex.app/Contents/Resources/codex").exists()


def cursor_available() -> bool:
    return executable("cursor")


def trae_available() -> bool:
    return executable("trae") or executable("trae-work")


def run_scorer(root: Path, transcripts: Path) -> tuple[int, str]:
    scorer = root / "scripts/score_agent_entry_transcripts.py"
    if not scorer.exists():
        return 1, f"missing scorer: {scorer}"
    completed = subprocess.run(
        [
            sys.executable,
            str(scorer),
            "--input",
            str(transcripts),
            "--require-agents",
            "codex,trae",
            "--require-trae-trials",
            "3",
        ],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return completed.returncode, completed.stdout.strip()


def transcript_status(transcripts: Path) -> dict[str, bool]:
    return {name: (transcripts / name).exists() for name in REQUIRED_TRANSCRIPTS}


def next_actions(transcripts: Path) -> list[str]:
    status = transcript_status(transcripts)
    actions: list[str] = []
    if not status["codex-valid-default-1.txt"]:
        actions.append("Run: python3 scripts/collect_codex_entry_transcript.py --trial-pack <trial-pack>")
    missing_trae = [name for name in REQUIRED_TRANSCRIPTS if name.startswith("trae-") and not status[name]]
    if missing_trae:
        actions.append("Save real TRAE Work first responses into: " + ", ".join(missing_trae))
    if not actions:
        actions.append("Run: python3 scripts/prd_acceptance_check.py --transcripts <transcripts> --require-trae-trials 3 --run-local-checks")
    return actions


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Show JourneyMem real Agent entry acceptance readiness.")
    parser.add_argument("--trial-pack", type=Path, default=Path("agent-entry-trials"), help="Trial pack directory.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="JourneyMem package root.")
    args = parser.parse_args(argv)

    transcripts = args.trial_pack / "transcripts"
    print("Agent Entry Readiness")
    print(f"- trial_pack: {args.trial_pack}")
    print(f"- transcripts: {transcripts}")
    print(f"- cli_codex: {'available' if codex_available() else 'missing'}")
    print(f"- cli_cursor: {'available' if cursor_available() else 'missing'}")
    print(f"- cli_trae: {'available' if trae_available() else 'missing'}")
    if not transcripts.exists():
        print("- transcript_dir: missing")
        print("- next: python3 scripts/prepare_agent_entry_trials.py --output " + str(args.trial_pack))
        print("- status: fail")
        return 1
    status = transcript_status(transcripts)
    for name, exists in status.items():
        print(f"- transcript_{name}: {'present' if exists else 'missing'}")
    scorer_rc, scorer_output = run_scorer(args.root, transcripts)
    print("- scorer:")
    for line in scorer_output.splitlines():
        print(f"  {line}")
    print("- next_actions:")
    for action in next_actions(transcripts):
        print(f"  - {action}")
    print(f"- status: {'pass' if scorer_rc == 0 else 'fail'}")
    return scorer_rc


if __name__ == "__main__":
    raise SystemExit(main())
