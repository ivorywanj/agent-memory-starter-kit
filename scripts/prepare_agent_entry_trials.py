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
- `trae-valid-default-1.txt`
- `trae-valid-default-2.txt`
- `trae-valid-default-3.txt`

The expected first response is a quiet two-choice JourneyMem menu with `memory new` and `memory connect`.
Cursor transcripts are optional and not required for the PRD gate.
"""


PROMPT = """You are testing JourneyMem first-run behavior. Treat the user command as `memory`.

Do not use tools.
Do not browse folders.
Do not inspect files.
Do not summarize the repository structure.
Do not run `memory new` or `memory connect` yet.
Do not ask for a memory library folder path.

Reply exactly with this menu and no other text:

What do you want to do?
1. memory new - Create a memory library
2. memory connect - Connect this Agent to an existing memory library
"""


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
    for name in ("codex", "trae-valid-default-1", "trae-valid-default-2", "trae-valid-default-3"):
        (prompts / f"{name}.prompt.txt").write_text(PROMPT, encoding="utf-8")


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
