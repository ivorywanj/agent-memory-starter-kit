#!/usr/bin/env python3
"""Public package fixture tests."""

from __future__ import annotations

import json
import csv
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(*args: str, check: bool = True, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    command_env = os.environ.copy()
    if env:
        command_env.update(env)
    result = subprocess.run(
        [sys.executable, *args] if args[0].endswith(".py") else [*args],
        cwd=ROOT,
        env=command_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if check and result.returncode != 0:
        raise AssertionError(result.stdout)
    return result


def create_local_public_git_repo(path: Path) -> None:
    if (ROOT / "scripts/export_public_package.py").exists():
        run("scripts/export_public_package.py", "--output", str(path))
    else:
        shutil.copytree(
            ROOT,
            path,
            ignore=shutil.ignore_patterns(".git", "__pycache__", ".venv", "venv", "node_modules"),
        )
    subprocess.run(["git", "init"], cwd=path, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    subprocess.run(["git", "add", "."], cwd=path, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    subprocess.run(
        ["git", "-c", "user.name=JourneyMem Tests", "-c", "user.email=tests@example.invalid", "commit", "-m", "fixture"],
        cwd=path,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def assert_no_user_first_screen_terms(text: str) -> None:
    blocked = ("runtime", "root", "bridge", "source-of-truth", "session cache", "deprecated", "cli", "markdown")
    lowered = text.lower()
    for term in blocked:
        assert term not in lowered, f"unexpected internal term: {term}"


def assert_entry_response_style_rules(text: str) -> None:
    lowered = text.lower()
    required = (
        "ask exactly one question at a time",
        "do not show internal analysis",
        "do not ask where to store the memory library",
        "treat the journeymem github url as an install source",
        "do not clone, inspect folder structure, summarize scripts",
        "if the user invokes `$journeymem`, treat it as `memory`",
        "do not infer that they want `memory new`",
        "do not ask for a folder path before checking the local journeymem registry",
        "for same-machine sharing, say no import is needed",
        "a confident memory library candidate must contain",
        "say this will create a zip backup",
        "ask where to save the zip backup",
        "use the default backup folder",
    )
    blocked = (
        "the repo is cloned",
        "i need to run the setup wizard",
        "i will create an answers file",
        "since the script is interactive",
        "non-interactive setup",
        "use sensible defaults",
    )
    for snippet in required:
        assert snippet in lowered, f"missing response style rule: {snippet}"
    for snippet in blocked:
        assert snippet not in lowered, f"noisy setup phrase leaked into helper: {snippet}"


def assert_quiet_first_response(text: str) -> None:
    lowered = text.lower()
    blocked = (
        "repo cloned successfully",
        "repository structure",
        "project structure",
        "inspect the structure",
        "understand the cli",
        "setup wizard",
        "answers file",
        "non-interactive setup",
        "use sensible defaults",
        "what would you like to do next?",
    )
    for snippet in blocked:
        assert snippet not in lowered, f"noisy first-response phrase leaked: {snippet}"
    question_count = text.count("?") + text.count("？")
    assert question_count <= 1, f"too many first-response questions: {question_count}"


def test_repo_agent_instructions_route_fresh_clone() -> None:
    instruction_files = (
        "AGENTS.md",
        "CLAUDE.md",
        ".cursorrules",
        ".cursor/rules/journeymem-first-run.mdc",
        ".trae/rules/journeymem-first-run.md",
        "JOURNEYMEM.md",
    )
    for rel in instruction_files:
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert "# JourneyMem Agent Instructions" in text
        assert "install source fallback, not a generic codebase task" in text
        assert "do not summarize the repository structure" in text
        assert "install or activate JourneyMem first" in text
        assert "I can help you use JourneyMem." in text
        assert "`memory new` - Create a new memory library" in text
        assert "`memory connect` - Connect this Agent to an existing memory library" in text
        assert "Do not start `memory new` until the user chooses create/new." in text
        assert "Do not ask \"What should Agents call you?\" before that choice." in text


def test_start_page_prompt_generation() -> None:
    for rel in ("index.html", "docs/index.html"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        first_screen = text.split("<!-- first-screen-end -->", 1)[0]
        assert "JourneyMem Start" in first_screen
        assert "Start JourneyMem without making your Agent inspect a repo." in first_screen
        assert "Install JourneyMem" in first_screen
        assert_no_user_first_screen_terms(first_screen)
        assert "1. Set up JourneyMem on this computer" in text
        assert "2. Use JourneyMem in my current Agent" in text
        assert "3. Back up or move my memory library" in text
        for agent in ("Codex", "TRAE Work", "Claude Code", "Cursor", "Other Agent"):
            assert f"<summary>{agent}</summary>" in text
        assert text.count("Install or activate JourneyMem first.") >= 5
        assert text.count("use this install source: https://github.com/ivorywanj/agent-memory-starter-kit") >= 5
        assert text.count("Do not clone, inspect folder structure, summarize scripts, or ask what to do with this repo before install/menu.") >= 5
        assert text.count("What do you want to do?") >= 5
        assert text.count("1. memory new - Create a memory library") >= 5
        assert text.count("2. memory connect - Connect this Agent to an existing memory library") >= 5
        assert "--agent" not in text
        assert "--root" not in text
        assert "API key" not in text


def test_init_creates_public_runtime() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "library"
        workspace = Path(tmp) / "example-saas"
        workspace.mkdir()
        (workspace / "private-note.md").write_text("DO_NOT_IMPORT_WORKSPACE_CONTENT", encoding="utf-8")
        answers = Path(tmp) / "answers.json"
        answers.write_text(
            json.dumps(
                {
                    "name": "Alex",
                    "language": "English",
                    "work_type": "indie product builder",
                    "communication_style": "Conclusion first, plain language.",
                    "projects": [{"name": "Example SaaS", "workspace": str(workspace)}, {"name": "Content workflow"}],
                    "confirmation_rules": ["public send", "production deploy"],
                    "never_store": ["secrets", "tokens", "customer data"],
                }
            ),
            encoding="utf-8",
        )
        result = run("scripts/memory", "--root", str(root), "init", "--answers", str(answers))
        expected = [
            "AGENTS.md",
            "ONBOARDING.md",
            "CROSS_AGENT.md",
            "memory/hot/USER.md",
            "memory/hot/MEMORY.md",
            "agent/CURRENT_STATE.md",
            "agent/DECISIONS.md",
            "tasks/lessons.md",
            "memory/projects/projects.md",
            "memory/projects/projects.json",
            "memory/agents/README.md",
        ]
        combined = "\n".join((root / rel).read_text(encoding="utf-8") for rel in expected)
        all_expected_exist = all((root / rel).exists() for rel in expected)
        projects_json = json.loads((root / "memory/projects/projects.json").read_text(encoding="utf-8"))
        codex_workspace = Path(tmp) / "codex-workspace"
        codex_workspace.mkdir()
        codex_connect = run("scripts/memory", "--root", str(root), "connect", "--workspace", str(codex_workspace), env={"AGENT_MEMORY_AGENT": "codex"})
        codex_connection = (codex_workspace / "AGENTS.md").read_text(encoding="utf-8")
        cursor_workspace = Path(tmp) / "cursor-workspace"
        cursor_workspace.mkdir()
        cursor_connect = run("scripts/memory", "--root", str(root), "connect", "--agent", "cursor", "--workspace", str(cursor_workspace))
        cursor_connection_exists = (cursor_workspace / ".cursor/rules/journeymem.mdc").exists()
        second = run("scripts/memory", "--root", str(root), "init", "--answers", str(answers), check=False)

    assert "Memory initialized" in result.stdout
    assert "No Markdown editing required" in result.stdout
    assert all_expected_exist
    assert "Alex" in combined
    assert "Example SaaS" in combined
    assert str(workspace) in combined
    assert "DO_NOT_IMPORT_WORKSPACE_CONTENT" not in combined
    assert "remember -> recall -> improve -> forget" in combined
    assert projects_json["projects"][0]["workspace"] == str(workspace)
    assert projects_json["projects"][0]["workspace_status"] == "verified_at_init"
    assert projects_json["projects"][1]["workspace_status"] == "not_provided"
    assert "Current Agent connected" in codex_connect.stdout
    assert_no_user_first_screen_terms(codex_connect.stdout)
    assert "JourneyMem Connection" in codex_connection
    assert "Alex" not in codex_connection
    assert "Example SaaS" not in codex_connection
    assert "DO_NOT_IMPORT_WORKSPACE_CONTENT" not in codex_connection
    assert "No profile, project facts, or long-term memory were copied" in codex_connect.stdout
    assert "Current Agent connected" in cursor_connect.stdout
    assert cursor_connection_exists
    private_markers = ("Wan" + "jia", "万" + "家", "Journey" + "Gen")
    assert all(marker not in combined for marker in private_markers)
    assert second.returncode == 1
    assert "init_blocked: existing files" in second.stdout


def test_memory_shortcuts_and_backup_zip() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        menu = run("scripts/memory")
        assert "1. memory new - Create a memory library" in menu.stdout
        assert "2. memory connect - Connect this Agent to an existing memory library" in menu.stdout
        assert "Other command:" in menu.stdout
        assert "- memory backup - Back up a memory library" in menu.stdout
        assert "3. memory backup" not in menu.stdout
        assert "4. memory backup" not in menu.stdout
        assert "memory - Show this menu" not in menu.stdout
        assert "/memory new" in menu.stdout
        assert "/memory connect" in menu.stdout
        assert "/memory backup" in menu.stdout
        assert "Slash-capable Agents may also support:" in menu.stdout
        assert_no_user_first_screen_terms(menu.stdout)
        assert_quiet_first_response(menu.stdout)

        root = Path(tmp) / "library"
        run("scripts/memory", "--root", str(root), "new", "--answers", "templates/public/answers.example.json")
        workspace = Path(tmp) / "workspace with spaces"
        workspace.mkdir()
        connect = run("scripts/memory", "--root", str(root), "connect", "--workspace", str(workspace), env={"AGENT_MEMORY_AGENT": "codex"})
        assert "Current Agent connected" in connect.stdout
        assert_no_user_first_screen_terms(connect.stdout)
        connection_file = workspace / "AGENTS.md"
        assert connection_file.exists()
        connection_text = connection_file.read_text(encoding="utf-8")

        (root / ".env.local").write_text("SECRET=not-included", encoding="utf-8")
        (root / "memory/runtime/session_cache").mkdir(parents=True, exist_ok=True)
        (root / "memory/runtime/session_cache/s1.jsonl").write_text("temporary dialogue", encoding="utf-8")
        (root / "memory/history/runtime").mkdir(parents=True, exist_ok=True)
        (root / "memory/history/runtime/history.sqlite3").write_text("sqlite", encoding="utf-8")
        (root / "memory/hot/USER.draft.md").write_text("# draft", encoding="utf-8")
        backup_path = Path(tmp) / "backup.zip"
        backup = run("scripts/memory", "--root", str(root), "backup", "--output", str(backup_path))
        assert "Memory backup created" in backup.stdout
        assert "Current Agent connected" not in backup.stdout
        assert "import" not in backup.stdout.lower()
        assert connection_file.read_text(encoding="utf-8") == connection_text
        with zipfile.ZipFile(backup_path) as archive:
            names = set(archive.namelist())
        assert "AGENTS.md" in names
        assert ".env.local" not in names
        assert "memory/runtime/session_cache/s1.jsonl" not in names
        assert "memory/history/runtime/history.sqlite3" not in names
        assert "memory/hot/USER.draft.md" not in names


def test_memory_connect_finds_existing_library_from_registry() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / "home"
        workspace = Path(tmp) / "codex-workspace"
        workspace.mkdir(parents=True)
        result = run("scripts/memory", "new", "--home", str(home), "--answers", "templates/public/answers.example.json")
        root = home / ".journeymem/libraries/default"
        registry = json.loads((home / ".journeymem/registry.json").read_text(encoding="utf-8"))
        connect = run(
            "scripts/memory",
            "connect",
            "--home",
            str(home),
            "--workspace",
            str(workspace),
            env={"AGENT_MEMORY_AGENT": "codex"},
        )
        connection = (workspace / "AGENTS.md").read_text(encoding="utf-8")
        trae_workspace = Path(tmp) / "trae-workspace"
        trae_workspace.mkdir()
        trae_connect = run(
            "scripts/memory",
            "connect",
            "--home",
            str(home),
            "--workspace",
            str(trae_workspace),
            env={"AGENT_MEMORY_AGENT": "trae"},
        )
        trae_connection = (trae_workspace / ".trae/rules/journeymem.md").read_text(encoding="utf-8")

        assert "Memory initialized" in result.stdout
        assert registry["default_library"] == str(root.resolve())
        assert "Found existing memory library" in connect.stdout
        assert "Current Agent connected" in connect.stdout
        assert "Found existing memory library" in trae_connect.stdout
        assert "Current Agent connected" in trae_connect.stdout
        assert "folder path" not in connect.stdout.lower()
        assert "folder path" not in trae_connect.stdout.lower()
        assert str(root.resolve()) in connection
        assert str(root.resolve()) in trae_connection
        assert "TRAE Work" in trae_connection
        assert "Alex" not in connection
        assert "Alex" not in trae_connection

        (home / ".journeymem/registry.json").unlink()
        fallback_workspace = Path(tmp) / "fallback-workspace"
        fallback_workspace.mkdir()
        fallback_connect = run(
            "scripts/memory",
            "connect",
            "--home",
            str(home),
            "--workspace",
            str(fallback_workspace),
            env={"AGENT_MEMORY_AGENT": "codex"},
        )
        fallback_connection = (fallback_workspace / "AGENTS.md").read_text(encoding="utf-8")

        assert "Found existing memory library" in fallback_connect.stdout
        assert "Current Agent connected" in fallback_connect.stdout
        assert "folder path" not in fallback_connect.stdout.lower()
        assert str(root.resolve()) in fallback_connection


def test_memory_connect_restores_backup_zip_on_clean_home() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        source_root = Path(tmp) / "source-library"
        source_home = Path(tmp) / "source-home"
        target_home = Path(tmp) / "target-home"
        workspace = Path(tmp) / "target-workspace"
        workspace.mkdir()
        run("scripts/memory", "--root", str(source_root), "new", "--home", str(source_home), "--answers", "templates/public/answers.example.json")
        (source_root / ".env.local").write_text("SECRET=not-restored", encoding="utf-8")
        (source_root / "memory/runtime/session_cache").mkdir(parents=True, exist_ok=True)
        (source_root / "memory/runtime/session_cache/s1.jsonl").write_text("temporary dialogue", encoding="utf-8")
        backup_path = Path(tmp) / "journeymem.zip"
        backup = run("scripts/memory", "--root", str(source_root), "backup", "--output", str(backup_path))
        connect = run(
            "scripts/memory",
            "connect",
            "--home",
            str(target_home),
            "--backup",
            str(backup_path),
            "--workspace",
            str(workspace),
            env={"AGENT_MEMORY_AGENT": "codex"},
        )
        restored = target_home / ".journeymem/libraries/default"
        registry = json.loads((target_home / ".journeymem/registry.json").read_text(encoding="utf-8"))
        connection = (workspace / "AGENTS.md").read_text(encoding="utf-8")

        assert "Memory backup created" in backup.stdout
        assert "Memory library restored from backup" in connect.stdout
        assert "Current Agent connected" in connect.stdout
        assert "folder path" not in connect.stdout.lower()
        assert registry["default_library"] == str(restored.resolve())
        for rel in ("AGENTS.md", "ONBOARDING.md", "memory/hot/USER.md", "memory/hot/MEMORY.md"):
            assert (restored / rel).exists()
        assert not (restored / ".env.local").exists()
        assert not (restored / "memory/runtime/session_cache/s1.jsonl").exists()
        assert str(restored.resolve()) in connection
        recall = run("scripts/memory", "--root", str(restored), "recall", "--query", "indie product builder", "--context-only")
        assert "[hot_memory | medium] memory/hot/USER.md" in recall.stdout
        assert "Final answer generation" not in recall.stdout
        status = run("scripts/memory_status.py", "--root", str(restored))
        assert "- Startup path: ready: AGENTS.md -> ONBOARDING.md -> memory/hot/USER.md -> memory/hot/MEMORY.md" in status.stdout
        assert "USER.md: ok" in status.stdout
        assert "MEMORY.md: ok" in status.stdout
        assert "- Safety scan: memory_guard: pass (exit 0)" in status.stdout


def test_memory_connect_rejects_stale_registry_and_unsafe_backups() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / "home"
        workspace = Path(tmp) / "workspace"
        workspace.mkdir()
        registry_dir = home / ".journeymem"
        registry_dir.mkdir(parents=True)
        stale_root = Path(tmp) / "missing-library"
        registry_dir.joinpath("registry.json").write_text(
            json.dumps(
                {
                    "version": 1,
                    "default_library": str(stale_root),
                    "libraries": [{"name": "stale", "path": str(stale_root)}],
                    "agents": {},
                }
            ),
            encoding="utf-8",
        )
        stale = run(
            "scripts/memory",
            "connect",
            "--home",
            str(home),
            "--workspace",
            str(workspace),
            env={"AGENT_MEMORY_AGENT": "codex"},
            check=False,
        )

        assert stale.returncode == 1
        assert "connect_needs_memory_library" in stale.stdout
        assert "No existing JourneyMem memory library was found" in stale.stdout
        assert "backup zip" in stale.stdout
        assert "memory new" in stale.stdout
        assert not (workspace / "AGENTS.md").exists()

        incomplete_zip = Path(tmp) / "incomplete.zip"
        with zipfile.ZipFile(incomplete_zip, "w") as archive:
            archive.writestr("AGENTS.md", "# AGENTS\n")
        incomplete = run(
            "scripts/memory",
            "connect",
            "--home",
            str(home),
            "--backup",
            str(incomplete_zip),
            "--workspace",
            str(workspace),
            env={"AGENT_MEMORY_AGENT": "codex"},
            check=False,
        )

        assert incomplete.returncode == 1
        assert "connect_blocked: backup_missing_required:" in incomplete.stdout
        assert not (home / ".journeymem/libraries/default").exists()

        unsafe_zip = Path(tmp) / "unsafe.zip"
        with zipfile.ZipFile(unsafe_zip, "w") as archive:
            for rel in ("AGENTS.md", "ONBOARDING.md", "memory/hot/USER.md", "memory/hot/MEMORY.md"):
                archive.writestr(rel, "safe placeholder\n")
            archive.writestr(".env.local", "SECRET=blocked\n")
        unsafe = run(
            "scripts/memory",
            "connect",
            "--home",
            str(home),
            "--backup",
            str(unsafe_zip),
            "--workspace",
            str(workspace),
            env={"AGENT_MEMORY_AGENT": "codex"},
            check=False,
        )

        assert unsafe.returncode == 1
        assert "connect_blocked: blocked_member:secret_file:.env.local" in unsafe.stdout
        assert not (home / ".journeymem/libraries/default").exists()


def test_score_agent_entry_transcripts_accepts_good_and_flags_bad_outputs() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        good = Path(tmp) / "good.jsonl"
        good.write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "id": "codex-1",
                            "agent": "codex",
                            "scenario": "valid_default",
                            "text": "What do you want to do?\n1. memory new - Create a memory library\n2. memory connect - Connect this Agent to an existing memory library\nOther command:\n- memory backup - Back up a memory library",
                        }
                    ),
                    json.dumps(
                        {
                            "id": "codex-skill",
                            "agent": "codex",
                            "scenario": "skill_trigger",
                            "text": "What do you want to do?\n1. memory new - Create a memory library\n2. memory connect - Connect this Agent to an existing memory library",
                        }
                    ),
                    json.dumps(
                        {
                            "id": "trae-1",
                            "agent": "trae",
                            "scenario": "start_page",
                            "text": "What do you want to do?\n1. memory new - Create a memory library\n2. memory connect - Connect this Agent to an existing memory library",
                        }
                    ),
                    json.dumps(
                        {
                            "id": "trae-2",
                            "agent": "trae",
                            "scenario": "github_fallback",
                            "text": "What do you want to do?\n1. memory new - Create a memory library\n2. memory connect - Connect this Agent to an existing memory library",
                        }
                    ),
                ]
            ),
            encoding="utf-8",
        )
        good_csv = Path(tmp) / "good.csv"
        good_score = run(
            "scripts/score_agent_entry_transcripts.py",
            "--input",
            str(good),
            "--output",
            str(good_csv),
            "--require-agents",
            "codex,trae",
            "--require-scenarios",
            "valid_default,skill_trigger,start_page,github_fallback",
            "--require-trae-trials",
            "1",
        )
        good_rows = list(csv.DictReader(good_csv.open(newline="", encoding="utf-8")))

        raw_dir = Path(tmp) / "raw-transcripts"
        raw_dir.mkdir()
        raw_menu = "What do you want to do?\n1. memory new - Create a memory library\n2. memory connect - Connect this Agent to an existing memory library"
        (raw_dir / "codex-valid-default-1.txt").write_text(raw_menu + "\nOther command:\n- memory backup - Back up a memory library", encoding="utf-8")
        (raw_dir / "codex-skill-trigger-1.txt").write_text(raw_menu, encoding="utf-8")
        (raw_dir / "trae-start-page-1.txt").write_text(raw_menu, encoding="utf-8")
        (raw_dir / "trae-github-fallback-1.txt").write_text(raw_menu, encoding="utf-8")
        raw_file = Path(tmp) / "codex-valid-default-single.txt"
        raw_file.write_text(raw_menu, encoding="utf-8")
        raw_score = run(
            "scripts/score_agent_entry_transcripts.py",
            "--input",
            str(raw_dir),
            "--require-agents",
            "codex,trae",
            "--require-scenarios",
            "valid_default,skill_trigger,start_page,github_fallback",
            "--require-trae-trials",
            "1",
        )
        raw_file_score = run(
            "scripts/score_agent_entry_transcripts.py",
            "--input",
            str(raw_file),
            "--require-agents",
            "codex",
        )

        missing_trae = Path(tmp) / "missing-trae.jsonl"
        missing_trae.write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "id": "codex-only",
                            "agent": "codex",
                            "scenario": "valid_default",
                            "text": "What do you want to do?\n1. memory new - Create a memory library\n2. memory connect - Connect this Agent to an existing memory library",
                        }
                    ),
                ]
            ),
            encoding="utf-8",
        )

        bad = Path(tmp) / "bad.jsonl"
        bad.write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "id": "trae-bad",
                            "agent": "trae",
                            "scenario": "valid_default",
                            "text": "Repo cloned successfully. Here is the repository structure. Please paste the full folder path to your existing JourneyMem memory library.",
                        }
                    ),
                ]
            ),
            encoding="utf-8",
        )
        bad_score = run("scripts/score_agent_entry_transcripts.py", "--input", str(bad), "--require-trae-trials", "1", check=False)
        missing_agent_score = run(
            "scripts/score_agent_entry_transcripts.py",
            "--input",
            str(missing_trae),
            "--require-agents",
            "codex,trae",
            "--require-trae-trials",
            "1",
            check=False,
        )
        missing_scenario_score = run(
            "scripts/score_agent_entry_transcripts.py",
            "--input",
            str(missing_trae),
            "--require-agents",
            "codex",
            "--require-scenarios",
            "valid_default,start_page",
            check=False,
        )
        missing_score = run("scripts/score_agent_entry_transcripts.py", "--input", str(Path(tmp) / "missing.jsonl"), check=False)
        example_score = run(
            "scripts/score_agent_entry_transcripts.py",
            "--input",
            "templates/public/agent-entry-transcripts.example.jsonl",
            "--require-agents",
            "codex,trae",
            "--require-trae-trials",
            "1",
        )

    assert "- status: pass" in good_score.stdout
    assert "- missing_agents: none" in good_score.stdout
    assert "- status: pass" in raw_score.stdout
    assert "- missing_agents: none" in raw_score.stdout
    assert "- status: pass" in raw_file_score.stdout
    assert "- status: pass" in example_score.stdout
    assert len(good_rows) == 4
    assert all(row["pass"] == "1" for row in good_rows)
    assert bad_score.returncode == 1
    assert "- status: fail" in bad_score.stdout
    assert "clone_or_inspect=1" in bad_score.stdout
    assert "folder_prompt=1" in bad_score.stdout
    assert missing_agent_score.returncode == 1
    assert "- missing_agents: trae" in missing_agent_score.stdout
    assert missing_scenario_score.returncode == 1
    assert "- missing_scenarios: start_page" in missing_scenario_score.stdout
    assert missing_score.returncode == 1
    assert "input_missing:" in missing_score.stdout
    assert "Traceback" not in missing_score.stdout


