# memory connect

Use this workflow when the user wants the current Agent to use an existing memory library.

## User Experience

Do not re-ask personal profile, preference, or project onboarding questions.

Start with:

```text
I will connect this Agent to your existing memory library.

If this is the same computer, no import is needed.

Do you already have a memory library on this computer?
```

1. Ask whether the user already has a memory library on this computer.
2. Try to detect the current Agent automatically.
3. A confident local memory library candidate must contain `AGENTS.md`, `ONBOARDING.md`, `memory/hot/USER.md`, and `memory/hot/MEMORY.md`.
4. Detection order: check the installed `memory` helper's configured path if available, then the current workspace connection file, then explicit helper/workspace paths. Do not broadly scan unrelated user folders.
5. If exactly one confident local candidate is found, connect automatically.
6. If no candidate or multiple candidates are found, ask the user for the memory library folder path.
7. If no local memory library exists, ask for a memory backup file or memory library folder from another computer, or guide the user to `memory new`.
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
- The first response asks whether the user already has a memory library on this computer.
- Confident local detection requires `AGENTS.md`, `ONBOARDING.md`, `memory/hot/USER.md`, and `memory/hot/MEMORY.md`.
- Response guides users without local memory to provide a memory backup file, a memory library folder from another computer, or create a new memory library.
- Response does not describe migration or copying memory into the Agent workspace.
- User profile, project facts, hot memory, history, observed memory, audit records, and secrets are not copied into the target workspace.
- The target Agent can read the startup path from the shared memory library.
