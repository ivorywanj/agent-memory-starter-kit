---
name: memory-forget
description: Apply user corrections by modifying, deprecating, or permanently deleting memory. Trigger with /memory-forget.
---

# /memory-forget

Purpose: let the user correct memory without making them manage candidate files.

## Run

Default behavior is deprecate with rollback:

```bash
python3 scripts/memory_runtime.py forget --instruction "<correction>"
```

Physical deletion requires explicit permanent deletion:

```bash
python3 scripts/memory_runtime.py forget --memory-id <memory-id> --permanent
```

## Recognize

Treat these as correction intents:

- `这条不要记`
- `删除第 2 条`
- `第 1 条改成...`
- `永久删除第 3 条`
- `这条记错了`

## Rules

- Default to `deprecated`, not physical deletion.
- Deprecated memory is blocked from truth recall.
- Write rollback audit for every deprecate or forget action.
- Modify when the user provides a corrected replacement.
- Permanently delete only when the user explicitly asks for permanent deletion.

## Output

```text
Memory corrected

Deprecated:
1. ...

Rollback:
- audit entry written
```