def test_prepare_agent_entry_trials_creates_empty_evidence_pack() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "trial-pack"
        result = run("scripts/prepare_agent_entry_trials.py", "--output", str(output))
        duplicate = run("scripts/prepare_agent_entry_trials.py", "--output", str(output), check=False)
        forced = run("scripts/prepare_agent_entry_trials.py", "--output", str(output), "--force")
        empty_gate = run(
            "scripts/prd_acceptance_check.py",
            "--mode",
            "transcript-only",
            "--transcripts",
            str(output / "transcripts"),
            "--require-trae-trials",
            "3",
            check=False,
        )

        assert result.returncode == 0
        assert forced.returncode == 0
        assert duplicate.returncode == 1
        assert "trial_pack_exists:" in duplicate.stdout
        assert (output / "README.md").exists()
        assert (output / "prompts/codex-valid-default-1.prompt.txt").exists()
        assert (output / "prompts/codex-skill-trigger-1.prompt.txt").exists()
        assert (output / "prompts/codex-start-page-1.prompt.txt").exists()
        assert (output / "prompts/codex-github-fallback-1.prompt.txt").exists()
        assert (output / "prompts/cursor-start-page-1.prompt.txt").exists()
        assert (output / "prompts/trae-github-fallback-1.prompt.txt").exists()
        assert "\n" not in (output / "prompts/trae-valid-default-1.prompt.txt").read_text(encoding="utf-8").strip()
        assert "\n" not in (output / "prompts/trae-github-fallback-1.prompt.txt").read_text(encoding="utf-8").strip()
        assert not list((output / "transcripts").glob("*.txt"))
        assert "- status: fail" in empty_gate.stdout
        assert "- records: 0" in empty_gate.stdout


