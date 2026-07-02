#!/usr/bin/env python3
"""Create a real-Agent first-response transcript collection pack."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


README = """# JourneyMem Agent Entry Trial Pack

Use this pack to collect required real first-response evidence from Codex and TRAE Work.

## What To Do

1. Open the target Agent.
2. Paste the matching prompt from `prompts/`.
3. Save only the first visible Agent response into `transcripts/`.
4. Do not include your follow-up messages or tool logs.
5. Run the PRD gate from the JourneyMem package root:

```bash
python3 scripts/prd_acceptance_check.py \\
  --transcripts {transcripts_dir} \\
  --require-trae-trials 3 \\
  --run-local-checks
```

## Required Transcript Files

- `codex-valid-default-1.txt`
- `codex-skill-trigger-1.txt`
- `codex-start-page-1.txt`
- `codex-github-fallback-1.txt`
- `trae-valid-default-1.txt`
- `trae-skill-trigger-1.txt`
- `trae-start-page-1.txt`
- `trae-github-fallback-1.txt`

The expected first response is a quiet two-choice JourneyMem menu with `memory new` and `memory connect`.
Cursor transcripts are optional and not required for the PRD gate.

Prompts are intentionally one line so Agent input boxes do not split the instruction into partial messages.
"""


MENU = "What do you want to do? 1. memory new - Create a memory library 2. memory connect - Connect this Agent to an existing memory library"


PROMPTS = {
    "valid-default": "You are testing JourneyMem first-run behavior. Treat the user command as `memory`. Do not use tools, browse folders, inspect files, summarize the repository structure, run `memory new`, run `memory connect`, or ask for a memory library folder path. Reply exactly with this menu and no other text: {menu}",
    "skill-trigger": "You are testing JourneyMem skill-trigger behavior. Treat the user command as `$journeymem`. Do not use tools, browse folders, inspect files, summarize the repository structure, run `memory new`, run `memory connect`, or ask for a memory library folder path. Reply exactly with this menu and no other text: {menu}",
    "start-page": "JourneyMem Start Page instruction: show the first-use menu before doing anything else. Do not clone, inspect files, summarize the repo, run commands, or ask for a folder path. Reply with only: {menu}",
    "github-fallback": "JourneyMem install source: https://github.com/ivorywanj/agent-memory-starter-kit. This is not a codebase task. Do not clone, inspect files, summarize the repo, run commands, or ask what to do with this repo. Reply with only: {menu}",
}


def prompt_text(key: str) -> str:
    return PROMPTS[key].format(menu=MENU)


def write_pack(output: Path, force: bool) -> None:
    if output.exists():
        if not force:
            raise SystemExit(f"trial_pack_exists: {output}")
        shutil.rmtree(output)
    prompts = output / "prompts"
    transcripts = output / "transcripts"
    prompts.mkdir(parents=True)
    transcripts.mkdir()
    (transcripts / ".gitkeep").write_text("", encoding="utf-8")
    readme = README.format(transcripts_dir=transcripts)
    (output / "README.md").write_text(readme, encoding="utf-8")
    for agent in ("codex", "cursor", "trae"):
        for scenario in ("valid-default", "skill-trigger", "start-page", "github-fallback"):
            (prompts / f"{agent}-{scenario}-1.prompt.txt").write_text(prompt_text(scenario), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create JourneyMem real-Agent transcript collection files.")
    parser.add_argument("--output", type=Path, default=Path("agent-entry-trials"), help="Output trial pack directory.")
    parser.add_argument("--force", action="store_true", help="Replace an existing trial pack directory.")
    args = parser.parse_args(argv)

    write_pack(args.output, args.force)
    print(f"agent_entry_trial_pack: {args.output}")
    print(f"transcripts_dir: {args.output / 'transcripts'}")
    print("next: paste prompts into Codex and TRAE Work, then save first responses into transcripts/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
