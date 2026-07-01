#!/usr/bin/env python3
"""Public package fixture tests."""

from __future__ import annotations

import json
import os
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


def assert_no_user_first_screen_terms(text: str) -> None:
    blocked = ("runtime", "root", "bridge", "source-of-truth", "session cache", "deprecated", "cli", "markdown")
    lowered = text.lower()
    for term in blocked:
        assert term not in lowered, f"unexpected internal term: {term}"


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
        cursor_connection_exists = (cursor_workspace / ".cursor/rules/agent-memory.mdc").exists()
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
    assert "Agent Memory Connection" in codex_connection
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
        assert "1. memory - Show this menu" in menu.stdout
        assert "2. memory new - Create a memory library" in menu.stdout
        assert "3. memory connect - Connect this Agent" in menu.stdout
        assert "4. memory backup - Back up a memory library" in menu.stdout
        assert "/memory new" in menu.stdout
        assert "/memory connect" in menu.stdout
        assert "/memory backup" in menu.stdout
        assert "Slash-capable Agents may also support:" in menu.stdout
        assert_no_user_first_screen_terms(menu.stdout)

        root = Path(tmp) / "library"
        run("scripts/memory", "--root", str(root), "new", "--answers", "templates/public/answers.example.json")
        workspace = Path(tmp) / "workspace"
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
            home / ".codex/skills/agent-memory/SKILL.md",
            home / ".local/bin/memory",
            home / ".codex/agent-memory-starter-kit-marketplace/.claude-plugin/marketplace.json",
            home / ".codex/agent-memory-starter-kit-marketplace/plugins/agent-memory-starter-kit/.codex-plugin/plugin.json",
            home / ".codex/agent-memory-starter-kit-marketplace/plugins/agent-memory-starter-kit/skills/agent-memory/SKILL.md",
            home / ".codex/agent-memory-starter-kit-marketplace/plugins/agent-memory-starter-kit/commands/memory.md",
            home / ".codex/agent-memory-starter-kit-marketplace/plugins/agent-memory-starter-kit/commands/memory-new.md",
            home / ".codex/agent-memory-starter-kit-marketplace/plugins/agent-memory-starter-kit/commands/memory-connect.md",
            home / ".codex/agent-memory-starter-kit-marketplace/plugins/agent-memory-starter-kit/commands/memory-backup.md",
            workspace / ".claude/commands/memory.md",
            workspace / ".claude/commands/memory-new.md",
            workspace / ".claude/commands/memory-connect.md",
            workspace / ".claude/commands/memory-backup.md",
            workspace / ".cursor/rules/agent-memory-commands.mdc",
            workspace / "AGENT_MEMORY_COMMANDS.md",
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

    assert "Memory shortcuts installed" in install.stdout
    assert "Codex plugin add: skipped_custom_home" in install.stdout
    assert "Text shortcut: memory" in install.stdout
    assert "Text shortcuts: memory new, memory connect, memory backup" in install.stdout
    assert "Shell command installed: memory" in install.stdout
    assert "PATH action: add" in install.stdout
    assert all_expected_exist
    assert memory_shim_executable
    assert "Shell:" in install.stdout
    assert "Preferred:" in texts
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
    assert "[marketplaces.agent-memory-starter-kit-local]" in texts
    assert '[plugins."agent-memory-starter-kit@agent-memory-starter-kit-local"]' in texts
    assert "scripts/memory" in texts
    assert "--root" in texts
    assert "Do not ask the user to hand-edit memory files" in texts
    assert duplicate.returncode == 1
    assert "install_blocked: target exists" in duplicate.stdout
    assert "Memory shortcuts installed" in forced.stdout
    assert cursor_shim_exists
    assert cursor_shim_executable
    assert "Text shortcut: memory" in cursor_install.stdout


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
        test_init_creates_public_runtime,
        test_memory_shortcuts_and_backup_zip,
        test_memory_install_writes_agent_shortcuts,
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
