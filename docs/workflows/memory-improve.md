---
name: memory-improve
description: Automatically promote, modify, deprecate, discard, or reject observed memory. Trigger with /memory-improve.
---

# /memory-improve

Purpose: end a task by improving long-term memory automatically. The user should not review candidate memories one by one; they only correct wrong outcomes.

## Run

```bash
python3 scripts/memory_runtime.py improve --session-id <session>
```

Refresh hot-memory draft when source files changed:

```bash
python3 scripts/memory_runtime.py improve --session-id <session> --refresh-hot-draft
```

## Gates

Only five gates matter:

```text
Safe
Explicit
Reusable
Routed
Fresh
```

Actions:

- all gates pass -> promote
- valuable but too broad -> narrow then promote
- route unclear -> keep as shadow/observed
- Fresh fails -> modify, deprecate, or forget
- Safe fails -> reject and do not save
- Explicit fails -> discard

## Growth Control

`/memory-improve` must also clean memory:

- merge duplicate memories
- deprecate stale paths
- mark stale commands
- modify or deprecate corrected old memory
- TTL-clean old shadow/observed memory after 30 days
- keep `memory/hot/USER.md <= 1800` chars
- keep `memory/hot/MEMORY.md <= 2400` chars

## Rules

- Run `scripts/memory_guard.py` before every source-of-truth write.
- Write audit entries for promote, modify, deprecate, forget, reject, discard, and merge.
- Notify the user with at most 8 changed items.
- Do not save raw conversation text, secrets, or secret-shaped examples. Use redacted placeholders in summaries and audit explanations.

## Output

```text
Memory updated

Promoted:
1. ...

Modified:
1. ...

Deprecated:
1. ...

Safety blocked: 0
```
