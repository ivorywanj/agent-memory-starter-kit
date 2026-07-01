# /memory connect

Use this workflow when the user wants the current Agent to use an existing memory library.

## User Experience

Do not re-ask personal profile, preference, or project onboarding questions.

1. Try to detect the current Agent automatically.
2. Try to find the existing memory library in the current folder or nearby default folder.
3. Ask for a folder or backup zip only when no memory library is found.
4. Ask for the target project folder only if it is not already the current workspace.
5. Use append mode when the target Agent file already exists, unless the user explicitly wants overwrite.

## Agent Command

```bash
scripts/memory connect --workspace ./my-project
```

If Agent detection fails:

```bash
scripts/memory connect --agent codex --workspace ./my-project
```

## Pass Criteria

- Connection file is pointer-only.
- User profile, project facts, hot memory, history, observed memory, audit records, and secrets are not copied into the target workspace.
- The target Agent can read the startup path from the shared memory library.
