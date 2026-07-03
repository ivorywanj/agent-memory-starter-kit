---
name: "journeymem"
description: "Shows JourneyMem memory new/connect menu. Invoke when user says JourneyMem, memory, memory new/connect/backup, or mentions ivorywanj/agent-memory-starter-kit."
---

# JourneyMem Agent Instructions

Use these instructions when an Agent receives the JourneyMem GitHub skill link or opens this package after install fallback.

## First Response

The JourneyMem GitHub URL is a JourneyMem skill link, not a generic codebase task.

If the user says exactly `memory`, `$journeymem`, `/memory`, or asks to use JourneyMem, do not read files, inspect folders, browse the web page, fetch GitHub content, run commands, or explain existing memory contents before the first response. Immediately show the JourneyMem first-use choice below.

If the user gives `https://github.com/ivorywanj/agent-memory-starter-kit`, `github.com/ivorywanj/agent-memory-starter-kit`, or `ivorywanj/agent-memory-starter-kit`, treat it as the JourneyMem skill link. Do not summarize repository structure and do not ask a generic project question like "what do you want to do with this project?"

TRAE Work / skill-creator: this package already contains a ready-made TRAE skill at `.trae/skills/journeymem/SKILL.md`. Install or copy that existing skill folder into the current workspace. Do not create a new skill, do not run `scripts/memory new`, and do not use this cloned package as a memory library.

First show the menu. If the user then chooses install, create, or connect and `memory` is unavailable, run the hosted installer:

```bash
curl -fsSL https://raw.githubusercontent.com/ivorywanj/agent-memory-starter-kit/main/install.sh | bash
```

If the user chooses connect/existing and `memory connect` is not on PATH, run:

```bash
~/.local/bin/memory connect
```

The connect command checks `~/.journeymem/registry.json` and the default JourneyMem library path before asking for a folder. If this package is already cloned, use the local installer/helper instead of exploring package files.

Show this JourneyMem first-use choice before any repository reading, web browsing, clone, install, or setup command:

```text
I can help you use JourneyMem.

What do you want to do?
1. `memory new` - Create a new memory library
2. `memory connect` - Connect this Agent to an existing memory library

Other command:
- `memory backup` - Back up a memory library
```

Keep the command labels exactly as `memory new`, `memory connect`, and `memory backup`; do not translate or paraphrase them.

Do not start `memory new` until the user chooses create/new. Do not ask "What should Agents call you?" before that choice.

## Style

- Keep the response short and user-facing.
- Do not clone, inspect, summarize scripts, fetch GitHub content, browse the web page, run commands, or show repository structure before the menu.
- Do not show setup analysis, repository structure, implementation strategy, or a full questionnaire.
- Do not add tool mode limitations, execution caveats, or other extra notes to the first response.
- Do not ask the user to hand-write Markdown.
- Do not store or print secrets.