def test_collect_codex_entry_transcript_writes_scoreable_output() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "trial-pack"
        workspace = Path(tmp) / "workspace"
        workspace.mkdir()
        run("scripts/prepare_agent_entry_trials.py", "--output", str(output))
        fake_codex = Path(tmp) / "fake_codex.py"
        fake_codex.write_text(
            "#!/usr/bin/env python3\n"
            "from pathlib import Path\n"
            "import sys\n"
            "out = Path(sys.argv[sys.argv.index('-o') + 1])\n"
            "sys.stdin.read()\n"
            "out.write_text('What do you want to do?\\n1. memory new - Create a memory library\\n2. memory connect - Connect this Agent to an existing memory library\\n', encoding='utf-8')\n",
            encoding="utf-8",
        )
        fake_codex.chmod(0o755)
        result = run(
            "scripts/collect_codex_entry_transcript.py",
            "--trial-pack",
            str(output),
            "--workspace",
            str(workspace),
            "--codex-bin",
            str(fake_codex),
        )
        dry_run = run(
            "scripts/collect_codex_entry_transcript.py",
            "--trial-pack",
            str(output),
            "--workspace",
            str(workspace),
            "--codex-bin",
            str(fake_codex),
            "--dry-run",
        )
        transcript = (output / "transcripts/codex-valid-default-1.txt").read_text(encoding="utf-8")

    assert "codex_entry_transcript:" in result.stdout
    assert "- status: pass" in result.stdout
    assert "memory new" in transcript
    assert "memory connect" in transcript
    assert "codex_entry_command:" in dry_run.stdout
    assert "--sandbox read-only" in dry_run.stdout


