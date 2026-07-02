#!/usr/bin/env python3
"""Report JourneyMem PRD A01-A17 acceptance status."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


CRITERIA: tuple[tuple[str, str], ...] = (
    ("A01", "README clone-first exposure"),
    ("A02", "TRAE clone-first trigger rate"),
    ("A03", "First-menu success rate"),
    ("A04", "First-response noise"),
    ("A05", "Existing-library auto-detection"),
    ("A06", "Invalid-registry fallback"),
    ("A07", "Folder-path prompt on valid default"),
    ("A08", "Multi-library selection"),
    ("A09", "New-user onboarding pacing"),
    ("A10", "Backup separation"),
    ("A11", "Secret write rate"),
    ("A12", "Public package privacy"),
    ("A13", "Regression tests"),
    ("A14", "Cross-Agent command availability"),
    ("A15", "Release readiness"),
    ("A16", "memory connect existing-library success"),
    ("A17", "Cross-computer backup restore"),
)

TRANSCRIPT_IDS = {"A02", "A03", "A04", "A07", "A09", "A14"}
LOCAL_TEST_IDS = {"A05", "A06", "A08", "A10", "A13", "A17"}


@dataclass
class CheckResult:
    status: str
    detail: str

    @property
    def passed(self) -> bool:
        return self.status == "pass"


def run_command(command: list[str], root: Path, timeout: int) -> CheckResult:
    try:
        completed = subprocess.run(
            command,
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return CheckResult("fail", f"timeout: {' '.join(command)}")
    except OSError as exc:
        return CheckResult("fail", f"command_error: {exc}")
    if completed.returncode == 0:
        return CheckResult("pass", "ok")
    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    summary_lines = [
        line
        for line in lines
        if line.startswith(("- records:", "- failed:", "- missing_agents:", "- trae_trials:", "- status:"))
    ]
    detail = "; ".join(summary_lines[:5]) or (lines[0] if lines else f"exit_{completed.returncode}")
    return CheckResult("fail", detail[:220])


def transcript_check(root: Path, transcripts: Path | None, require_trae_trials: int, timeout: int) -> CheckResult:
    if transcripts is None:
        return CheckResult("fail", "missing transcript evidence")
    if not transcripts.exists():
        return CheckResult("fail", f"transcript path missing: {transcripts}")
    scorer = root / "scripts/score_agent_entry_transcripts.py"
    if not scorer.exists():
        return CheckResult("fail", "missing scripts/score_agent_entry_transcripts.py")
    command = [
        sys.executable,
        str(scorer.relative_to(root)),
        "--input",
        str(transcripts),
        "--require-agents",
        "codex,trae",
        "--require-trae-trials",
        str(require_trae_trials),
    ]
    return run_command(command, root=root, timeout=timeout)


def local_checks(root: Path, run_local_checks: bool, timeout: int) -> dict[str, CheckResult]:
    if not run_local_checks:
        return {
            "release": CheckResult("fail", "not run; pass --run-local-checks"),
            "guard": CheckResult("fail", "not run; pass --run-local-checks"),
            "tests": CheckResult("fail", "not run; pass --run-local-checks"),
            "diff": CheckResult("fail", "not run; pass --run-local-checks"),
        }
    checks: dict[str, CheckResult] = {}
    release_script = root / "scripts/public_release_check.py"
    if release_script.exists():
        checks["release"] = run_command([sys.executable, "scripts/public_release_check.py"], root, timeout)
    else:
        checks["release"] = CheckResult("fail", "missing scripts/public_release_check.py")
    guard_script = root / "scripts/memory_guard.py"
    if guard_script.exists():
        checks["guard"] = run_command([sys.executable, "scripts/memory_guard.py"], root, timeout)
    else:
        checks["guard"] = CheckResult("fail", "missing scripts/memory_guard.py")
    public_tests = root / "tests/test_public_package.py"
    if public_tests.exists():
        checks["tests"] = run_command([sys.executable, "tests/test_public_package.py"], root, timeout)
    else:
        checks["tests"] = CheckResult("fail", "missing tests/test_public_package.py")
    if (root / ".git").exists():
        checks["diff"] = run_command(["git", "diff", "--check"], root, timeout)
    else:
        checks["diff"] = CheckResult("pass", "no git repo; skipped")
    return checks


def build_results(
    *,
    mode: str,
    root: Path,
    transcripts: Path | None,
    require_trae_trials: int,
    run_local: bool,
    timeout: int,
) -> dict[str, CheckResult]:
    transcript = transcript_check(root, transcripts, require_trae_trials, timeout)
    if mode == "transcript-only":
        return {criterion_id: transcript for criterion_id in sorted(TRANSCRIPT_IDS)}

    local = local_checks(root, run_local, timeout)
    release = local["release"]
    guard = local["guard"]
    tests = local["tests"]
    diff = local["diff"]
    results: dict[str, CheckResult] = {}
    for criterion_id, _name in CRITERIA:
        if criterion_id in TRANSCRIPT_IDS:
            results[criterion_id] = transcript
        elif criterion_id in {"A01", "A12"}:
            results[criterion_id] = release
        elif criterion_id == "A11":
            results[criterion_id] = guard
        elif criterion_id in LOCAL_TEST_IDS:
            results[criterion_id] = tests
        elif criterion_id == "A16":
            results[criterion_id] = (
                CheckResult("pass", "fixture and transcript evidence ok")
                if tests.passed and transcript.passed
                else CheckResult("fail", f"tests={tests.status}; transcripts={transcript.status}")
            )
        elif criterion_id == "A15":
            prereqs = (release, guard, tests, diff, transcript)
            results[criterion_id] = (
                CheckResult("pass", "all release checks passed")
                if all(item.passed for item in prereqs)
                else CheckResult(
                    "fail",
                    "release="
                    f"{release.status}; guard={guard.status}; tests={tests.status}; diff={diff.status}; transcripts={transcript.status}",
                )
            )
        else:
            results[criterion_id] = CheckResult("fail", "unmapped criterion")
    return results


def print_results(mode: str, root: Path, results: dict[str, CheckResult]) -> None:
    print("PRD Acceptance Check")
    print(f"- mode: {mode}")
    print(f"- root: {root}")
    passed = 0
    for criterion_id, name in CRITERIA:
        if criterion_id not in results:
            continue
        result = results[criterion_id]
        if result.passed:
            passed += 1
        print(f"{criterion_id} {result.status} - {name} - {result.detail}")
    print(f"- passed: {passed}")
    print(f"- failed: {len(results) - passed}")
    print(f"- status: {'pass' if passed == len(results) else 'fail'}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check JourneyMem PRD A01-A17 acceptance status.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="JourneyMem package root.")
    parser.add_argument("--transcripts", type=Path, default=None, help="Real Agent transcript JSONL/file directory.")
    parser.add_argument("--require-trae-trials", type=int, default=3, help="Required TRAE Work transcript count.")
    parser.add_argument("--run-local-checks", action="store_true", help="Run public tests, guard, release check, and diff check.")
    parser.add_argument(
        "--mode",
        choices=("full", "transcript-only"),
        default="full",
        help="Use transcript-only for focused real-Agent evidence scoring.",
    )
    parser.add_argument("--timeout", type=int, default=240, help="Per-command timeout in seconds.")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    results = build_results(
        mode=args.mode,
        root=root,
        transcripts=args.transcripts.resolve() if args.transcripts else None,
        require_trae_trials=args.require_trae_trials,
        run_local=args.run_local_checks,
        timeout=args.timeout,
    )
    print_results(args.mode, root, results)
    return 0 if all(result.passed for result in results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
