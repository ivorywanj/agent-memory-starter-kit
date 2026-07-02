# JourneyMem

A local memory library for AI agents.

JourneyMem helps Codex, Claude Code, Cursor, TRAE Work, and other Agents that can read project files learn a new user quickly, connect several Agents to the same memory, and keep everything in plain files. Users do not edit memory files by hand; the Agent asks guided questions and runs the setup steps.

## Quickstart

For most users, install JourneyMem once from Terminal:

```bash
curl -fsSL https://raw.githubusercontent.com/ivorywanj/agent-memory-starter-kit/main/install.sh | bash
```

Then start immediately:

```bash
~/.local/bin/memory
```

If your terminal or Agent already knows `~/.local/bin`, you can type:

```text
memory
```

Optional Start Page:

```text
https://ivorywanj.github.io/agent-memory-starter-kit/
```

The Start Page has copy buttons for Agent-specific prompts. Users do not write prompts by hand. If the page is unavailable, use the Terminal install command above.

The installer creates `~/.journeymem/`, installs the `memory` command, and writes Agent helper files. It detects the current Agent when possible; when it cannot detect one, it installs helpers for all supported Agents. It does not create a personal memory library until the user chooses `memory new`, and it does not import workspace files.

Open Codex, TRAE Work, Claude Code, Cursor, or another Agent that can read project files, then type `memory`.

If your Agent supports explicit skill references, you can also use the installed local skill after install:

```text
[$journeymem](<generated-local-skill-path>/SKILL.md)
```

The Agent should show:

```text
What do you want to do?
1. memory new - Create a memory library
2. memory connect - Connect this Agent to an existing memory library

Other command:
- memory backup - Back up a memory library
```

Do not paste only the GitHub URL into an Agent as the normal quickstart. Many Agents treat a bare GitHub URL like a generic code repo to clone and inspect. JourneyMem's GitHub URL is an install source fallback, not the primary Agent entry.

Manual terminal fallback only:

```bash
git clone https://github.com/ivorywanj/agent-memory-starter-kit.git
cd agent-memory-starter-kit
./install.sh
```

You can then type:

```text
memory new
memory connect
```

Backup is a separate command:

```text
memory backup
```

The installer writes a real `memory` shell command into `~/.local/bin` so Agents can run `memory`, `memory new`, `memory connect`, and `memory backup` from any project. It also detects the current Agent when possible and writes helper files for Codex, Claude Code, Cursor, TRAE Work, or generic file-reading Agents.

Slash-capable Agents may also support `/memory`, `/memory new`, `/memory connect`, and `/memory backup`, but the stable entry is `memory`.

If `memory` is not found in the current shell, run `~/.local/bin/memory` or restart the terminal / Agent so the PATH update is picked up. Do not rerun setup just because the short command is not on PATH yet.

Then use these troubleshooting commands only when the Agent prompt flow is not available:

```bash
./scripts/memory
./scripts/memory new
./scripts/memory connect
./scripts/memory backup
```

For first-time setup, the Agent should not explain setup internals or ask where to store the files. It should ask one question at a time and only show the next useful question.

For connecting another Agent, the Agent should already know which tool you are using. It only asks you to choose Codex, Claude Code, Cursor, TRAE Work, or Generic if it cannot identify the current Agent.

## What It Creates

The first setup creates a compact local memory library:

```text
AGENTS.md
ONBOARDING.md
CROSS_AGENT.md
memory/hot/USER.md
memory/hot/MEMORY.md
agent/CURRENT_STATE.md
agent/DECISIONS.md
tasks/lessons.md
memory/projects/projects.md
memory/projects/projects.json
```

The user flow stays simple:

```text
create -> connect -> remember useful corrections -> improve automatically -> backup
```

There is no background service, hosted backend, vector database, graph database, or web UI in v1.

## First-Run Wizard

The onboarding flow starts by identifying the user's first-use intent:

```text
Do you want to create a new memory library, or connect this Agent to an existing memory library?
```

Install-source fallback rule: if the JourneyMem GitHub URL or a manual clone appears first, the Agent must install or activate JourneyMem before any repo exploration, then ask this two-choice question. It must not start `memory new` automatically.

If the user is new, the first visible setup response should be:

```text
I will help you create your memory library.

First question:
What should Agents call you?
For example: Alex, Sam, or your real name.
```

Then ask one next question after each user answer. Do not show the full questionnaire upfront.
Do not ask where to store the memory library during `memory new`; use the default location.

Project workspaces are routing hints, not ingestion permission. The setup records the folder pointer and whether it existed at setup time, but it does not read, scan, index, or import the folder.

## Productized Flow Metrics

See `docs/productized-user-flow.md` for the user-flow design and measurable acceptance criteria. The core gates are:

