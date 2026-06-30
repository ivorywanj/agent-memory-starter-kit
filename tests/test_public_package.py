#!/usr/bin/env python3
"""Public package fixture tests."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, *args] if args[0].endswith(".py") else [*args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if check and result.returncode != 0:
        raise AssertionError(result.stdout)
    return result


def test_init_creates_public_runtime() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "runtime"
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
        codex_share = run("scripts/memory", "--root", str(root), "share", "--agent", "codex", "--workspace", str(codex_workspace))
        codex_bridge = (codex_workspace / "AGENTS.md").read_text(encoding="utf-8")
        cursor_workspace = Path(tmp) / "cursor-workspace"
        cursor_workspace.mkdir()
        cursor_share = run("scripts/memory", "--root", str(root), "share", "--agent", "cursor", "--workspace", str(cursor_workspace))
        cursor_bridge_exists = (cursor_workspace / ".cursor/rules/agent-memory.mdc").exists()
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
    assert "Shared memory bridge ready" in codex_share.stdout
    assert "This bridge is a pointer only" in codex_bridge
    assert "Alex" not in codex_bridge
    assert "Example SaaS" not in codex_bridge
    assert "DO_NOT_IMPORT_WORKSPACE_CONTENT" not in codex_bridge
    assert "Shared memory bridge ready" in cursor_share.stdout
    assert cursor_bridge_exists
    private_markers = ("Wan" + "jia", "万" + "家", "Journey" + "Gen")
    assert all(marker not in combined for marker in private_markers)
    assert second.returncode == 1
    assert "init_blocked: existing files" in second.stdout


def test_memory_loop_promotes_recalls_and_deprecates() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "runtime"
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
        result = run("scripts/memory", "--root", str(Path(tmp) / "runtime"), "init", "--answers", str(answers), check=False)

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
