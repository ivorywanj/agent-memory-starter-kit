# memory connect

Use this workflow when the user wants the current Agent to use an existing memory library.

## User Experience

Do not re-ask personal profile, preference, or project onboarding questions.

Start with:

```text
I will connect this Agent to your existing memory library.

If this is the same computer, no import is needed.
```

1. Try to detect the current Agent automatically.
2. Check `~/.journeymem/registry.json` for an existing default memory library.
3. Check the default JourneyMem library path.
4. A confident local memory library candidate must contain `AGENTS.md`, `ONBOARDING.md`, `memory/hot/USER.md`, and `memory/hot/MEMORY.md`.
5. If exactly one confident local candidate is found, connect automatically.
6. If multiple candidates are found, show numbered choices.
7. If no local memory library exists, ask for a memory backup file from another computer or guide the user to `memory new`.
8. For same-machine sharing, connect to the existing local memory library. Do not import or duplicate memory content.
9. Ask for the target project folder only if it is not already the current workspace.
10. Use append mode when the target Agent file already exists, unless the user explicitly wants overwrite.

## Agent Command

```bash
memory connect --workspace ./my-project
```

If Agent detection fails:

```bash
memory connect --agent codex --workspace ./my-project
```

## Pass Criteria

- Connection file is pointer-only.
- Same-machine Agent sharing does not require import.
- The first response does not ask for a folder path when the registry has one valid default library.
- Confident local detection requires `AGENTS.md`, `ONBOARDING.md`, `memory/hot/USER.md`, and `memory/hot/MEMORY.md`.
- Response guides users without local memory to provide a memory backup file from another computer or create a new memory library.
- Response does not describe migration or copying memory into the Agent workspace.
- User profile, project facts, hot memory, history, observed memory, audit records, and secrets are not copied into the target workspace.
- The target Agent can read the startup path from the shared memory library.
