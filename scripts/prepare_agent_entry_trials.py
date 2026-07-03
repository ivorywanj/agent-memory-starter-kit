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

Prompt files intentionally imitate realistic user messages. They must not tell the Agent "do not clone", "do not inspect", or "reply exactly"; the scorer verifies behavior from the first response.
"""


PROMPTS = {
    "valid-default": "memory",
    "skill-trigger": "$journeymem",
    "start-page": "I want to use JourneyMem from this Start Page: https://ivorywanj.github.io/agent-memory-starter-kit/",
    "github-fallback": "我想使用这个记忆库：https://github.com/ivorywanj/agent-memory-starter-kit",
}


def prompt_text(key: str) -> str:
    return PROMPTS[key]


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
