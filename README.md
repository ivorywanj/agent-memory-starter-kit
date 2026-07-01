# Agent Memory Starter Kit

Local-first memory library for coding agents.

Agent Memory Starter Kit helps Codex, Claude Code, Cursor, and other Agents that can read project files learn a new user quickly, connect several Agents to the same memory, and keep everything in plain files. Users do not edit memory files by hand; the Agent asks guided questions and runs the setup steps.

## Quickstart

Clone the starter kit:

```bash
git clone https://github.com/ivorywanj/agent-memory-starter-kit.git
cd agent-memory-starter-kit
```

Open Codex, Claude Code, Cursor, or another Agent that can read project files.

Install the Agent shortcuts into a project workspace:

```bash
scripts/memory install --agent all --workspace ./your-project
```

This installs command helpers for Codex, Claude Code, Cursor, and generic file-reading Agents. Native slash menus vary by Agent. If `/memory` still does not appear, ask the Agent to read the installed helper file and run the matching command.

If your Agent recognizes `/memory`, send:

```text
/memory
```

If `/memory` does not appear in your Agent UI yet, ask the Agent to run:

```bash
scripts/memory
```

The menu should show four quick entries:

```text
1. /memory - Show this menu
2. /memory new - Create a memory library
3. /memory connect - Connect this Agent
4. /memory backup - Back up a memory library
```

You can also go directly:

```text
/memory new
/memory connect
/memory backup
```

The Agent will ask one short question at a time, offer examples, and run the matching setup step:

```bash
scripts/memory new
scripts/memory connect
scripts/memory backup
```

For first-time setup, the Agent should not ask where to store the files. It creates a default memory library and helps you correct the summary afterward.

For connecting another Agent, the Agent should already know which tool you are using. It only asks you to choose Codex, Claude Code, Cursor, or Generic if it cannot identify the current Agent.

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

The onboarding flow starts by identifying the user's intent:

```text
Are you new to Agent Memory, or do you want to connect this Agent to an existing memory library?
```

If the user is new, ask one question at a time:

1. What should Agents call you?
2. What language should Agents use by default?
3. What kind of work do you do?
4. What are your current 1-3 projects? If a project has a workspace folder, include it.
5. How should Agents communicate with you?
6. Which actions require confirmation?
7. What must never be stored in memory?

Project workspaces are routing hints, not ingestion permission. The setup records the folder pointer and whether it existed at setup time, but it does not read, scan, index, or import the folder.

## Productized Flow Metrics

See `docs/productized-user-flow.md` for the user-flow design and measurable acceptance criteria. The core gates are:

- `/memory` or `scripts/memory` shows exactly four quick entries.
- `scripts/memory install --agent all` writes Codex, Claude Code, Cursor, and generic command helpers.
- `/memory new` asks no more than seven setup questions, plus an optional project-folder follow-up.
- `/memory connect` does not re-ask profile questions and auto-detects the current Agent when possible.
- `/memory backup` creates a zip and excludes unsafe or temporary files.
- User-facing first screens contain zero blocked internal terms.

## Sharing Across Agents

Use `/memory connect` when Codex, Claude Code, Cursor, or another Agent should use the same memory library.

The command writes a small connection file into the target Agent workspace. It points back to the same memory library instead of copying user profile, project facts, hot memory, history, or audit records into each Agent.

Default connection targets:

| Agent | Target |
|---|---|
| Codex | `AGENTS.md` |
| Claude Code | `CLAUDE.md` |
| Cursor | `.cursor/rules/agent-memory.mdc` |
| Generic | `AGENT_MEMORY.md` |

## Backup

Use `/memory backup` to create a zip backup.

The backup excludes secrets, temporary dialogue data, search indexes, raw runs, generated drafts, and local database files.

## Developer Commands

The user-facing commands are `/memory new`, `/memory connect`, and `/memory backup`. The lower-level CLI also keeps these developer commands for tests and automation:

```text
init -> remember -> recall -> improve -> forget
```

Examples:

```bash
scripts/memory --root ./my-agent-memory init --answers templates/public/answers.example.json
scripts/memory --root ./my-agent-memory install --agent all --workspace ./my-project
scripts/memory --root ./my-agent-memory share --agent codex --workspace ./my-project
scripts/memory --root ./my-agent-memory remember --session-id demo --text "以后测试通过必须验证真实行为，不能只检查文件存在。"
scripts/memory --root ./my-agent-memory improve --session-id demo
scripts/memory --root ./my-agent-memory recall --query "测试 真实行为" --context-only
scripts/memory --root ./my-agent-memory forget --instruction "删除第 1 条"
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
