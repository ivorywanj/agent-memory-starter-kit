# memory install

Use this workflow when the user wants `memory`, `memory new`, `memory connect`, and `memory backup` to work as Agent shortcuts.

## User Experience

The user should not need to understand where each Agent stores commands.

Run one install command and report what was installed:

```bash
scripts/memory install --agent all --workspace ./my-project
```

## What Gets Installed

| Agent | Helper file |
|---|---|
| Shell | shared executable `memory` command |
| Codex | local plugin package and user-level JourneyMem skill |
| Claude Code | project command files |
| Cursor | project rule helper |
| TRAE Work | global skill, project skill, project rule helper |
| Generic Agent | project command helper |

Native slash menus vary by Agent. Use the text shortcuts `memory`, `memory new`, `memory connect`, and `memory backup` as the stable entries. Slash-capable Agents may also support `/memory`, `/memory new`, `/memory connect`, and `/memory backup`.

Best-effort alias command files such as `/memory-new`, `/memory-connect`, and `/memory-backup` are also installed for Agents that expose plugin commands.

## Pass Criteria

- Shared `memory` shell shortcut is executable.
- Codex local plugin package, Claude Code command files, Cursor rule, TRAE Work global/project skills, TRAE Work rule, and generic helper files are written.
- Duplicate install blocks unless `--force` is used.
- Helper files include `memory`, `memory new`, `memory connect`, and `memory backup`.
- Helper files do not copy profile details, project facts, history, or secrets.
