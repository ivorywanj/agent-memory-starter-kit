# Developer command: memory share

User-facing sharing should use `/memory connect`.

Use this lower-level command when the same memory library should be shared by Codex, Claude Code, Cursor, or another local-file-reading Agent.

## Command

```bash
scripts/memory --root ./my-agent-memory share --agent codex --workspace ./my-project
scripts/memory --root ./my-agent-memory share --agent claude --workspace ./my-project
scripts/memory --root ./my-agent-memory share --agent cursor --workspace ./my-project
```

Default pointer targets:

| Agent | Target |
|---|---|
| `codex` | `AGENTS.md` |
| `claude` | `CLAUDE.md` |
| `cursor` | `.cursor/rules/agent-memory.mdc` |
| `generic` | `AGENT_MEMORY.md` |

Use `--target <file>` for an explicit file path.

Use `--append` when the target file already exists and should keep its current content.

Use `--print` to preview the pointer text without writing files.

## Behavior

- Writes a small pointer file that points to the shared memory library.
- Does not copy user profile, project facts, hot memory, observed memory, history, or audit records into the target workspace.
- Refuses to overwrite an existing target unless `--force` or `--append` is explicit.
- Records created pointers in `memory/agents/registry.json`.

## Rule

There is one final record: the shared Markdown memory library. Agent-specific files are pointers only.
