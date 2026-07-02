# JourneyMem Agent Instructions

Use these instructions when an Agent opens this repository after install-source fallback or manual clone.

## First Response

The JourneyMem GitHub URL is an install source fallback, not a generic codebase task.

If the user says exactly `memory`, `$journeymem`, `/memory`, or asks to use JourneyMem, do not read files, inspect folders, or explain existing memory contents. Immediately show the JourneyMem first-use choice below.

If the user gives `https://github.com/ivorywanj/agent-memory-starter-kit`, do not summarize the repository structure and do not ask a generic project question like "what do you want to do with this project?"

If possible, install or activate JourneyMem first. If `memory` is unavailable, run the hosted installer:

```bash
curl -fsSL https://raw.githubusercontent.com/ivorywanj/agent-memory-starter-kit/main/install.sh | bash
```

If the user chooses connect/existing and `memory connect` is not on PATH, run:

```bash
~/.local/bin/memory connect
```

The connect command checks `~/.journeymem/registry.json` and the default JourneyMem library path before asking for a folder. If the repository is already cloned, use the local installer/helper instead of exploring the repo.

Instead, show this JourneyMem first-use choice:

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
- Do not clone, inspect, summarize scripts, or show repository structure before install/menu.
- Do not show setup analysis, repository structure, implementation strategy, or a full questionnaire.
- Do not add tool mode limitations, execution caveats, or other extra notes to the first response.
- Do not ask the user to hand-write Markdown.
- Do not store or print secrets.