def test_collect_cursor_entry_transcript_writes_scoreable_output_and_blocks_usage_limit() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "trial-pack"
        workspace = Path(tmp) / "workspace"
        workspace.mkdir()
        run("scripts/prepare_agent_entry_trials.py", "--output", str(output))
        fake_cursor = Path(tmp) / "fake_cursor.py"
        fake_cursor.write_text(
            "#!/usr/bin/env python3\n"
            "print('What do you want to do?\\n1. memory new - Create a memory library\\n2. memory connect - Connect this Agent to an existing memory library')\n",
            encoding="utf-8",
        )
        fake_cursor.chmod(0o755)
        result = run(
            "scripts/collect_cursor_entry_transcript.py",
            "--trial-pack",
            str(output),
            "--workspace",
            str(workspace),
            "--cursor-bin",
            str(fake_cursor),
        )
        dry_run = run(
            "scripts/collect_cursor_entry_transcript.py",
            "--trial-pack",
            str(output),
            "--workspace",
            str(workspace),
            "--cursor-bin",
            str(fake_cursor),
            "--dry-run",
        )
        limit_cursor = Path(tmp) / "limit_cursor.py"
        limit_cursor.write_text(
            "#!/usr/bin/env python3\n"
            "import sys\n"
            "print(\"ActionRequiredError: You've hit your usage limit Get Cursor Pro for more Agent usage\")\n"
            "raise SystemExit(1)\n",
            encoding="utf-8",
        )
        limit_cursor.chmod(0o755)
        limit_result = run(
            "scripts/collect_cursor_entry_transcript.py",
            "--trial-pack",
            str(output),
            "--workspace",
            str(workspace),
            "--cursor-bin",
            str(limit_cursor),
            check=False,
        )
        transcript = (output / "transcripts/cursor-valid-default-1.txt").read_text(encoding="utf-8")

    assert "cursor_entry_transcript:" in result.stdout
    assert "- status: pass" in result.stdout
    assert "memory new" in transcript
    assert "memory connect" in transcript
    assert "cursor_entry_command:" in dry_run.stdout
    assert "--sandbox enabled" in dry_run.stdout
    assert limit_result.returncode == 1
    assert "cursor_entry_failed:" in limit_result.stdout
    assert "usage limit" in limit_result.stdout.lower()


