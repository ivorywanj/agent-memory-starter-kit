# Productized User Flow

This document defines the simple user flow and measurable acceptance criteria for JourneyMem.

## Goal

Users should be able to open the first-use menu and choose between creating a memory library or connecting this Agent to an existing memory library. Backup remains a separate command, not a first-use branch.

```text
memory
memory new
memory connect
memory backup
```

The Agent handles setup steps. The user answers guided questions and corrects the summary if needed.

Slash-capable Agents may also support `/memory`, but the stable entry is `memory`.

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

1. Write a shared executable `memory` shell shortcut.
2. Write a Codex local plugin package, command files, skill helper, and config block.
3. Write Claude Code command files.
4. Write a Cursor rule helper.
5. Write a TRAE Work rule helper and fallback prompt file.
6. Write a generic Agent command helper.
7. Report where each helper was installed.

### 1. New User Setup

Entry:

```text
memory new
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
memory connect
```

Flow:

1. Do not ask profile or preference questions again.
2. Ask whether the user already has a memory library on this computer.
3. Detect the current Agent when possible.
4. A confident local memory library candidate must contain `AGENTS.md`, `ONBOARDING.md`, `memory/hot/USER.md`, and `memory/hot/MEMORY.md`.
5. If exactly one confident local candidate exists, connect automatically.
6. If none or multiple exist, ask for the memory library folder path.
7. If no local memory library exists, ask for a memory backup file or memory library folder from another computer, or guide the user to `memory new`.
8. Write a small connection file into the Agent workspace.
9. Report what was connected.

### 3. Backup

Entry:

```text
memory backup
```

Flow:

1. Run safety scan.
2. Ask where to save the zip backup. The user can also say "use the default backup folder".
3. Create a zip backup.
4. Exclude unsafe or temporary files.
5. Report the zip path.

## Quantitative Acceptance Criteria

| ID | Area | Pass Criteria | Automated Evidence |
|---|---|---|---|
| T21 | Quick entry | `/memory` or `scripts/memory` shows exactly 2 first-use choices: create new or connect existing. Backup is available separately, not as a main first-use branch. Blocked internal terms on the first screen = 0. | `tests/test_public_package.py::test_memory_shortcuts_and_backup_zip` |
| T21a | GitHub install-source fallback | A JourneyMem GitHub URL or manual clone does not trigger repo exploration or `memory new`; the Agent treats it as an install source and asks the two-choice first-use question after install/activation. | `scripts/public_release_check.py` |
| T22 | Shortcut install | `scripts/memory install --agent all` writes Codex, Claude Code, Cursor, TRAE Work, and generic helpers. Duplicate install blocks unless `--force` is used. | `tests/test_public_package.py::test_memory_install_writes_agent_shortcuts` |
| T23 | New setup | Setup creates required files, asks no storage-location question, requires no manual memory-file editing, and blocks secret-shaped answers. | `tests/test_public_package.py::test_init_creates_public_runtime` and `test_init_blocks_secret_shaped_answers` |
| T24 | Cross-Agent connect | Connect checks the local registry/default path before asking for any folder path, only trusts candidates with the expected starter files, and creates a pointer-only connection. Copied profile/project facts/secrets = 0. | `tests/test_public_package.py::test_memory_connect_finds_existing_library_from_registry` |
| T25 | Backup | Backup asks where to save the zip, accepts the default backup folder wording, and excludes `.env*`, temporary dialogue data, search indexes, drafts, and local database files. | `tests/test_public_package.py::test_memory_shortcuts_and_backup_zip` |
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
