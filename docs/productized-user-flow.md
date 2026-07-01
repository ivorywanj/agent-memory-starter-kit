# Productized User Flow

This document defines the simple user flow and measurable acceptance criteria for Agent Memory Starter Kit.

## Goal

Users should be able to open the menu, start, connect, and back up memory through four quick entries:

```text
/memory
/memory new
/memory connect
/memory backup
```

The Agent handles setup steps. The user answers guided questions and corrects the summary if needed.

If the Agent UI does not recognize `/memory`, the Agent should run `scripts/memory` and show the same four entries.

Before that, users can install Agent command helpers once:

```bash
scripts/memory install --agent all --workspace ./your-project
```

## User Flow

### 0. Install Agent Shortcuts

Entry:

```text
scripts/memory install --agent all --workspace ./your-project
```

Flow:

1. Write a Codex local plugin package, command files, skill helper, and config block.
2. Write Claude Code command files.
3. Write a Cursor rule helper.
4. Write a generic Agent command helper.
5. Report where each helper was installed.

### 1. New User Setup

Entry:

```text
/memory new
```

Flow:

1. Ask what the Agent should call the user.
2. Ask default language.
3. Ask work type.
4. Ask current projects and optionally attach a work folder.
5. Ask communication preference.
6. Ask which actions require confirmation.
7. Ask what must never be stored.
8. Create the memory library.
9. Show a short summary and correction syntax.

### 2. Connect This Agent

Entry:

```text
/memory connect
```

Flow:

1. Do not ask profile or preference questions again.
2. Detect the current Agent when possible.
3. Locate an existing memory library or ask for a folder/backup zip only if needed.
4. Write a small connection file into the Agent workspace.
5. Report what was connected.

### 3. Backup

Entry:

```text
/memory backup
```

Flow:

1. Run safety scan.
2. Create a zip backup.
3. Exclude unsafe or temporary files.
4. Report the zip path.

## Quantitative Acceptance Criteria

| ID | Area | Pass Criteria | Automated Evidence |
|---|---|---|---|
| T21 | Quick entry | `/memory` or `scripts/memory` shows exactly 4 quick entries. Blocked internal terms on the first screen = 0. | `tests/test_public_package.py::test_memory_shortcuts_and_backup_zip` |
| T22 | Shortcut install | `scripts/memory install --agent all` writes Codex, Claude Code, Cursor, and generic helpers. Duplicate install blocks unless `--force` is used. | `tests/test_public_package.py::test_memory_install_writes_agent_shortcuts` |
| T23 | New setup | Setup creates required files, asks no storage-location question, requires no manual memory-file editing, and blocks secret-shaped answers. | `tests/test_public_package.py::test_init_creates_public_runtime` and `test_init_blocks_secret_shaped_answers` |
| T24 | Cross-Agent connect | Agent detection succeeds when an Agent marker is provided. Connection file is created. Copied profile/project facts/secrets = 0. | `tests/test_public_package.py::test_init_creates_public_runtime` |
| T25 | Backup | Zip is created. Excluded categories are absent from zip: `.env*`, temporary dialogue data, search indexes, drafts, and local database files. | `tests/test_public_package.py::test_memory_shortcuts_and_backup_zip` |
| T26 | Low-terminology first screen | README first screen blocked internal terms = 0. Required user shortcuts are present. | `scripts/public_release_check.py` |
| T27 | Public package release gate | Public fixture tests, memory guard, release check, and diff check all pass. | CI and local validation commands |

## Local Validation

```bash
python3 tests/test_public_package.py
python3 scripts/memory_guard.py
python3 scripts/public_release_check.py
git diff --check
```

Development is incomplete if any criterion above fails.
