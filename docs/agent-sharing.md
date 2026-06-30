# Agent Sharing

Use `memory share` when Codex, Claude Code, Cursor, or another local-file-reading Agent should use the same memory runtime.

## Goal

Different Agents should share one source of truth instead of each keeping a private copy of user preferences, project facts, and lessons.

```text
shared memory root
-> pointer-only bridge file per Agent workspace
-> same startup path
-> same remember / recall / improve / forget loop
```

## Commands

```bash
scripts/memory --root ./my-agent-memory share --agent codex --workspace ./my-project
scripts/memory --root ./my-agent-memory share --agent claude --workspace ./my-project
scripts/memory --root ./my-agent-memory share --agent cursor --workspace ./my-project
scripts/memory --root ./my-agent-memory share --agent generic --workspace ./my-project
```

Default targets:

| Agent | Target |
|---|---|
| `codex` | `AGENTS.md` |
| `claude` | `CLAUDE.md` |
| `cursor` | `.cursor/rules/agent-memory.mdc` |
| `generic` | `AGENT_MEMORY.md` |

Use `--target <file>` for an explicit target, `--append` for existing files, and `--print` for preview-only output.

## Safety

Bridge files are pointer-only. They must not include user profile details, project facts, hot memory content, session cache, raw history, deprecated audit, secrets, or customer data.

The shared Markdown runtime remains the source of truth.
