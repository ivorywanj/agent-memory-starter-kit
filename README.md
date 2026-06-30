# Agent Memory Starter Kit

Local-first memory runtime for coding agents.

Agent Memory Starter Kit gives Codex, Claude Code, Cursor, and other coding agents a small Markdown runtime they can read, update, validate, and hand off without asking users to maintain memory files manually.

## Why This Exists

Most agent memory setups become either too heavy to load or too invisible to trust. This starter kit keeps memory understandable:

- Markdown is the source of truth.
- Short-term session cache captures observations.
- Agents improve long-term memory after safety and routing checks.
- Users correct outcomes in plain language instead of editing files.

The core loop:

```text
init -> remember -> recall -> improve -> forget
```

There is no background service, vector database, hosted backend, or web UI in v1.

## Quickstart

Clone and initialize a memory runtime:

```bash
git clone https://github.com/ivorywanj/agent-memory-starter-kit.git
cd agent-memory-starter-kit
scripts/memory --root ./my-agent-memory init --answers templates/public/answers.example.json
```

Run the public checks:

```bash
python3 tests/test_public_package.py
python3 scripts/memory_guard.py
python3 scripts/public_release_check.py
```

The CLI creates a working starter runtime. The user does not hand-write Markdown.

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

| Step | What it does |
|---|---|
| `init` | Creates the starter Markdown runtime from answers. |
| `remember` | Captures explicit facts, corrections, and tool/file evidence into session cache. |
| `recall --context-only` | Returns evidence with source and authority tags before generating an answer. |
| `improve` | Promotes, modifies, deprecates, rejects, or discards observed memory after safety and routing gates. |
| `forget` | Handles corrections. Default is deprecate with rollback; permanent delete requires explicit wording. |

Example:

```bash
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
