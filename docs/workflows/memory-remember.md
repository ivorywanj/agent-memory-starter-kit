---
name: memory-remember
description: Capture explicit session observations into short-term observed memory. Trigger with /memory-remember.
---

# /memory-remember

Purpose: capture useful session observations without writing source-of-truth files.

This is the first step of the product loop:

```text
remember -> recall -> improve -> forget
```

## Run

```bash
python3 scripts/memory_runtime.py remember --session-id <session> --text "<plain-language observation>"
```

For user corrections, prefer:

```bash
python3 scripts/memory_runtime.py remember --session-id <session> --source-type user_correction --text "<correction>"
```

## Capture

Capture only:

- explicit user corrections
- explicit user preferences that will recur
- file facts
- tool-result summaries
- repeatable workflow failures

Discard:

- Agent guesses
- one-off wording choices
- broad personality guesses
- raw conversation dumps
- unsafe text blocked by `scripts/memory_guard.py`

## Rules

- Write only to internal `memory/runtime/session_cache/`.
- Do not write source-of-truth files.
- Do not expose `memory/inbox/` as a user todo box.
- Every observed memory needs `source_event`, `first_seen_at`, `type`, and `status`.
- Fake or real secrets must be blocked and not printed. Report them only with redacted placeholders, not realistic secret-shaped examples.

## Output

Return a short status:

```text
Observed:
- <memory_id>: <summary>

Discarded:
- <reason>

Safety blocked:
- <kind>
```
