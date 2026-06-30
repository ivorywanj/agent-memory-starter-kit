---
name: memory-guard
description: Run the local memory safety scanner before committing, exporting, or promoting memory files. Trigger with /memory-guard.
---

# /memory-guard

Purpose: scan memory runtime files for secrets, hidden Unicode, database URLs, private keys, webhook URLs, and prompt-injection text.

## Run

```bash
python3 scripts/memory_guard.py
```

## Rules

- A blocking finding must be fixed or explicitly excluded before commit, export, or promotion.
- Do not paste secrets into chat when reporting findings.
- Do not paste secret-shaped examples either. Use `<redacted api key>`, `<redacted database url>`, `<redacted webhook url>`, or `<redacted token>` instead of realistic patterns.
- Generic words like `webhook` or `token` are not enough to fail; real URL/key patterns or unsafe hidden characters are.
- If a finding appears in a deliberately anonymous fixture, scan that fixture separately and explain that it is not part of default runtime scanning.

## Output

Return:

```text
Memory Guard
- Result:
- Findings:
- Files needing review:
- Next safe action:
```
