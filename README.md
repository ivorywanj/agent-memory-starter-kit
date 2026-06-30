# Agent Memory Starter Kit

A lightweight local-first memory runtime for coding agents.

The starter kit gives an agent a simple, auditable memory loop:

```text
memory init -> remember -> recall -> improve -> forget
```

It uses Markdown files as source of truth and local JSONL files as short-term runtime state. There is no background service, vector database, hosted backend, or web UI in v1.

## Quickstart

Create a starter runtime:

```bash
scripts/memory --root ./my-agent-memory init --answers templates/public/answers.example.json
```

The user does not hand-write Markdown. The CLI creates:

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
memory/history/README.md
memory/inbox/README.md
memory/promotions/README.md
```

## First Agent Prompt

```text
Please read AGENTS.md, ONBOARDING.md, memory/hot/USER.md, and memory/hot/MEMORY.md first.
Do not read the full runtime by default.

Then answer:
1. Who is the user?
2. What is the source-of-truth order?
3. How do hot memory, history evidence, session cache, deprecated audit, and Markdown files differ?
4. What must never be stored or printed?
5. Which task-specific files would you read next only if needed?
```

## Memory Loop

- `remember` captures explicit facts, corrections, and tool/file evidence into session cache.
- `recall --context-only` returns evidence with source and authority tags.
- `improve` promotes, modifies, deprecates, rejects, or discards observed memory after safety and routing gates.
- `forget` handles corrections. Default is deprecate with rollback; permanent delete requires explicit wording.

Example:

```bash
scripts/memory --root ./my-agent-memory remember --session-id demo --text "以后测试通过必须验证真实行为，不能只检查文件存在。"
scripts/memory --root ./my-agent-memory improve --session-id demo
scripts/memory --root ./my-agent-memory recall --query "测试 真实行为" --context-only
scripts/memory --root ./my-agent-memory forget --instruction "删除第 1 条"
```

## Safety

The runtime refuses secret-shaped content before it writes generated memory files. Do not store API keys, tokens, webhook URLs, database URLs, private keys, raw sessions, customer data, account data, cookies, or passwords.

Run:

```bash
python3 scripts/memory_guard.py
python3 tests/test_public_package.py
```

## Publish Boundary

This public package contains only anonymous templates, fixture tests, CLI scripts, and public documentation. It intentionally excludes private runtime files, raw benchmark runs, history indexes, session caches, hot-memory drafts, inbox entries, promotions, product source code, and user-specific memory.