def test_agent_entry_readiness_reports_missing_and_complete_evidence() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        missing_pack = Path(tmp) / "missing-pack"
        missing = run("scripts/agent_entry_readiness.py", "--trial-pack", str(missing_pack), check=False)

        partial_pack = Path(tmp) / "partial-pack"
        transcripts = partial_pack / "transcripts"
        transcripts.mkdir(parents=True)
        menu = "What do you want to do?\n1. memory new - Create a memory library\n2. memory connect - Connect this Agent to an existing memory library\n"
        (transcripts / "codex-valid-default-1.txt").write_text(menu, encoding="utf-8")
        partial = run("scripts/agent_entry_readiness.py", "--trial-pack", str(partial_pack), check=False)

        complete_pack = Path(tmp) / "complete-pack"
        complete_transcripts = complete_pack / "transcripts"
        complete_transcripts.mkdir(parents=True)
        for name in (
            "codex-valid-default-1.txt",
            "codex-skill-trigger-1.txt",
            "codex-start-page-1.txt",
            "codex-github-fallback-1.txt",
            "trae-valid-default-1.txt",
            "trae-skill-trigger-1.txt",
            "trae-start-page-1.txt",
            "trae-github-fallback-1.txt",
        ):
            complete_transcripts.joinpath(name).write_text(menu, encoding="utf-8")
        complete = run("scripts/agent_entry_readiness.py", "--trial-pack", str(complete_pack))

    assert missing.returncode == 1
    assert "transcript_dir: missing" in missing.stdout
    assert "prepare_agent_entry_trials.py" in missing.stdout
    assert partial.returncode == 1
    assert "transcript_codex-valid-default-1.txt: present" in partial.stdout
    assert "transcript_cursor-valid-default-1.txt" not in partial.stdout
    assert "collect_cursor_entry_transcript.py" not in partial.stdout
    assert "trae-github-fallback-1.txt" in partial.stdout
    assert "- status: fail" in partial.stdout
    assert "- status: pass" in complete.stdout
    assert "missing_agents: none" in complete.stdout


