# Contributing

Thanks for improving JourneyMem.

## Development Checks

Run these before opening a pull request:

```bash
python3 tests/test_public_package.py
python3 scripts/memory_guard.py
python3 scripts/public_release_check.py
```

## Contribution Rules

- Keep v1 as CLI + Markdown. Do not add a server, vector database, graph database, or hosted backend without a design proposal.
- Do not commit private runtime files, raw benchmark runs, real sessions, history indexes, hot-memory drafts, observed memory, promotions, `.env*`, product source code, media assets, or generated caches.
- Do not add real secrets or secret-shaped examples. Use redacted placeholders such as `<redacted api key>`.
- Public docs and fixtures must use fake users, fake projects, fake paths, and fake examples.