- `memory` shows exactly two first-use choices: create a new memory library or connect this Agent to an existing memory library.
- A JourneyMem GitHub URL or manual clone does not trigger repo exploration or `memory new`; the Agent treats it as an install source and asks the two-choice first-use question after install/activation.
- `scripts/memory install --agent all` writes a shared `memory` shell command plus Codex, Claude Code, Cursor, TRAE Work, and generic command helpers.
- Codex install writes a local plugin package and enables it in `~/.codex/config.toml`.
- `memory new` asks no more than seven setup questions, plus an optional project-folder follow-up.
- `memory connect` starts by asking whether a local memory library already exists, then connects by pointer without import when possible.
- `memory backup` asks where to save a zip backup, allows the default backup folder, and excludes unsafe or temporary files.
- User-facing first screens contain zero blocked internal terms.

## Sharing Across Agents

Use `memory connect` when Codex, TRAE Work, Claude Code, Cursor, or another Agent should use the same memory library on the same machine.

The command writes a small connection file into the target Agent workspace. It points back to the same memory library instead of copying user profile, project facts, hot memory, history, or audit records into each Agent.

For same-machine sharing, no import is needed. The Agent should not describe this as migration or copying.

The Agent first runs the local `memory connect` flow. It checks `~/.journeymem/registry.json` and the default JourneyMem library path before asking for any folder path. It only treats a folder as a confident match when it contains `AGENTS.md`, `ONBOARDING.md`, `memory/hot/USER.md`, and `memory/hot/MEMORY.md`. It should not broadly scan unrelated user folders. If no local memory library exists, provide a memory backup file from another computer or create a new memory library.

Default connection targets:

| Agent | Target |
|---|---|
| Codex | `AGENTS.md` |
| Claude Code | `CLAUDE.md` |
| Cursor | `.cursor/rules/journeymem.mdc` |
| Generic | `JOURNEYMEM.md` |

## Backup

Use `memory backup` to create a zip backup.

The Agent asks where to save the zip. You can also say "use the default backup folder".

The backup excludes secrets, temporary dialogue data, search indexes, raw runs, generated drafts, and local database files.

Backup does not connect, import, restore, switch, or initialize a memory library.

## Developer Commands

The user-facing commands are `memory new`, `memory connect`, and `memory backup`. The lower-level CLI also keeps these developer commands for tests, automation, and fallback troubleshooting:

```text
init -> remember -> recall -> improve -> forget
```

Examples:

```bash
scripts/memory --root ./my-journeymem init --answers templates/public/answers.example.json
scripts/memory --root ./my-journeymem install --agent all --workspace ./my-project
scripts/memory --root ./my-journeymem share --agent codex --workspace ./my-project
scripts/memory --root ./my-journeymem remember --session-id demo --text "以后测试通过必须验证真实行为，不能只检查文件存在。"
scripts/memory --root ./my-journeymem improve --session-id demo
scripts/memory --root ./my-journeymem recall --query "测试 真实行为" --context-only
scripts/memory --root ./my-journeymem forget --instruction "删除第 1 条"
```

## Safety

The runtime refuses secret-shaped content before it writes generated memory files. Do not store API keys, tokens, webhook URLs, database URLs, private keys, raw sessions, customer data, account data, cookies, or passwords.

Safety checks:

```bash
python3 scripts/memory_guard.py
python3 scripts/public_release_check.py
```

## Validation

GitHub Actions runs the public fixture tests, memory guard, and public release check on every push and pull request.

Local validation:

```bash
python3 tests/test_public_package.py
python3 scripts/memory_guard.py
python3 scripts/public_release_check.py
```

## Benchmark Evidence

The private development runtime passed a 60-row real-model benchmark before this public package was extracted. The public repo includes only the anonymized summary in `docs/benchmark-evidence.md`, not raw prompts, logs, private paths, or model outputs.

Final fused benchmark summary:

| Metric | Result |
|---|---:|
| Background hit rate | 94% |
| Preference compliance | 99% |
| Safety violations | 0 |
| Source-of-truth accuracy | 100% |
| Tool command validity | 100% |
| Average score | 4.8 |

## V1 Limits

- CLI + Markdown only.
- Single-user local runtime.
- No hosted backend, auth layer, graph database, vector database, or web UI.
- Public package contains anonymous templates and fixture tests, not private runtime data.
- History, session cache, and deprecated memory are evidence or audit layers; Markdown source-of-truth files win conflicts.

## Publish Boundary

This public package contains only anonymous templates, fixture tests, CLI scripts, and public documentation. It intentionally excludes private runtime files, raw benchmark runs, history indexes, session caches, hot-memory drafts, inbox entries, promotions, product source code, and user-specific memory.
