# Agent Sharing

Use `memory connect` when Codex, TRAE Work, Claude Code, Cursor, or another local-file-reading Agent should use the same memory library on the same machine.

## Goal

Different Agents should use the same memory library instead of each keeping a private copy of user preferences, project facts, and lessons.

```text
shared memory library
-> connection file per Agent workspace
-> same startup path
-> same remember / recall / improve / forget loop
```

## Commands

User-facing flow:

```text
memory connect
```

Install shortcut helpers first when `memory` is not available:

```bash
scripts/memory --root ./my-journeymem install --agent all --workspace ./my-project
```

Agent command:

```bash
scripts/memory --root ./my-journeymem connect --agent codex --workspace ./my-project
scripts/memory --root ./my-journeymem connect --agent claude --workspace ./my-project
scripts/memory --root ./my-journeymem connect --agent cursor --workspace ./my-project
scripts/memory --root ./my-journeymem connect --agent generic --workspace ./my-project
```

Default targets:

| Agent | Target |
|---|---|
| `codex` | `AGENTS.md` |
| `claude` | `CLAUDE.md` |
| `cursor` | `.cursor/rules/journeymem.mdc` |
| `generic` | `JOURNEYMEM.md` |

Use `--target <file>` for an explicit target, `--append` for existing files, and `--print` for preview-only output.

## Safety

Connection files are pointer-only. They must not include user profile details, project facts, hot memory content, observed memory, raw history, audit records, secrets, or customer data.

Markdown files in the shared memory library remain the final record.
