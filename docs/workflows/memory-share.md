# /memory-share

Use this when the same memory runtime should be shared by Codex, Claude Code, Cursor, or another local-file-reading Agent.

## Command

```bash
scripts/memory --root ./my-agent-memory share --agent codex --workspace ./my-project
scripts/memory --root ./my-agent-memory share --agent claude --workspace ./my-project
scripts/memory --root ./my-agent-memory share --agent cursor --workspace ./my-project
```

Default bridge targets:

| Agent | Target |
|---|---|
| `codex` | `AGENTS.md` |
| `claude` | `CLAUDE.md` |
| `cursor` | `.cursor/rules/agent-memory.mdc` |
| `generic` | `AGENT_MEMORY.md` |

Use `--target <file>` for an explicit file path.

Use `--append` when the target file already exists and should keep its current content.

Use `--print` to preview the bridge without writing files.

## Behavior

- Writes a small bridge file that points to the shared memory root.
- Does not copy user profile, project facts, hot memory, session cache, history, or deprecated audit into the target workspace.
- Refuses to overwrite an existing target unless `--force` or `--append` is explicit.
- Records created bridges in `memory/agents/registry.json`.

## Rule

There is one source of truth: the shared Markdown runtime. Agent-specific files are pointers only.
