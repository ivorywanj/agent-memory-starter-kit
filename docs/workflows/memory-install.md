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
| Codex | user-level Agent Memory skill |
| Claude Code | project command files |
| Cursor | project rule helper |
| Generic Agent | project command helper |

Native slash menus vary by Agent. If `/memory` still does not appear, ask the Agent to read the installed helper file and run the matching command.

## Pass Criteria

- Codex, Claude Code, Cursor, and generic helper files are written.
- Duplicate install blocks unless `--force` is used.
- Helper files include `/memory`, `/memory new`, `/memory connect`, and `/memory backup`.
- Helper files do not copy profile details, project facts, history, or secrets.