def test_save_agent_entry_transcript_names_scores_and_blocks_unsafe_text() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        pack = Path(tmp) / "trial-pack"
        run("scripts/prepare_agent_entry_trials.py", "--output", str(pack))
        menu = "What do you want to do?\n1. memory new - Create a memory library\n2. memory connect - Connect this Agent to an existing memory library\n"
        input_file = Path(tmp) / "first-response.txt"
        input_file.write_text(menu, encoding="utf-8")
        save_cursor = run(
            "scripts/save_agent_entry_transcript.py",
            "--trial-pack",
            str(pack),
            "--agent",
            "cursor",
            "--input",
            str(input_file),
        )
        duplicate = run(
            "scripts/save_agent_entry_transcript.py",
            "--trial-pack",
            str(pack),
            "--agent",
            "cursor",
            "--input",
            str(input_file),
            check=False,
        )
        for scenario in ("valid-default", "skill-trigger", "start-page", "github-fallback"):
            run(
                "scripts/save_agent_entry_transcript.py",
                "--trial-pack",
                str(pack),
                "--agent",
                "trae",
                "--scenario",
                scenario,
                "--input",
                str(input_file),
            )
        unsafe = run(
            "scripts/save_agent_entry_transcript.py",
            "--trial-pack",
            str(pack),
            "--agent",
            "codex",
            "--text",
            "sk-" + "abcdefghijklmnopqrstuvwxyz123456",
            check=False,
        )
        readiness = run("scripts/agent_entry_readiness.py", "--trial-pack", str(pack), check=False)

        assert "transcript_saved:" in save_cursor.stdout
        assert "- status: pass" in save_cursor.stdout
        assert (pack / "transcripts/cursor-valid-default-1.txt").exists()
        assert (pack / "transcripts/trae-github-fallback-1.txt").exists()
        assert duplicate.returncode == 1
        assert "transcript_exists:" in duplicate.stdout
        assert unsafe.returncode == 1
        assert "transcript_blocked: secret_like_text" in unsafe.stdout
        assert "transcript_cursor-valid-default-1.txt" not in readiness.stdout
        assert "transcript_trae-github-fallback-1.txt: present" in readiness.stdout
        assert "transcript_codex-valid-default-1.txt: missing" in readiness.stdout


