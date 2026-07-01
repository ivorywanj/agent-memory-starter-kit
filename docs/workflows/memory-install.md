# /memory install

Use this workflow when the user wants `/memory`, `/memory new`, `/memory connect`, and `/memory backup` to work as Agent shortcuts.

## User Experience

The user should not need to understand where each Agent stores commands.

Run one install command and report what was installed:

```bash
scripts/memory install --agent all --workspace ./my-project
```

## What Gets Installed

| Agent | Helper file |
|---|---|
| Codex | `memory` shell shortcut, local plugin package, and user-level Agent Memory skill |
| Claude Code | project command files |
| Cursor | project rule helper |
| Generic Agent | project command helper |

Native slash menus vary by Agent. In Codex, use the text shortcuts `memory`, `memory new`, `memory connect`, and `memory backup`; current Codex versions may not show custom plugin commands in the slash picker. For slash-capable Agents, `/memory`, `/memory new`, `/memory connect`, and `/memory backup` remain the intended shortcuts.

Best-effort alias command files such as `/memory-new`, `/memory-connect`, and `/memory-backup` are also installed for Agents that expose plugin commands.

## Pass Criteria

- Codex local plugin package, Claude Code command files, Cursor rule, and generic helper files are written.
- Codex `memory` shell shortcut is executable.
- Duplicate install blocks unless `--force` is used.
- Helper files include `/memory`, `/memory new`, `/memory connect`, and `/memory backup`.
- Helper files do not copy profile details, project facts, history, or secrets.
