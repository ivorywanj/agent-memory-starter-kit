#!/usr/bin/env python3
"""Score real Agent entry transcripts for JourneyMem first-run acceptance."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any


REQUIRED_MENU_TERMS = ("memory new", "memory connect")
NOISY_PHRASES = (
    "repo cloned successfully",
    "repository structure",
    "project structure",
    "inspect the structure",
    "understand the cli",
    "setup wizard",
    "answers file",
    "non-interactive setup",
    "use sensible defaults",
    "what would you like to do next?",
)
CLONE_OR_INSPECT_PATTERNS = (
    re.compile(r"\brepo cloned successfully\b", re.I),
    re.compile(r"\bclone(?:d|s|ing)?\b.{0,80}\b(agent-memory-starter-kit|journeymem|repo|repository)\b", re.I),
    re.compile(r"\binspect(?:ed|s|ing)?\b.{0,80}\b(repo|repository|project structure|scripts/memory)\b", re.I),
    re.compile(r"\b(project|repo|repository) structure\b", re.I),
)
FOLDER_PROMPT_PATTERNS = (
    re.compile(r"\bplease paste\b.{0,80}\b(folder|path|memory library)\b", re.I),
    re.compile(r"\bpaste\b.{0,80}\b(full folder path|memory library folder)\b", re.I),
    re.compile(r"\bprovide\b.{0,80}\b(full folder path|memory library folder)\b", re.I),
    re.compile(r"\bwhere\b.{0,80}\b(memory library folder|memory library path)\b", re.I),
)
RAW_TRANSCRIPT_SUFFIXES = {".txt", ".md"}
KNOWN_AGENTS = ("codex", "cursor", "trae")


def infer_agent(path: Path) -> str:
    stem = path.stem.lower()
    for agent in KNOWN_AGENTS:
        if agent in stem:
            return agent
    return ""


def infer_scenario(path: Path) -> str:
    stem = path.stem.lower().replace("-", "_")
    if "valid_default" in stem:
        return "valid_default"
    return ""


def load_directory_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item in sorted(path.iterdir()):
        if not item.is_file() or item.suffix.lower() not in RAW_TRANSCRIPT_SUFFIXES:
            continue
        records.append(
            {
                "id": item.stem,
                "agent": infer_agent(item),
                "scenario": infer_scenario(item),
                "text": item.read_text(encoding="utf-8"),
            }
        )
    return records


def load_records(path: Path) -> list[dict[str, Any]]:
    if path.is_dir():
        return load_directory_records(path)
    if path.suffix.lower() in RAW_TRANSCRIPT_SUFFIXES:
        return [
            {
                "id": path.stem,
                "agent": infer_agent(path),
                "scenario": infer_scenario(path),
                "text": path.read_text(encoding="utf-8"),
            }
        ]
    text = path.read_text(encoding="utf-8")
    stripped = text.strip()
    if not stripped:
        return []
    if stripped.startswith("["):
        data = json.loads(stripped)
        if not isinstance(data, list):
            raise ValueError("JSON transcript input must be a list of records")
        return [dict(item) for item in data]
    records: list[dict[str, Any]] = []
    for line in stripped.splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def first_output(record: dict[str, Any]) -> str:
    return str(record.get("first_output") or record.get("output") or record.get("text") or "")


def contains_clone_or_inspect(text: str) -> bool:
    head = text[:1600]
    return any(pattern.search(head) for pattern in CLONE_OR_INSPECT_PATTERNS)


def noisy_phrase_count(text: str) -> int:
    lowered = text.lower()
    return sum(1 for phrase in NOISY_PHRASES if phrase in lowered)


def asks_folder_path(text: str) -> bool:
    head = text[:1600]
    return any(pattern.search(head) for pattern in FOLDER_PROMPT_PATTERNS)


def question_count(text: str) -> int:
    return text.count("?") + text.count("？")


def score_record(record: dict[str, Any]) -> dict[str, Any]:
    text = first_output(record)
    lowered = text.lower()
    scenario = str(record.get("scenario") or "")
    valid_default = bool(record.get("valid_default") or "valid_default" in scenario)
    menu_hit = all(term in lowered for term in REQUIRED_MENU_TERMS)
    clone_or_inspect = contains_clone_or_inspect(text)
    noisy_count = noisy_phrase_count(text)
    folder_prompt = asks_folder_path(text) if valid_default else False
    questions = question_count(text)
    command_available = "memory" in lowered
    passed = menu_hit and not clone_or_inspect and noisy_count == 0 and not folder_prompt and questions <= 1 and command_available
    return {
        "id": record.get("id") or "",
        "agent": record.get("agent") or "",
        "scenario": scenario,
        "pass": int(passed),
        "menu_hit": int(menu_hit),
        "clone_or_inspect": int(clone_or_inspect),
        "noisy_phrase_count": noisy_count,
        "folder_prompt_on_valid_default": int(folder_prompt),
        "question_count": questions,
        "command_available": int(command_available),
    }


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score real JourneyMem Agent entry transcripts.")
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="JSON array, JSONL transcript records, or a directory of raw .txt/.md first responses.",
    )
    parser.add_argument("--output", type=Path, default=None, help="Optional CSV output path.")
    parser.add_argument(
        "--require-agents",
        default="",
        help="Comma-separated required Agent names, for example: codex,cursor,trae.",
    )
    parser.add_argument("--require-trae-trials", type=int, default=0, help="Minimum TRAE Work transcript count required.")
    args = parser.parse_args(argv)

    if not args.input.exists():
        print("Agent Entry Transcript Score")
        print(f"- input_missing: {args.input}")
        print("- status: fail")
        return 1

    records = load_records(args.input)
    rows = [score_record(record) for record in records]
    if args.output:
        write_csv(rows, args.output)

    total = len(rows)
    passed = sum(row["pass"] for row in rows)
    present_agents = {str(row["agent"]).strip().lower().replace(" work", "") for row in rows if row["agent"]}
    required_agents = {
        agent.strip().lower().replace(" work", "")
        for agent in args.require_agents.split(",")
        if agent.strip()
    }
    missing_agents = sorted(required_agents - present_agents)
    trae_count = sum(1 for row in rows if str(row["agent"]).strip().lower().replace(" work", "") == "trae")
    failures = [row for row in rows if not row["pass"]]
    print("Agent Entry Transcript Score")
    print(f"- records: {total}")
    print(f"- passed: {passed}")
    print(f"- failed: {len(failures)}")
    if required_agents:
        print(f"- required_agents: {','.join(sorted(required_agents))}")
        print(f"- missing_agents: {','.join(missing_agents) if missing_agents else 'none'}")
    print(f"- trae_trials: {trae_count}")
    if args.require_trae_trials:
        print(f"- required_trae_trials: {args.require_trae_trials}")
    for row in failures[:12]:
        print(
            "- fail:"
            f" {row['id'] or '<no-id>'}"
            f" agent={row['agent']}"
            f" menu={row['menu_hit']}"
            f" clone_or_inspect={row['clone_or_inspect']}"
            f" noise={row['noisy_phrase_count']}"
            f" folder_prompt={row['folder_prompt_on_valid_default']}"
            f" questions={row['question_count']}"
            f" command={row['command_available']}"
        )

    status_ok = total > 0 and passed == total and not missing_agents and trae_count >= args.require_trae_trials
    print(f"- status: {'pass' if status_ok else 'fail'}")
    return 0 if status_ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
