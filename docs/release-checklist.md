# Release Checklist

Use this checklist before publishing a public release.

## From Private Source

```bash
cd "/path/to/private-agent-memory"
PYTHONDONTWRITEBYTECODE=1 python3 tests/test_memory_tools.py
python3 scripts/memory_guard.py
python3 scripts/export_public_package.py --output public-export --force --preserve-git
```

## Public Package Checks

```bash
cd public-export
python3 tests/test_public_package.py
python3 scripts/memory_guard.py
python3 scripts/public_release_check.py
git diff --check
```

## Fresh Clone Check

```bash
git clone https://github.com/ivorywanj/agent-memory-starter-kit.git /tmp/agent-memory-starter-kit-fresh
cd /tmp/agent-memory-starter-kit-fresh
python3 tests/test_public_package.py
python3 scripts/memory_guard.py
python3 scripts/public_release_check.py
```

## Publish

Only tag a release after all checks pass.