def test_memory_install_writes_agent_shortcuts() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "library"
        workspace = Path(tmp) / "workspace"
        home = Path(tmp) / "home"
        workspace.mkdir()
        home.mkdir()
        run("scripts/memory", "--root", str(root), "new", "--answers", "templates/public/answers.example.json")
        install = run(
            "scripts/memory",
            "--root",
            str(root),
            "install",
            "--agent",
            "all",
            "--workspace",
            str(workspace),
            "--home",
            str(home),
        )
        expected = [
            home / ".codex/config.toml",
            home / ".codex/skills/journeymem/SKILL.md",
            home / ".local/bin/memory",
            home / ".codex/journeymem-marketplace/.claude-plugin/marketplace.json",
            home / ".codex/journeymem-marketplace/plugins/journeymem/.codex-plugin/plugin.json",
            home / ".codex/journeymem-marketplace/plugins/journeymem/skills/journeymem/SKILL.md",
            home / ".codex/journeymem-marketplace/plugins/journeymem/commands/memory.md",
            home / ".codex/journeymem-marketplace/plugins/journeymem/commands/memory-new.md",
            home / ".codex/journeymem-marketplace/plugins/journeymem/commands/memory-connect.md",
            home / ".codex/journeymem-marketplace/plugins/journeymem/commands/memory-backup.md",
            workspace / ".claude/commands/memory.md",
            workspace / ".claude/commands/memory-new.md",
            workspace / ".claude/commands/memory-connect.md",
            workspace / ".claude/commands/memory-backup.md",
            workspace / ".cursor/rules/journeymem-commands.mdc",
            workspace / ".trae/rules/journeymem-commands.md",
            workspace / "TRAE_MEMORY.md",
            workspace / "JOURNEYMEM_COMMANDS.md",
        ]
        all_expected_exist = all(path.exists() for path in expected)
        memory_shim_executable = os.access(home / ".local/bin/memory", os.X_OK)
        texts = "\n".join(path.read_text(encoding="utf-8") for path in expected)
        duplicate = run(
            "scripts/memory",
            "--root",
            str(root),
            "install",
            "--agent",
            "all",
            "--workspace",
            str(workspace),
            "--home",
            str(home),
            check=False,
        )
        forced = run(
            "scripts/memory",
            "--root",
            str(root),
            "install",
            "--agent",
            "all",
            "--workspace",
            str(workspace),
            "--home",
            str(home),
            "--force",
        )
        cursor_home = Path(tmp) / "cursor-home"
        cursor_workspace = Path(tmp) / "cursor-workspace"
        cursor_home.mkdir()
        cursor_workspace.mkdir()
        cursor_install = run(
            "scripts/memory",
            "--root",
            str(root),
            "install",
            "--agent",
            "cursor",
            "--workspace",
            str(cursor_workspace),
            "--home",
            str(cursor_home),
        )
        cursor_shim = cursor_home / ".local/bin/memory"
        cursor_shim_exists = cursor_shim.exists()
        cursor_shim_executable = os.access(cursor_shim, os.X_OK)

    assert "JourneyMem shortcuts installed" in install.stdout
    assert "Installed for: Codex, Claude Code, Cursor, TRAE Work, Generic Agent" in install.stdout
    assert "Codex plugin add: skipped_custom_home" in install.stdout
    assert "Text shortcut: memory" in install.stdout
    assert "Text shortcuts: memory new, memory connect, memory backup" in install.stdout
    assert "Shell command installed: memory" in install.stdout
    assert "Skill-capable Agents: $journeymem" in install.stdout
    assert "PATH action: add" in install.stdout
    assert all_expected_exist
    assert memory_shim_executable
    assert "Shell:" in install.stdout
    assert "Preferred:" in texts
    assert "$journeymem" in texts
    assert "memory backup" in texts
    assert "/memory" in texts
    assert "memory new" in texts
    assert "/memory new" in texts
    assert "/memory connect" in texts
    assert "/memory backup" in texts
    assert "$ARGUMENTS" in texts
    assert "`new`: run `" in texts
    assert "`connect`: run `" in texts
    assert "`backup`: run `" in texts
    assert "If arguments are unclear" in texts
    assert "[marketplaces.journeymem-local]" in texts
    assert '[plugins."journeymem@journeymem-local"]' in texts
    assert "scripts/memory" in texts
    assert "--root" in texts
    assert "Do not ask the user to hand-edit memory files" in texts
    assert "Treat the JourneyMem GitHub URL as an install source" in texts
    assert "Do not clone, inspect folder structure, summarize scripts" in texts
    assert_entry_response_style_rules(texts)
    assert duplicate.returncode == 1
    assert "install_blocked: target exists" in duplicate.stdout
    assert "JourneyMem shortcuts installed" in forced.stdout
    assert cursor_shim_exists
    assert cursor_shim_executable
    assert "Text shortcut: memory" in cursor_install.stdout


def test_install_script_installs_command_without_creating_memory_library() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / "home"
        workspace = Path(tmp) / "workspace with spaces"
        home.mkdir()
        workspace.mkdir()
        result = subprocess.run(
            ["sh", "install.sh"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            env={
                **os.environ,
                "JOURNEYMEM_HOME": str(home),
                "JOURNEYMEM_WORKSPACE": str(workspace),
                "JOURNEYMEM_AGENT": "all",
                "JOURNEYMEM_FORCE": "1",
            },
        )
        registry = json.loads((home / ".journeymem/registry.json").read_text(encoding="utf-8"))
        memory_cmd = home / ".local/bin/memory"
        package_root = home / ".journeymem/starter-kit"
        package_memory_cmd = home / ".journeymem/starter-kit/scripts/memory"
        default_library = home / ".journeymem/libraries/default"
        memory_cmd_exists = memory_cmd.exists()
        memory_cmd_executable = os.access(memory_cmd, os.X_OK)
        package_memory_cmd_exists = package_memory_cmd.exists()
        package_readme = (package_root / "README.md").read_text(encoding="utf-8")
        package_has_private_source_file = (package_root / "OPEN_SOURCE_PACKAGE.md").exists()
        shim_text = memory_cmd.read_text(encoding="utf-8")
        trae_helper_exists = (workspace / ".trae/rules/journeymem-commands.md").exists()
        default_library_created = (default_library / "AGENTS.md").exists()
        menu = subprocess.run(
            [str(memory_cmd)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            env={**os.environ, "HOME": str(home)},
        )
        unsafe_home = Path(tmp) / "unsafe-home"
        unsafe_workspace = Path(tmp) / "unsafe-workspace"
        unsafe_package = Path(tmp) / "not-journeymem-package"
        unsafe_home.mkdir()
        unsafe_workspace.mkdir()
        unsafe_package.mkdir()
        (unsafe_package / "user-file.txt").write_text("do not delete", encoding="utf-8")
        unsafe_result = subprocess.run(
            ["sh", "install.sh"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            env={
                **os.environ,
                "JOURNEYMEM_HOME": str(unsafe_home),
                "JOURNEYMEM_WORKSPACE": str(unsafe_workspace),
                "JOURNEYMEM_PACKAGE_DIR": str(unsafe_package),
                "JOURNEYMEM_AGENT": "all",
                "JOURNEYMEM_FORCE": "1",
            },
        )
        unsafe_file_preserved = (unsafe_package / "user-file.txt").exists()

        auto_home = Path(tmp) / "auto-home"
        auto_workspace = Path(tmp) / "auto-workspace"
        auto_home.mkdir()
        auto_workspace.mkdir()
        auto_install = run(
            "scripts/memory",
            "--root",
            str(home / ".journeymem/starter-kit"),
            "install",
            "--agent",
            "auto",
            "--workspace",
            str(auto_workspace),
            "--home",
            str(auto_home),
            env={"AGENT_MEMORY_AGENT": "cursor"},
        )
        auto_cursor_helper = (auto_workspace / ".cursor/rules/journeymem-commands.mdc").exists()
        auto_claude_helper = (auto_workspace / ".claude/commands/memory.md").exists()
        auto_trae_helper = (auto_workspace / ".trae/rules/journeymem-commands.md").exists()

        remote_repo = Path(tmp) / "remote-repo"
        create_local_public_git_repo(remote_repo)
        remote_home = Path(tmp) / "remote-home"
        remote_workspace = Path(tmp) / "remote workspace"
        remote_package = Path(tmp) / "old-package"
        remote_home.mkdir()
        remote_workspace.mkdir()
        (remote_package / "scripts").mkdir(parents=True)
        (remote_package / "scripts/memory").write_text("old command", encoding="utf-8")
        (remote_package / "scripts/memory_runtime.py").write_text("old runtime", encoding="utf-8")
        (remote_package / "README.md").write_text("stale package", encoding="utf-8")
        remote_installer = Path(tmp) / "install-remote.sh"
        remote_installer.write_text((ROOT / "install.sh").read_text(encoding="utf-8"), encoding="utf-8")
        remote_result = subprocess.run(
            ["sh", str(remote_installer)],
            cwd=remote_workspace,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            env={
                **os.environ,
                "JOURNEYMEM_HOME": str(remote_home),
                "JOURNEYMEM_WORKSPACE": str(remote_workspace),
                "JOURNEYMEM_PACKAGE_DIR": str(remote_package),
                "JOURNEYMEM_REPO_URL": str(remote_repo),
                "JOURNEYMEM_AGENT": "all",
                "JOURNEYMEM_FORCE": "1",
            },
        )
        remote_memory_cmd = remote_home / ".local/bin/memory"
        remote_package_readme = (remote_package / "README.md").read_text(encoding="utf-8")
        remote_shim_text = remote_memory_cmd.read_text(encoding="utf-8")

    assert result.returncode == 0, result.stdout
    assert "JourneyMem installed" in result.stdout
    assert "Next step: type memory, then choose memory new or memory connect." in result.stdout
    assert registry == {"agents": {}, "default_library": None, "libraries": [], "version": 1}
    assert memory_cmd_exists
    assert memory_cmd_executable
    assert package_memory_cmd_exists
    assert "A local memory library for AI agents." in package_readme
    assert "Wan" + "jia" not in package_readme
    assert "万" + "家" not in package_readme
    assert "/Users/" + "wanj" not in package_readme
    assert not package_has_private_source_file
    assert str(package_memory_cmd) in shim_text
    assert str(ROOT / "scripts/memory") not in shim_text
    assert trae_helper_exists
    assert not default_library_created
    assert "What do you want to do?" in menu.stdout
    assert "memory new" in menu.stdout
    assert "memory connect" in menu.stdout
    assert unsafe_result.returncode == 1
    assert "install_blocked: package dir exists but is not JourneyMem" in unsafe_result.stdout
    assert unsafe_file_preserved
    assert "Installed for: Cursor" in auto_install.stdout
    assert auto_cursor_helper
    assert not auto_claude_helper
    assert not auto_trae_helper
    assert remote_result.returncode == 0, remote_result.stdout
    assert "JourneyMem installed" in remote_result.stdout
    assert "A local memory library for AI agents." in remote_package_readme
    assert "stale package" not in remote_package_readme
    assert str(remote_package / "scripts/memory") in remote_shim_text


def test_memory_loop_promotes_recalls_and_deprecates() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "library"
        run("scripts/memory", "--root", str(root), "init", "--answers", "templates/public/answers.example.json")
        run(
            "scripts/memory",
            "--root",
            str(root),
            "remember",
            "--session-id",
            "demo",
            "--text",
            "以后测试通过必须验证真实行为，不能只检查文件存在。",
            "--type",
            "failure_pattern",
            "--target",
            "tasks/lessons.md",
        )
        improve = run("scripts/memory", "--root", str(root), "improve", "--session-id", "demo")
        recall = run("scripts/memory", "--root", str(root), "recall", "--query", "测试 真实行为", "--context-only")
        forget = run("scripts/memory", "--root", str(root), "forget", "--instruction", "删除第 1 条")
        blocked_recall = run("scripts/memory", "--root", str(root), "recall", "--query", "测试 真实行为", "--context-only")

    assert "Promoted:" in improve.stdout
    assert "[source_of_truth | high]" in recall.stdout
    assert "Deprecated:" in forget.stdout
    assert "[deprecated | blocked]" in blocked_recall.stdout


def test_init_blocks_secret_shaped_answers() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        answers = Path(tmp) / "answers.json"
        answers.write_text(
            json.dumps({"name": "Alex", "projects": [{"name": "Safe name", "workspace": "sk-" + "abcdefghijklmnopqrstuvwxyz123456"}]}),
            encoding="utf-8",
        )
        result = run("scripts/memory", "--root", str(Path(tmp) / "library"), "init", "--answers", str(answers), check=False)

    assert result.returncode == 1
    assert "init_blocked:" in result.stdout
    assert "abcdefghijklmnopqrstuvwxyz" not in result.stdout


def test_memory_guard_passes_public_package() -> None:
    result = run("scripts/memory_guard.py")
    assert "memory_guard: pass" in result.stdout


def test_public_release_check_passes_package() -> None:
    result = run("scripts/public_release_check.py")
    assert "public_release_check: pass" in result.stdout


def main() -> int:
    tests = [
        test_repo_agent_instructions_route_fresh_clone,
        test_start_page_prompt_generation,
        test_init_creates_public_runtime,
        test_memory_shortcuts_and_backup_zip,
        test_memory_connect_finds_existing_library_from_registry,
        test_memory_connect_restores_backup_zip_on_clean_home,
        test_memory_connect_rejects_stale_registry_and_unsafe_backups,
        test_score_agent_entry_transcripts_accepts_good_and_flags_bad_outputs,
        test_prepare_agent_entry_trials_creates_empty_evidence_pack,
        test_collect_codex_entry_transcript_writes_scoreable_output,
        test_collect_cursor_entry_transcript_writes_scoreable_output_and_blocks_usage_limit,
        test_agent_entry_readiness_reports_missing_and_complete_evidence,
        test_save_agent_entry_transcript_names_scores_and_blocks_unsafe_text,
        test_memory_install_writes_agent_shortcuts,
        test_install_script_installs_command_without_creating_memory_library,
        test_memory_loop_promotes_recalls_and_deprecates,
        test_init_blocks_secret_shaped_answers,
        test_memory_guard_passes_public_package,
        test_public_release_check_passes_package,
    ]
    for test in tests:
        test()
        print(f"pass {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
