#!/usr/bin/env python3
"""Lightweight remember/recall/improve/forget runtime for JourneyMem."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shlex
import shutil
import os
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

import memory_guard


HOT_LIMITS = {
    "memory/hot/USER.md": 1800,
    "memory/hot/MEMORY.md": 2400,
}
SOURCE_TARGETS = {
    "tasks/lessons.md",
    "agent/DECISIONS.md",
    "agent/CURRENT_STATE.md",
    "domains/BUILDING.md",
    "domains/CONTENT.md",
    "domains/INVESTING.md",
    "domains/RESEARCH.md",
    "memory/projects/projects.md",
    "memory/projects/projects.json",
    "memory/hot/USER.md",
    "memory/hot/MEMORY.md",
}
TYPE_TARGETS = {
    "failure_pattern": "tasks/lessons.md",
    "workflow": "agent/DECISIONS.md",
    "preference": "memory/hot/USER.md",
    "project_fact": "memory/projects/projects.md",
    "current_state": "agent/CURRENT_STATE.md",
    "decision": "agent/DECISIONS.md",
}
SOURCE_GROUPS = (
    ("source_of_truth", "high", ("tasks", "agent", "domains", "memory/projects")),
    ("hot_memory", "medium", ("memory/hot",)),
)
TEXT_SUFFIXES = {".md", ".txt", ".json"}
EXPLICIT_MARKERS = (
    "以后",
    "请记住",
    "记住",
    "我纠正",
    "纠正你",
    "必须",
    "不能",
    "不要",
    "source-of-truth",
    "source of truth",
)
GUESS_MARKERS = ("可能", "也许", "大概", "我猜", "看起来", "probably", "maybe", "seems")
INIT_FIELDS = (
    "name",
    "language",
    "work_type",
    "communication_style",
    "projects",
    "confirmation_rules",
    "never_store",
)
INIT_DEFAULTS = {
    "name": "User",
    "language": "中文",
    "work_type": "independent builder",
    "communication_style": "Conclusion first, plain language, ask when uncertain.",
    "projects": ["First Project"],
    "confirmation_rules": ["public send", "production deploy", "database migration", "destructive action"],
    "never_store": ["secrets", "API keys", "tokens", "webhook URLs", "database URLs", "private keys", "raw sessions"],
}
AGENT_BRIDGE_TARGETS = {
    "codex": Path("AGENTS.md"),
    "claude": Path("CLAUDE.md"),
    "cursor": Path(".cursor/rules/journeymem.mdc"),
    "trae": Path(".trae/rules/journeymem.md"),
    "generic": Path("JOURNEYMEM.md"),
}
AGENT_INSTALL_TARGETS = ("codex", "claude", "cursor", "trae", "generic")
CODEX_MARKETPLACE_NAME = "journeymem-local"
CODEX_PLUGIN_NAME = "journeymem"
CODEX_PLUGIN_VERSION = "0.1.1"
CODEX_CONFIG_BEGIN = "# BEGIN JourneyMem plugin"
CODEX_CONFIG_END = "# END JourneyMem plugin"
CODEX_COMMANDS = ("memory", "memory-new", "memory-connect", "memory-backup")
AGENT_LABELS = {
    "codex": "Codex",
    "claude": "Claude Code",
    "cursor": "Cursor",
    "trae": "TRAE Work",
    "generic": "Generic Agent",
    "shell": "Shell",
}
BACKUP_EXCLUDED_PARTS = {".git", "__pycache__", ".venv", "venv", "node_modules"}
BACKUP_EXCLUDED_PREFIXES = (
    "memory/runtime",
    "memory/history/runtime",
    "content/data/memory-benchmark/runs",
)
BACKUP_EXCLUDED_SUFFIXES = {".sqlite", ".sqlite3", ".db", ".db-wal", ".db-shm"}
REQUIRED_MEMORY_LIBRARY_FILES = (
    "AGENTS.md",
    "ONBOARDING.md",
    "memory/hot/USER.md",
    "memory/hot/MEMORY.md",
)
REGISTRY_VERSION = 1


@dataclass
class MemoryRecord:
    memory_id: str
    content: str
    type: str
    source_event: str
    first_seen_at: str
    last_seen_at: str
    status: str
    target: str
    explicit: bool
    reusable: bool
    fresh: bool
    session_id: str


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def memory_script() -> Path:
    return Path(__file__).resolve().with_name("memory")


def journeymem_home(home: Path | None = None) -> Path:
    if home is not None:
        return home.expanduser() / ".journeymem"
    configured = os.environ.get("JOURNEYMEM_HOME", "").strip()
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".journeymem"


def default_library_root(home: Path | None = None) -> Path:
    return journeymem_home(home) / "libraries/default"


def user_default_root() -> Path:
    return default_library_root()


def registry_path(home: Path | None = None) -> Path:
    return journeymem_home(home) / "registry.json"


def is_memory_library(root: Path) -> bool:
    return all((root / rel).is_file() for rel in REQUIRED_MEMORY_LIBRARY_FILES)


def load_registry(home: Path | None = None) -> dict:
    path = registry_path(home)
    if not path.exists():
        return {"version": REGISTRY_VERSION, "default_library": None, "libraries": [], "agents": {}}
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"version": REGISTRY_VERSION, "default_library": None, "libraries": [], "agents": {}}
    if not isinstance(loaded, dict):
        return {"version": REGISTRY_VERSION, "default_library": None, "libraries": [], "agents": {}}
    loaded.setdefault("version", REGISTRY_VERSION)
    loaded.setdefault("default_library", None)
    loaded.setdefault("libraries", [])
    loaded.setdefault("agents", {})
    return loaded


def save_registry(home: Path | None, registry: dict) -> None:
    path = registry_path(home)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def register_library(home: Path | None, root: Path, name: str = "default") -> None:
    registry = load_registry(home)
    root_text = str(root.expanduser().resolve())
    now = now_iso()
    libraries = [item for item in registry.get("libraries", []) if item.get("path") != root_text and item.get("name") != name]
    libraries.append({"name": name, "path": root_text, "created_at": now, "last_used_at": now})
    registry["version"] = REGISTRY_VERSION
    registry["default_library"] = root_text if name == "default" or not registry.get("default_library") else registry["default_library"]
    registry["libraries"] = libraries
    registry.setdefault("agents", {})
    save_registry(home, registry)


def valid_registry_libraries(home: Path | None = None) -> list[dict]:
    registry = load_registry(home)
    items: list[dict] = []
    seen: set[str] = set()

    def add_candidate(name: str, root: Path, *, at_front: bool = False) -> None:
        key = str(root.resolve()) if root.exists() else str(root)
        if key in seen or not is_memory_library(root):
            return
        seen.add(key)
        item = {"name": name, "path": root}
        if at_front:
            items.insert(0, item)
        else:
            items.append(item)

    for item in registry.get("libraries", []):
        path_text = item.get("path")
        if not path_text:
            continue
        root = Path(path_text).expanduser()
        add_candidate(item.get("name") or root.name, root)
    default_text = registry.get("default_library")
    if default_text:
        default = Path(default_text).expanduser()
        add_candidate("default", default, at_front=True)
    fallback = default_library_root(home)
    add_candidate("default", fallback, at_front=True)
    for name, root in local_memory_library_candidates(home):
        add_candidate(name, root)
    return items


def local_memory_library_candidates(home: Path | None = None) -> list[tuple[str, Path]]:
    """Return narrow local fallback paths without scanning the user's folders."""
    candidates: list[tuple[str, Path]] = []
    if home is None:
        for env_name in ("JOURNEYMEM_LIBRARY", "JOURNEYMEM_ROOT"):
            value = os.environ.get(env_name, "").strip()
            if value:
                candidates.append((env_name.lower(), Path(value).expanduser()))
        candidates.append(("package", repo_root()))
    user_home = home.expanduser() if home is not None else Path.home()
    candidates.extend(
        [
            ("Agent Memory", user_home / "Documents/Agent Memory"),
            ("JourneyMem", user_home / "Documents/JourneyMem"),
            ("JourneyMem", user_home / "Documents/JourneyMem Library"),
            ("JourneyMem", user_home / "JourneyMem"),
            ("JourneyMem", user_home / "JourneyMem Library"),
            ("Agent Memory", user_home / "Agent Memory"),
        ]
    )
    return candidates


def choose_registry_library(home: Path | None, library: str | None, library_index: int | None) -> tuple[Path | None, str, list[dict]]:
    candidates = valid_registry_libraries(home)
    if library:
        requested = Path(library).expanduser()
        for item in candidates:
            if item["name"] == library or item["path"] == requested or str(item["path"]) == library:
                return item["path"], "selected", candidates
        return None, "missing_requested", candidates
    if library_index is not None:
        if 1 <= library_index <= len(candidates):
            return candidates[library_index - 1]["path"], "selected", candidates
        return None, "invalid_index", candidates
    if len(candidates) == 1:
        return candidates[0]["path"], "found", candidates
    if len(candidates) > 1:
        return None, "multiple", candidates
    return None, "none", candidates


def runtime_root(root: Path) -> Path:
    return root / "memory/runtime"


def session_path(root: Path, session_id: str) -> Path:
    return runtime_root(root) / "session_cache" / f"{safe_slug(session_id)}.jsonl"


def audit_path(root: Path) -> Path:
    return runtime_root(root) / "audit.jsonl"


def deprecated_path(root: Path) -> Path:
    return runtime_root(root) / "deprecated.jsonl"


def safe_slug(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", text).strip("-")
    return slug[:80] or "default"


def memory_id_for(content: str, target: str) -> str:
    digest = hashlib.sha1(f"{target}\n{normalize_content(content)}".encode("utf-8")).hexdigest()[:12]
    return f"mem-{digest}"


def normalize_content(text: str) -> str:
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    text = text.replace("。", "")
    return text


def append_jsonl(path: Path, item: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, items: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in items)
    path.write_text(text, encoding="utf-8")


def load_init_answers(args: argparse.Namespace) -> dict:
    answers = dict(INIT_DEFAULTS)
    if args.answers:
        loaded = json.loads(args.answers.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict):
            raise ValueError("--answers must be a JSON object")
        answers.update({key: loaded[key] for key in INIT_FIELDS if key in loaded})
    for key in ("name", "language", "work_type", "communication_style"):
        value = getattr(args, key)
        if value:
            answers[key] = value
    if args.project:
        answers["projects"] = args.project
    if args.confirmation_rule:
        answers["confirmation_rules"] = args.confirmation_rule
    if args.never_store:
        answers["never_store"] = args.never_store
    if sys.stdin.isatty() and args.interactive:
        answers = prompt_for_missing_answers(answers)
    return normalize_init_answers(answers)


def prompt_for_missing_answers(answers: dict) -> dict:
    prompts = {
        "name": "Step 1/7 - What should Agents call you? Example: Alex / Sam / your nickname",
        "language": "Step 2/7 - What language should Agents use by default? Example: English / Chinese",
        "work_type": "Step 3/7 - What kind of work should Agents help with? Example: indie product builder / code and bugs / research and writing",
        "communication_style": "Step 5/7 - How should Agents communicate with you? Example: conclusion first, concise, ask before risky actions",
    }
    updated = dict(answers)
    for key, prompt in prompts.items():
        current = str(updated.get(key, "")).strip()
        value = input(f"{prompt} [{current}]: ").strip()
        if value:
            updated[key] = value
    for key, prompt in (
        ("projects", "Step 4/7 - Current projects and optional workspace, comma-separated. Example: Example SaaS | ~/projects/example-saas"),
        ("confirmation_rules", "Step 6/7 - Actions that require confirmation, comma-separated. Example: public send, production deploy, delete files"),
        ("never_store", "Step 7/7 - Things memory must never store, comma-separated. Example: secrets, customer data, raw sessions"),
    ):
        current = ", ".join(project_display(project) for project in normalize_projects(updated.get(key))) if key == "projects" else ", ".join(ensure_list(updated.get(key)))
        value = input(f"{prompt} [{current}]: ").strip()
        if value:
            updated[key] = [item.strip() for item in value.split(",") if item.strip()]
    return updated


def normalize_init_answers(answers: dict) -> dict:
    normalized = dict(INIT_DEFAULTS)
    normalized.update(answers)
    for key in ("name", "language", "work_type", "communication_style"):
        normalized[key] = str(normalized.get(key) or INIT_DEFAULTS[key]).strip()
    normalized["projects"] = normalize_projects(normalized.get("projects"))
    for key in ("confirmation_rules", "never_store"):
        values = ensure_list(normalized.get(key))
        normalized[key] = values or list(INIT_DEFAULTS[key])
    return normalized


def ensure_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    if not text:
        return []
    return [item.strip() for item in re.split(r"[,;\n]+", text) if item.strip()]


def bullet_lines(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def normalize_projects(value: object) -> list[dict]:
    if isinstance(value, dict):
        raw_projects = [value]
    else:
        raw_projects = value if isinstance(value, list) else ensure_list(value)
    projects: list[dict] = []
    for item in raw_projects:
        if isinstance(item, dict):
            name = str(item.get("name") or item.get("title") or "").strip()
            workspace = str(item.get("workspace") or item.get("path") or "").strip()
        else:
            text = str(item).strip()
            if "|" in text:
                name, workspace = [part.strip() for part in text.split("|", 1)]
            else:
                name, workspace = text, ""
        if not name:
            continue
        project = {
            "name": name,
            "workspace": workspace,
            "workspace_status": workspace_status(workspace),
        }
        projects.append(project)
    if projects:
        return projects
    return normalize_projects(INIT_DEFAULTS["projects"])


def workspace_status(workspace: str) -> str:
    if not workspace:
        return "not_provided"
    return "verified_at_init" if Path(workspace).expanduser().exists() else "provided_unverified"


def project_display(project: dict) -> str:
    workspace = project.get("workspace", "")
    return f"{project['name']} | {workspace}" if workspace else project["name"]


def project_markdown(projects: list[dict]) -> str:
    lines: list[str] = []
    for project in projects:
        lines.append(f"- {project['name']}")
        if project["workspace"]:
            lines.append(f"  - workspace: {project['workspace']}")
            lines.append(f"  - workspace_status: {project['workspace_status']}")
        else:
            lines.append("  - workspace: not provided")
    return "\n".join(lines)


def bridge_target_for(agent: str, workspace: Path | None, explicit_target: Path | None, root: Path) -> Path:
    if explicit_target:
        return explicit_target.expanduser().resolve()
    if workspace:
        return (workspace.expanduser() / AGENT_BRIDGE_TARGETS[agent]).resolve()
    return (root / "memory/agents" / f"{agent}.md").resolve()


def detect_agent() -> str | None:
    explicit = os.environ.get("AGENT_MEMORY_AGENT", "").strip().lower()
    if explicit in AGENT_BRIDGE_TARGETS:
        return explicit
    env = {key.upper(): value for key, value in os.environ.items() if value}
    if any(key.startswith("CODEX") for key in env):
        return "codex"
    if any(key.startswith("CLAUDE") for key in env):
        return "claude"
    if any("CURSOR" in key or "CURSOR" in value.upper() for key, value in env.items()):
        return "cursor"
    if any("TRAE" in key or "TRAE" in value.upper() for key, value in env.items()):
        return "trae"
    return None


def agent_bridge_text(root: Path, agent: str) -> str:
    label = AGENT_LABELS[agent]
    root_text = str(root)
    memory_cmd = shlex.quote(str(memory_script()))
    root_arg = shlex.quote(root_text)
    return f"""# JourneyMem Bridge

This {label} workspace uses a shared JourneyMem memory library.

Runtime root:

```text
{root_text}
```

Read first:

```text
{root_text}/AGENTS.md
-> {root_text}/ONBOARDING.md
-> {root_text}/memory/hot/USER.md
-> {root_text}/memory/hot/MEMORY.md
-> task-specific source-of-truth files only when needed
```

This bridge is a pointer only. Do not copy user profile, project facts, hot memory, session cache, history, or deprecated audit into this workspace file.

Authority:

- Markdown files under the runtime root are the source of truth.
- Hot memory is startup cache, not final truth.
- Platform memory and chat history are recall/evidence only.
- Conflicts are resolved by checking source-of-truth files in the runtime root.
- New durable memory must go through `remember -> recall -> improve -> forget`.

Useful commands:

```bash
{memory_cmd} --root {root_arg} recall --query "<query>" --context-only
{memory_cmd} --root {root_arg} remember --session-id "<session>" --text "<explicit user correction>"
{memory_cmd} --root {root_arg} improve --session-id "<session>"
{memory_cmd} --root {root_arg} forget --instruction "<user correction>"
```

Safety:

- Never store or print secrets, API keys, tokens, webhook URLs, database URLs, private keys, raw sessions, customer data, account data, cookies, or passwords.
- Do not read the full runtime by default.
- Do not read project workspaces unless the task specifically requires the relevant source files.
"""


def agent_connection_text(root: Path, agent: str) -> str:
    label = AGENT_LABELS[agent]
    root_text = str(root)
    memory_cmd = shlex.quote(str(memory_script()))
    root_arg = shlex.quote(root_text)
    return f"""# JourneyMem Connection

This {label} workspace uses this shared memory library:

```text
{root_text}
```

Read first:

```text
{root_text}/AGENTS.md
-> {root_text}/ONBOARDING.md
-> {root_text}/memory/hot/USER.md
-> {root_text}/memory/hot/MEMORY.md
-> task-specific authoritative files only when needed
```

This file is a pointer only. Do not copy user profile, project facts, hot memory, observed memory, history, or audit records into this workspace file.

Authority:

- Markdown files in the memory library are the final record.
- Hot memory is only a startup summary.
- Platform memory and chat history are recall/evidence only.
- Conflicts are resolved by checking the authoritative Markdown files.
- New durable memory must go through `remember -> recall -> improve -> forget`.

Useful commands:

```bash
{memory_cmd} --root {root_arg} recall --query "<query>" --context-only
{memory_cmd} --root {root_arg} remember --session-id "<session>" --text "<explicit user correction>"
{memory_cmd} --root {root_arg} improve --session-id "<session>"
{memory_cmd} --root {root_arg} forget --instruction "<user correction>"
```

Safety:

- Never store or print secrets, API keys, tokens, webhook URLs, database URLs, private keys, raw sessions, customer data, account data, cookies, or passwords.
- Do not load every file by default.
- Do not read project folders unless the task specifically requires the relevant source files.
"""


def command_helper_text(root: Path) -> str:
    memory_cmd = shlex.quote(str(memory_script()))
    root_arg = shlex.quote(str(root))
    return f"""# JourneyMem Commands

Use these shortcuts when the user asks for JourneyMem setup, connection, or backup.

Stable text entry for all Agents:

- `memory`: show the first-use menu with two choices: create a new memory library or connect this Agent to an existing memory library.
- `memory new`: create a memory library for a new user. Ask one guided question at a time.
- `memory connect`: connect this Agent to an existing memory library.
- `memory backup`: create a zip backup. This is an available command, not a main first-use branch.
- `$journeymem`: when explicit skill references are supported, treat this as the same as `memory`.

Slash-capable Agents may also support:

- `/memory`: show the menu.
- `/memory new`: create a memory library for a new user. Ask one guided question at a time.
- `/memory connect`: connect this Agent to an existing memory library.
- `/memory backup`: create a zip backup.

Some Agents may not show custom slash commands in their command picker. Treat `memory`, `memory new`, `memory connect`, `memory backup`, and `$journeymem` as the reliable entry points and run the matching command below.

Hard first-response rule:

- If the current user message is exactly `memory`, `$journeymem`, `/memory`, or asks to use JourneyMem, show the first-use menu immediately.
- The visible first-use menu must keep these command labels exactly in English: `memory new`, `memory connect`, and `memory backup`.
- Do not translate, remove, or paraphrase the command labels in the first-use menu.
- Do not read files, inspect folders, browse repository structure, or explain existing memory contents before showing the menu.

GitHub URL install-source fallback:

- Treat the JourneyMem GitHub URL as an install source, not as a generic codebase task.
- If the user gives `https://github.com/ivorywanj/agent-memory-starter-kit`, install or activate the JourneyMem skill/helper first when possible.
- Do not clone, inspect folder structure, summarize scripts, or ask "what do you want to do with this repo?" before install/menu.
- If the environment has already cloned the repo, do not explore it. Use its installer/helper and show the JourneyMem menu.
- If the user only asks you to clone this repo or run `git clone ...` and `cd agent-memory-starter-kit`, do not infer that they want `memory new`.
- After install, activation, clone, or cd, stop and ask the two-choice first-use question: create a new memory library or connect this Agent to an existing memory library.
- Run `memory new` only after the user chooses create/new. Run `memory connect` only after the user chooses connect/existing.

## Response Style

Keep the visible response short and user-facing. Do not show internal analysis, setup strategy, repository status, implementation notes, temporary answer-file strategy, batch setup details, or a full questionnaire.

Forbidden visible patterns:

- Repository/setup progress narration.
- Temporary answer-file or batch setup strategy.
- A full list of all setup questions before the first answer.
- A default-vs-manual setup choice.
- Instructions to manually edit memory files.

For `memory new`:

- Start by saying you will help create the memory library.
- Ask exactly one question at a time.
- First question: "What should Agents call you?"
- Do not ask where to store the memory library; use the default location.
- Include 1 to 3 short examples when helpful.
- Wait for the user's answer before asking the next question.

For `memory connect`:

- Say this will connect the current Agent to an existing memory library.
- First run `memory connect`; do not ask for a folder path before checking the local JourneyMem registry.
- For same-machine sharing, say no import is needed when an existing library is found.
- Detection rule: a confident memory library candidate must contain `AGENTS.md`, `ONBOARDING.md`, `memory/hot/USER.md`, and `memory/hot/MEMORY.md`.
- Detection order: check `~/.journeymem/registry.json`, then the default JourneyMem library path, then explicit user-provided backup/folder inputs. Do not broadly scan unrelated user folders.
- If exactly one confident local candidate is found, connect automatically and do not ask for a folder path.
- If multiple candidates are found, show numbered choices.
- If no local memory library is found, ask for a memory backup file from another computer or guide the user to `memory new`.
- Ask for only one missing input at a time.
- Do not say the memory will be imported, migrated, or copied into this Agent workspace.
- End with a short connection summary.

For `memory backup`:

- Say this will create a zip backup.
- Ask for only one missing input at a time.
- Do not ask which memory library to back up when the current installed memory library is known.
- If a question is needed, ask where to save the zip backup. You can say: "You can also say 'use the default backup folder'."
- Do not say backup connects, imports, restores, switches, or initializes a memory library.
- End with the backup file path and what was excluded.

## Commands To Run

Preferred:

```bash
memory
memory new
memory connect
memory backup
```

Fallback if `memory` is not on PATH:

```bash
{memory_cmd}
{memory_cmd} new
{memory_cmd} --root {root_arg} connect
{memory_cmd} --root {root_arg} backup
```

If the user is new only because they just cloned the repo, do not start `memory new` automatically. Ask the two-choice first-use question first.
If the user chooses create/new, start with `memory new` or `/memory new` where slash commands are supported.
If the user chooses connect/existing, start with `memory connect` or `/memory connect` where slash commands are supported.
If the user invokes `$journeymem`, treat it as `memory` and show the menu.
Do not ask the user to hand-edit memory files.
Do not store or print secrets.
"""


def codex_skill_text(root: Path) -> str:
    helper = command_helper_text(root)
    return f"""---
name: journeymem
description: Use when the user says JourneyMem, $journeymem, memory, memory new, memory connect, memory backup, gives the JourneyMem GitHub URL as an install source, or asks to set up, connect, share, or back up a JourneyMem library.
---

# JourneyMem

## When To Use

Use this skill when the user says `JourneyMem`, `$journeymem`, `memory`, `memory new`, `memory connect`, `memory backup`, gives the JourneyMem GitHub URL as an install source, or asks to set up, connect, share, or back up a JourneyMem library.

## Instructions

{helper}
"""


def codex_command_text(root: Path, command: str) -> str:
    memory_cmd = shlex.quote(str(memory_script()))
    root_arg = shlex.quote(str(root))
    if command == "memory":
        return f"""---
description: Show JourneyMem menu or run new/connect/backup
argument-hint: [new|connect|backup]
allowed-tools: Bash
---

# /memory

The user invoked this command with: `$ARGUMENTS`

Route the request exactly:

- Empty arguments: run `{memory_cmd}`.
- `new`: run `{memory_cmd} new`.
- `connect`: run `{memory_cmd} --root {root_arg} connect`.
- `backup`: run `{memory_cmd} --root {root_arg} backup`.

If arguments are unclear, show the two first-use choices (`memory new` and `memory connect`) and mention `memory backup` as a separate available command. Do not invent another command.
Follow the response style rules in the JourneyMem skill/helper text. Do not expose internal setup steps. Do not ask the user to hand-edit memory files. Do not store or print secrets.
"""

    command_map = {
        "memory-new": f"{memory_cmd} new",
        "memory-connect": f"{memory_cmd} --root {root_arg} connect",
        "memory-backup": f"{memory_cmd} --root {root_arg} backup",
    }
    descriptions = {
        "memory-new": "Create a memory library",
        "memory-connect": "Connect this Agent to a memory library",
        "memory-backup": "Back up a memory library",
    }
    display = "/" + command.replace("-", " ")
    return f"""---
description: {descriptions[command]}
argument-hint: [optional details]
allowed-tools: Bash
---

# {display}

Run this command:

```bash
{command_map[command]}
```

Follow the response style rules in the JourneyMem skill/helper text:

- `memory new`: ask exactly one question at a time and do not show internal setup steps.
- `memory connect`: first check the local JourneyMem registry/default path; if one valid local library is found, connect without asking for a folder path. If none is found, ask for a backup zip from another computer or guide `memory new`.
- `memory backup`: say it creates a zip backup; ask where to save it and say the user can use the default backup folder; do not mix backup with connect, import, restore, switch, or initialization.

Do not ask the user to hand-edit memory files. Do not store or print secrets.
"""


def codex_plugin_manifest_text() -> str:
    manifest = {
        "name": CODEX_PLUGIN_NAME,
        "version": CODEX_PLUGIN_VERSION,
        "description": "JourneyMem shortcuts for creating, connecting, and backing up a local memory library.",
        "author": {"name": "JourneyMem contributors"},
        "repository": "https://github.com/ivorywanj/agent-memory-starter-kit",
        "license": "MIT",
        "keywords": ["memory", "agent", "onboarding", "local-first"],
        "skills": "./skills/",
        "interface": {
            "displayName": "JourneyMem",
            "shortDescription": "Local-first memory shortcuts for coding agents",
            "longDescription": "Create, connect, and back up a local memory library for Codex and other coding agents.",
            "developerName": "JourneyMem contributors",
            "category": "Developer Tools",
            "capabilities": ["Interactive", "Read", "Write"],
            "websiteURL": "https://github.com/ivorywanj/agent-memory-starter-kit",
            "defaultPrompt": ["Set up JourneyMem"],
            "brandColor": "#10A37F",
        },
    }
    return json.dumps(manifest, indent=2, sort_keys=True) + "\n"


def codex_marketplace_manifest_text() -> str:
    manifest = {
        "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
        "name": CODEX_MARKETPLACE_NAME,
        "description": "Local marketplace for JourneyMem.",
        "owner": {"name": "JourneyMem contributors"},
        "plugins": [
            {
                "name": CODEX_PLUGIN_NAME,
                "description": "JourneyMem shortcuts for creating, connecting, and backing up a local memory library.",
                "author": {"name": "JourneyMem contributors"},
                "category": "development",
                "source": f"./plugins/{CODEX_PLUGIN_NAME}",
                "homepage": "https://github.com/ivorywanj/agent-memory-starter-kit",
            }
        ],
    }
    return json.dumps(manifest, indent=2, sort_keys=True) + "\n"


def claude_command_text(root: Path, command: str) -> str:
    memory_cmd = shlex.quote(str(memory_script()))
    root_arg = shlex.quote(str(root))
    command_map = {
        "memory": f"{memory_cmd}",
        "memory-new": f"{memory_cmd} new",
        "memory-connect": f"{memory_cmd} --root {root_arg} connect",
        "memory-backup": f"{memory_cmd} --root {root_arg} backup",
    }
    display = "/" + command.replace("-", " ")
    return f"""# {display}

Run:

```bash
{command_map[command]}
```

Follow the response style rules in the JourneyMem command helper:

- `memory new`: ask exactly one question at a time and do not show internal setup steps.
- `memory connect`: first check the local JourneyMem registry/default path; if one valid local library is found, connect without asking for a folder path. If none is found, ask for a backup zip from another computer or guide `memory new`.
- `memory backup`: say it creates a zip backup; ask where to save it and say the user can use the default backup folder; do not mix backup with connect, import, restore, switch, or initialization.

Do not ask the user to hand-edit memory files. Do not store or print secrets.
"""


def cursor_rule_text(root: Path) -> str:
    return f"""---
description: JourneyMem shortcuts
alwaysApply: true
---

{command_helper_text(root)}
"""


def trae_rule_text(root: Path) -> str:
    return f"""# JourneyMem TRAE Work Commands

Use this file when the user says `memory`, `memory new`, `memory connect`, or `memory backup`.

First response rule for TRAE Work:

- If the user says `memory`, `$journeymem`, `/memory`, or asks to use JourneyMem, respond with the first-use menu.
- Keep the command labels exactly as `memory new`, `memory connect`, and `memory backup`; do not translate or paraphrase them.

```text
I can help you use JourneyMem.

What do you want to do?
1. memory new - Create a memory library
2. memory connect - Connect this Agent to an existing memory library

Other command:
- memory backup - Back up a memory library
```

Treat the JourneyMem GitHub repo URL as an install source, not as a codebase task. Do not clone, inspect, or summarize the repo before install/menu. Start from the command flow below.

{command_helper_text(root)}
"""


def generic_command_text(root: Path) -> str:
    return command_helper_text(root)


def codex_marketplace_dir(home: Path) -> Path:
    return home / ".codex/journeymem-marketplace"


def codex_plugin_root(home: Path) -> Path:
    return codex_marketplace_dir(home) / "plugins" / CODEX_PLUGIN_NAME


def codex_config_block(home: Path) -> str:
    source = str(codex_marketplace_dir(home))
    return f"""{CODEX_CONFIG_BEGIN}

[marketplaces.{CODEX_MARKETPLACE_NAME}]
source_type = "local"
source = "{source}"

[plugins."{CODEX_PLUGIN_NAME}@{CODEX_MARKETPLACE_NAME}"]
enabled = true

{CODEX_CONFIG_END}
"""


def upsert_codex_config(home: Path, force: bool) -> Path:
    config = home / ".codex/config.toml"
    block = codex_config_block(home)
    config.parent.mkdir(parents=True, exist_ok=True)
    existing = config.read_text(encoding="utf-8") if config.exists() else ""
    if CODEX_CONFIG_BEGIN in existing and CODEX_CONFIG_END in existing:
        if not force:
            return config
        pattern = re.compile(re.escape(CODEX_CONFIG_BEGIN) + r".*?" + re.escape(CODEX_CONFIG_END), re.S)
        updated = pattern.sub(block.rstrip(), existing)
    else:
        updated = existing.rstrip() + "\n\n" + block if existing.strip() else block
    config.write_text(updated.rstrip() + "\n", encoding="utf-8")
    return config


def find_codex_cli() -> Path | None:
    explicit = os.environ.get("CODEX_CLI_PATH", "").strip()
    candidates = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    found = shutil.which("codex")
    if found:
        candidates.append(Path(found))
    candidates.append(Path("/Applications/Codex.app/Contents/Resources/codex"))
    for candidate in candidates:
        if candidate.exists() and os.access(candidate, os.X_OK):
            return candidate
    return None


def codex_plugin_selector() -> str:
    return f"{CODEX_PLUGIN_NAME}@{CODEX_MARKETPLACE_NAME}"


def install_codex_plugin_with_cli(home: Path) -> tuple[str, str]:
    if home.resolve() != Path.home().resolve():
        return "skipped_custom_home", "Codex CLI install skipped for non-default --home."
    cli = find_codex_cli()
    if not cli:
        return "skipped_no_cli", f"Codex CLI not found. Run: codex plugin add {codex_plugin_selector()}"
    env = os.environ.copy()
    env["CODEX_HOME"] = str(home / ".codex")
    completed = subprocess.run(
        [str(cli), "plugin", "add", codex_plugin_selector()],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        env=env,
    )
    output = completed.stdout.strip()
    if completed.returncode == 0:
        return "installed", output
    if "already" in output.lower() and "installed" in output.lower():
        return "already_installed", output
    return "failed", output


@dataclass
class InstallFile:
    agent: str
    path: Path
    content: str
    mode: int | None = None


def memory_shell_shim_text(root: Path) -> str:
    python_cmd = shlex.quote(os.environ.get("AGENT_MEMORY_PYTHON", sys.executable or "python3"))
    memory_cmd = shlex.quote(str(memory_script()))
    root_arg = shlex.quote(str(root))
    return f"""#!/bin/sh
export PYTHONDONTWRITEBYTECODE=1
exec {python_cmd} {memory_cmd} --root {root_arg} "$@"
"""


def shell_shim_path(home: Path) -> Path:
    return home / ".local/bin/memory"


def shared_install_files(root: Path, home: Path) -> list[InstallFile]:
    return [InstallFile("shell", shell_shim_path(home), memory_shell_shim_text(root), 0o755)]


def bin_dir_on_path(path: Path) -> bool:
    target = path.expanduser().resolve()
    for entry in os.environ.get("PATH", "").split(os.pathsep):
        if not entry:
            continue
        try:
            if Path(entry).expanduser().resolve() == target:
                return True
        except OSError:
            continue
    return False


def install_files_for(root: Path, agent: str, workspace: Path, home: Path) -> list[InstallFile]:
    if agent == "codex":
        plugin_root = codex_plugin_root(home)
        files = [
            InstallFile(agent, codex_marketplace_dir(home) / ".claude-plugin/marketplace.json", codex_marketplace_manifest_text()),
            InstallFile(agent, home / ".codex/skills/journeymem/SKILL.md", codex_skill_text(root)),
            InstallFile(agent, plugin_root / ".codex-plugin/plugin.json", codex_plugin_manifest_text()),
            InstallFile(agent, plugin_root / "skills/journeymem/SKILL.md", codex_skill_text(root)),
        ]
        files.extend(InstallFile(agent, plugin_root / "commands" / f"{command}.md", codex_command_text(root, command)) for command in CODEX_COMMANDS)
        return files
    if agent == "claude":
        command_dir = workspace / ".claude/commands"
        return [
            InstallFile(agent, command_dir / "memory.md", claude_command_text(root, "memory")),
            InstallFile(agent, command_dir / "memory-new.md", claude_command_text(root, "memory-new")),
            InstallFile(agent, command_dir / "memory-connect.md", claude_command_text(root, "memory-connect")),
            InstallFile(agent, command_dir / "memory-backup.md", claude_command_text(root, "memory-backup")),
        ]
    if agent == "cursor":
        return [InstallFile(agent, workspace / ".cursor/rules/journeymem-commands.mdc", cursor_rule_text(root))]
    if agent == "trae":
        text = trae_rule_text(root)
        return [
            InstallFile(agent, workspace / ".trae/rules/journeymem-commands.md", text),
            InstallFile(agent, workspace / "TRAE_MEMORY.md", text),
        ]
    if agent == "generic":
        return [InstallFile(agent, workspace / "JOURNEYMEM_COMMANDS.md", generic_command_text(root))]
    raise ValueError(f"unsupported agent: {agent}")


def command_install(args: argparse.Namespace) -> int:
    root = args.root
    workspace = (args.workspace or Path.cwd()).expanduser().resolve()
    home = (args.home or Path.home()).expanduser().resolve()
    if args.agent == "auto":
        detected = detect_agent()
        agents = [detected] if detected in AGENT_INSTALL_TARGETS else list(AGENT_INSTALL_TARGETS)
    else:
        agents = list(AGENT_INSTALL_TARGETS) if args.agent == "all" else [args.agent]
    planned: list[InstallFile] = shared_install_files(root, home)
    for agent in agents:
        planned.extend(install_files_for(root, agent, workspace, home))
    combined = "\n".join(item.content + "\n" + str(item.path) for item in planned)
    findings = guard_text(root, combined)
    if findings:
        print(f"install_blocked: {findings[0].kind}")
        return 1
    existing = [item.path for item in planned if item.path.exists()]
    if existing and not args.force:
        print("install_blocked: target exists")
        for path in existing:
            print(str(path))
        print("Use --force to overwrite installed shortcuts.")
        return 1
    for item in planned:
        item.path.parent.mkdir(parents=True, exist_ok=True)
        item.path.write_text(item.content, encoding="utf-8")
        if item.mode is not None:
            item.path.chmod(item.mode)
    config_path = None
    codex_cli_status = None
    codex_cli_output = None
    if "codex" in agents:
        config_path = upsert_codex_config(home, args.force)
        codex_cli_status, codex_cli_output = install_codex_plugin_with_cli(home)
    installed_agents = ", ".join(AGENT_LABELS[agent] for agent in agents)
    print("JourneyMem shortcuts installed")
    print(f"Installed for: {installed_agents}")
    print(f"Workspace: {workspace}")
    print(f"Memory library: {root}")
    print("Text shortcut: memory")
    print("Text shortcuts: memory new, memory connect, memory backup")
    print("Shell command installed: memory")
    print("Skill-capable Agents: $journeymem")
    print("Slash-capable Agents: /memory, /memory new, /memory connect, /memory backup")
    print("Codex custom slash commands are best-effort; current Codex may not show plugin commands.")
    print("If your Agent does not show slash commands, use the text shortcuts above.")
    shim = shell_shim_path(home)
    shim_dir = shim.parent
    if bin_dir_on_path(shim_dir):
        print(f"- PATH: {shim_dir} is available")
    else:
        print(f"- PATH action: add {shim_dir} to PATH, then restart your Agent")
    if config_path:
        print(f"- Codex config: {config_path}")
    if codex_cli_status:
        print(f"- Codex plugin add: {codex_cli_status}")
        if codex_cli_output:
            print(codex_cli_output)
    for item in planned:
        print(f"- {AGENT_LABELS[item.agent]}: {item.path}")
    return 0


def write_agent_registry(root: Path, agent: str, target: Path, mode: str) -> None:
    registry = root / "memory/agents/registry.json"
    items = []
    if registry.exists():
        try:
            loaded = json.loads(registry.read_text(encoding="utf-8"))
            items = loaded.get("bridges", []) if isinstance(loaded, dict) else []
        except json.JSONDecodeError:
            items = []
    record = {
        "agent": agent,
        "target": str(target),
        "mode": mode,
        "updated_at": now_iso(),
        "source": "memory share",
    }
    items = [item for item in items if not (item.get("agent") == agent and item.get("target") == str(target))]
    items.append(record)
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text(json.dumps({"bridges": items}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def guard_text(root: Path, text: str) -> list[memory_guard.Finding]:
    with tempfile.TemporaryDirectory(prefix="journeymem-guard-") as tmp:
        probe = Path(tmp) / ".guard-probe.md"
        probe.write_text(text, encoding="utf-8")
        return memory_guard.scan_file(probe, root)


def public_template_files(answers: dict) -> dict[str, str]:
    projects = project_markdown(answers["projects"])
    confirmation_rules = bullet_lines(answers["confirmation_rules"])
    never_store = bullet_lines(answers["never_store"])
    first_project = answers["projects"][0]["name"]
    project_rows = [
        {
            "id": safe_slug(project["name"]).lower(),
            "name": project["name"],
            "workspace": project["workspace"],
            "workspace_status": project["workspace_status"],
            "status": "initialized",
            "source": "memory init",
        }
        for project in answers["projects"]
    ]
    return {
        "AGENTS.md": f"""# Agent Instructions

## Identity

- User name: {answers['name']}
- Preferred language: {answers['language']}
- Work type: {answers['work_type']}
- Communication style: {answers['communication_style']}

## Startup Path

Read only this compact path by default:

```text
AGENTS.md
-> ONBOARDING.md
-> memory/hot/USER.md
-> memory/hot/MEMORY.md
-> task-specific source-of-truth files only when needed
```

Do not load the full runtime, raw history, session cache, promotions, deprecated audit, or generated drafts at startup.

## Memory Authority

- Markdown source-of-truth files win over hot memory, history, platform memory, and session cache.
- Hot memory is a startup cache, not final truth.
- History and platform memory are recall/evidence only.
- New durable memory goes through `remember -> recall -> improve -> forget`.

## Safety

Never store or print secrets, API keys, tokens, webhook URLs, database URLs, private keys, cookies, passwords, raw sessions, account data, or customer data.

Actions requiring confirmation:

{confirmation_rules}

Things memory must never store:

{never_store}
""",
        "ONBOARDING.md": f"""# Onboarding

## 10-Minute Startup

1. Read `AGENTS.md`.
2. Read `memory/hot/USER.md`.
3. Read `memory/hot/MEMORY.md`.
4. Stop and route by task. Only read deeper source files when the task needs them.

## User

- Name: {answers['name']}
- Work type: {answers['work_type']}
- Preferred language: {answers['language']}
- Communication style: {answers['communication_style']}

## Current Projects

{projects}

## Memory Loop

```text
remember -> recall -> improve -> forget
```

- `remember` captures explicit facts, corrections, and tool/file evidence into session cache.
- `recall --context-only` returns evidence with source and authority tags.
- `improve` promotes, modifies, deprecates, rejects, or discards observed memory after gates.
- `forget` handles user corrections. Default is deprecate with rollback; permanent delete requires explicit user wording.

## First Response Check

After reading the startup path, answer:

1. Who is the user?
2. What is the current project entry point?
3. What files are source of truth?
4. What must never be stored?
5. What should be read only if the task needs it?
""",
        "CROSS_AGENT.md": f"""# Cross-Agent First Run

Use this prompt in Codex, Claude Code, Cursor, or any Agent that can read local files:

```text
Please read AGENTS.md, ONBOARDING.md, memory/hot/USER.md, and memory/hot/MEMORY.md first.
Do not read the full runtime by default.

Then answer:
1. Who is the user?
2. What is the source-of-truth order?
3. How do hot memory, history evidence, session cache, deprecated audit, and Markdown files differ?
4. What must never be stored or printed?
5. Which task-specific files would you read next only if needed?
```

## Share This Runtime

Generate pointer-only bridge files for Agent workspaces:

```bash
scripts/memory --root /path/to/this-runtime share --agent codex --workspace /path/to/project
scripts/memory --root /path/to/this-runtime share --agent claude --workspace /path/to/project
scripts/memory --root /path/to/this-runtime share --agent cursor --workspace /path/to/project
scripts/memory --root /path/to/this-runtime share --agent trae --workspace /path/to/project
```

Bridge files point Agents back to this runtime. They do not copy user profile, project facts, hot memory, history, or session cache.
""",
        "memory/hot/USER.md": f"""# USER

- Name: {answers['name']}
- Preferred language: {answers['language']}
- Work type: {answers['work_type']}
- Communication style: {answers['communication_style']}

## Current Projects

{projects}

## Confirmation Required

{confirmation_rules}

## Never Store

{never_store}
""",
        "memory/hot/MEMORY.md": f"""# MEMORY

## Startup

Use compact startup only:

```text
AGENTS.md -> ONBOARDING.md -> memory/hot/USER.md -> memory/hot/MEMORY.md
```

Then read task-specific source-of-truth files only when needed.

## Authority

- Source of truth: `agent/`, `domains/`, `memory/projects/`, `tasks/lessons.md`.
- Hot memory: startup summary/cache.
- History/platform memory: recall evidence only.
- Session cache/observed memory: short-term candidates only.
- Deprecated memory: blocked as fact; audit only.

## Memory Loop

```text
remember -> recall -> improve -> forget
```

Improve gates:

```text
Safe
Explicit
Reusable
Routed
Fresh
```

## Safety

Never store secrets, tokens, webhook URLs, database URLs, private keys, raw sessions, customer data, or account data.
""",
        "agent/CURRENT_STATE.md": f"""# Current State

Status: initialized by `memory init`.

## Active Projects

{projects}

## Current Focus

- Start with `{first_project}` unless the user gives a different task.
- Check freshness before treating project status as current.
""",
        "agent/DECISIONS.md": """# Decisions

- Markdown source-of-truth files beat hot memory, history evidence, platform memory, and session cache.
- Hot memory is a startup cache, not final truth.
- Durable memory updates must pass safety and improve gates before writing source-of-truth files.
""",
        "tasks/lessons.md": """# Lessons

- When claiming something is done or tested, verify real behavior, not only file existence.
- If unsure, say what is unknown and which source file or command would verify it.
""",
        "memory/projects/projects.md": f"""# Projects

{projects}
""",
        "memory/projects/projects.json": json.dumps({"projects": project_rows}, ensure_ascii=False, indent=2) + "\n",
        "memory/history/README.md": """# History

History search is recall/evidence only. It does not become long-term truth without improve gates and source routing.
""",
        "memory/inbox/README.md": """# Observed Memory Buffer

Internal compatibility directory. Users should not manage this manually. Use `memory remember` / `memory improve`.
""",
        "memory/promotions/README.md": """# Promotion Audit

Internal audit directory for durable memory changes. Users correct summaries; Agents maintain files.
""",
        "memory/agents/README.md": """# Agent Bridges

Use `memory share` to connect Codex, Claude Code, Cursor, or another local-file-reading Agent to this same runtime.

Bridge files are pointers only. They must not duplicate user profile, hot memory, project facts, session cache, history, or deprecated audit.
""",
    }


def command_init(args: argparse.Namespace) -> int:
    root = args.root
    answers = load_init_answers(args)
    files = public_template_files(answers)
    generated_text = "\n\n".join(files.values())
    findings = guard_text(root, generated_text)
    if findings:
        print(f"init_blocked: {findings[0].kind}")
        return 1
    existing = [rel for rel in files if (root / rel).exists()]
    if existing and not args.force:
        print("init_blocked: existing files")
        for rel in existing[:12]:
            print(f"- {rel}")
        if len(existing) > 12:
            print(f"- ... {len(existing) - 12} more")
        print("Use --force only when you intentionally want to overwrite generated starter files.")
        return 1
    created: list[str] = []
    overwritten: list[str] = []
    for rel, text in files.items():
        path = root / rel
        existed = path.exists()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        overwritten.append(rel) if existed else created.append(rel)
    home = getattr(args, "home", None)
    if home is not None or root == default_library_root(home):
        register_library(home, root, "default")
    print("Memory initialized")
    print("")
    print("Created:")
    for index, rel in enumerate(created[:8], 1):
        print(f"{index}. {rel}")
    if not created:
        print("- none")
    elif len(created) > 8:
        print(f"... {len(created) - 8} more")
    if overwritten:
        print("")
        print("Overwritten:")
        for index, rel in enumerate(overwritten[:8], 1):
            print(f"{index}. {rel}")
        if len(overwritten) > 8:
            print(f"... {len(overwritten) - 8} more")
    print("")
    print("No Markdown editing required. To correct anything, say: 第 1 条不对 / 删除第 2 条 / 第 3 条改成...")
    print("")
    print("Next Agent startup path:")
    print("AGENTS.md -> ONBOARDING.md -> memory/hot/USER.md -> memory/hot/MEMORY.md")
    return 0


def command_start(args: argparse.Namespace) -> int:
    choice = (args.choice or "").strip().lower()
    if not choice:
        print_memory_menu()
        return 0
    if choice in {"1", "n", "new", "start"}:
        init_args = argparse.Namespace(
            root=args.root or default_library_root(args.home),
            answers=args.answers,
            name=args.name,
            language=args.language,
            work_type=args.work_type,
            communication_style=args.communication_style,
            project=args.project,
            confirmation_rule=args.confirmation_rule,
            never_store=args.never_store,
            interactive=args.interactive,
            force=args.force,
            home=args.home,
        )
        return command_init(init_args)
    if choice in {"2", "c", "connect", "share"}:
        connect_args = argparse.Namespace(
            root=args.root,
            agent=args.agent,
            workspace=args.workspace,
            target=args.target,
            append=args.append,
            force=args.force,
            print_only=args.print_only,
            home=args.home,
            library=args.library,
            library_index=args.library_index,
            backup=args.backup,
        )
        return command_connect(connect_args)
    if choice in {"3", "b", "backup"}:
        default = default_library_root(args.home)
        backup_root = args.root or (default if is_memory_library(default) else repo_root())
        backup_args = argparse.Namespace(root=backup_root, output=args.output, backup_dir=args.backup_dir, home=args.home)
        return command_backup(backup_args)
    print("start_blocked: choose 1, 2, or 3")
    return 1


def print_memory_menu() -> None:
    print("What do you want to do?")
    print("1. memory new - Create a memory library")
    print("2. memory connect - Connect this Agent to an existing memory library")
    print("")
    print("Other command:")
    print("- memory backup - Back up a memory library")
    print("")
    print("Slash-capable Agents may also support:")
    print("- /memory")
    print("- /memory new")
    print("- /memory connect")
    print("- /memory backup")


def command_connect(args: argparse.Namespace) -> int:
    agent = args.agent or detect_agent()
    if not agent:
        print("connect_needs_agent")
        print("I could not identify the current Agent. Choose codex, claude, cursor, trae, or generic.")
        return 1
    home = getattr(args, "home", None)
    root = args.root
    restored = False
    found_existing = False
    if root is None:
        backup = getattr(args, "backup", None)
        if backup:
            root, restore_status = restore_backup_zip(backup.expanduser(), home, force=args.force)
            if root is None:
                print(f"connect_blocked: {restore_status}")
                return 1
            restored = True
        else:
            root, status, candidates = choose_registry_library(home, getattr(args, "library", None), getattr(args, "library_index", None))
            if root is None:
                if status == "multiple":
                    print("connect_needs_library_choice")
                    print("Choose a memory library:")
                    for index, item in enumerate(candidates, 1):
                        print(f"{index}. {item['name']} - {item['path']}")
                    print("Rerun with --library-index N.")
                elif status == "missing_requested":
                    print("connect_blocked: requested memory library was not found")
                elif status == "invalid_index":
                    print("connect_blocked: invalid library index")
                else:
                    print("connect_needs_memory_library")
                    print("No existing JourneyMem memory library was found on this computer.")
                    print("Provide a memory backup zip with --backup, or create one with memory new.")
                return 1
            found_existing = True
    root = root.expanduser().resolve()
    if not is_memory_library(root):
        print("connect_blocked: not a JourneyMem memory library")
        print("Required files: AGENTS.md, ONBOARDING.md, memory/hot/USER.md, memory/hot/MEMORY.md")
        return 1
    if found_existing and not args.print_only:
        register_library(home, root, "default" if root == default_library_root(home).resolve() else root.name)
    target = bridge_target_for(agent, args.workspace, args.target, root)
    content = agent_connection_text(root, agent)
    findings = guard_text(root, content + "\n" + str(target))
    if findings:
        print(f"connect_blocked: {findings[0].kind}")
        return 1
    if args.print_only:
        print(content)
        return 0
    if target.exists() and not args.force and not args.append:
        print("connect_blocked: target exists")
        print(str(target))
        print("Use --append to add a connection block or --force to overwrite.")
        return 1
    target.parent.mkdir(parents=True, exist_ok=True)
    mode = "created"
    if target.exists() and args.append:
        existing = target.read_text(encoding="utf-8")
        if "<!-- BEGIN AGENT MEMORY CONNECTION -->" in existing and not args.force:
            print("connect_blocked: connection already present")
            print(str(target))
            return 1
        text = existing.rstrip() + "\n\n<!-- BEGIN AGENT MEMORY CONNECTION -->\n" + content.rstrip() + "\n<!-- END AGENT MEMORY CONNECTION -->\n"
        target.write_text(text, encoding="utf-8")
        mode = "appended"
    else:
        target.write_text(content, encoding="utf-8")
        mode = "overwritten" if args.force else "created"
    write_agent_registry(root, agent, target, mode)
    if restored:
        print("Memory library restored from backup")
    elif found_existing:
        print("Found existing memory library")
    print("Current Agent connected")
    print(f"Agent: {AGENT_LABELS[agent]}")
    print(f"Connection file: {target}")
    print(f"Memory library: {root}")
    print("No profile, project facts, or long-term memory were copied into this workspace.")
    return 0


def should_backup_file(path: Path, root: Path) -> bool:
    rel = rel_path(path, root)
    if any(part in BACKUP_EXCLUDED_PARTS for part in path.parts):
        return False
    if path.name.startswith(".env") or "/.env" in f"/{rel}":
        return False
    if any(rel == prefix or rel.startswith(prefix + "/") for prefix in BACKUP_EXCLUDED_PREFIXES):
        return False
    if path.suffix in BACKUP_EXCLUDED_SUFFIXES:
        return False
    if rel.startswith("memory/hot/") and path.name.endswith(".draft.md"):
        return False
    return path.is_file()


def unsafe_backup_member(name: str) -> str | None:
    posix = PurePosixPath(name)
    if posix.is_absolute() or ".." in posix.parts or not name.strip():
        return "unsafe_path"
    rel = str(posix)
    if any(part in BACKUP_EXCLUDED_PARTS for part in posix.parts):
        return "blocked_part"
    if posix.name.startswith(".env") or "/.env" in f"/{rel}":
        return "secret_file"
    if any(rel == prefix or rel.startswith(prefix + "/") for prefix in BACKUP_EXCLUDED_PREFIXES):
        return "runtime_cache"
    if Path(posix.name).suffix in BACKUP_EXCLUDED_SUFFIXES:
        return "local_database"
    if rel.startswith("memory/hot/") and posix.name.endswith(".draft.md"):
        return "draft"
    return None


def validate_backup_zip(path: Path) -> tuple[bool, str, set[str]]:
    if not path.exists():
        return False, "backup_missing", set()
    try:
        with zipfile.ZipFile(path) as archive:
            names = {info.filename for info in archive.infolist() if not info.is_dir()}
            for info in archive.infolist():
                if info.is_dir():
                    continue
                reason = unsafe_backup_member(info.filename)
                if reason:
                    return False, f"blocked_member:{reason}:{info.filename}", names
    except zipfile.BadZipFile:
        return False, "backup_invalid_zip", set()
    missing = [rel for rel in REQUIRED_MEMORY_LIBRARY_FILES if rel not in names]
    if missing:
        return False, f"backup_missing_required:{missing[0]}", names
    return True, "ok", names


def restore_backup_zip(path: Path, home: Path | None, force: bool = False) -> tuple[Path | None, str]:
    ok, reason, _ = validate_backup_zip(path)
    if not ok:
        return None, reason
    target = default_library_root(home).expanduser()
    if target.exists() and not force:
        return None, "restore_target_exists"
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="journeymem-restore-", dir=str(target.parent)) as tmp:
        extracted = Path(tmp) / "library"
        extracted.mkdir()
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                member_target = extracted / info.filename
                member_target.parent.mkdir(parents=True, exist_ok=True)
                member_target.write_bytes(archive.read(info))
        findings = memory_guard.scan(memory_guard.DEFAULT_PATHS, extracted)
        if findings:
            return None, f"restore_safety_blocked:{findings[0].kind}"
        if target.exists():
            shutil.rmtree(target)
        shutil.move(str(extracted), str(target))
    register_library(home, target, "default")
    return target, "restored"


def default_backup_path(root: Path, backup_dir: Path | None) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target_dir = backup_dir.expanduser() if backup_dir else root.parent / "memory-backups"
    return target_dir / f"journeymem-{stamp}.zip"


def command_backup(args: argparse.Namespace) -> int:
    root = args.root
    findings = memory_guard.scan(memory_guard.DEFAULT_PATHS, root)
    if findings:
        print(f"backup_blocked: safety scan found {len(findings)} issue(s)")
        return 1
    output = (args.output.expanduser() if args.output else default_backup_path(root, args.backup_dir)).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    files = [path for path in sorted(root.rglob("*")) if should_backup_file(path, root)]
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, rel_path(path, root))
    print("Memory backup created")
    print(f"File: {output}")
    print(f"Files included: {len(files)}")
    print("Excluded: secrets, local session data, search indexes, raw runs, and drafts.")
    return 0


def command_share(args: argparse.Namespace) -> int:
    root = args.root
    target = bridge_target_for(args.agent, args.workspace, args.target, root)
    content = agent_bridge_text(root, args.agent)
    findings = guard_text(root, content + "\n" + str(target))
    if findings:
        print(f"share_blocked: {findings[0].kind}")
        return 1
    if args.print_only:
        print(content)
        return 0
    if target.exists() and not args.force and not args.append:
        print("share_blocked: target exists")
        print(str(target))
        print("Use --append to add a bridge block or --force to overwrite.")
        return 1
    target.parent.mkdir(parents=True, exist_ok=True)
    mode = "created"
    if target.exists() and args.append:
        existing = target.read_text(encoding="utf-8")
        if "<!-- BEGIN AGENT MEMORY BRIDGE -->" in existing and not args.force:
            print("share_blocked: bridge already present")
            print(str(target))
            return 1
        text = existing.rstrip() + "\n\n<!-- BEGIN AGENT MEMORY BRIDGE -->\n" + content.rstrip() + "\n<!-- END AGENT MEMORY BRIDGE -->\n"
        target.write_text(text, encoding="utf-8")
        mode = "appended"
    else:
        target.write_text(content, encoding="utf-8")
        mode = "overwritten" if args.force else "created"
    write_agent_registry(root, args.agent, target, mode)
    print("Shared memory bridge ready")
    print(f"Agent: {args.agent}")
    print(f"Target: {target}")
    print(f"Runtime root: {root}")
    print("Bridge is pointer-only; it does not copy long-term memory into the workspace.")
    return 0


def is_explicit(text: str, source_type: str) -> bool:
    if source_type in {"user_correction", "file_fact", "tool_result"}:
        return True
    return any(marker.lower() in text.lower() for marker in EXPLICIT_MARKERS)


def is_guess(text: str) -> bool:
    return any(marker.lower() in text.lower() for marker in GUESS_MARKERS)


def is_reusable(text: str, memory_type: str) -> bool:
    if memory_type in {"failure_pattern", "workflow", "preference", "decision"}:
        return True
    return any(marker in text for marker in ("以后", "每次", "默认", "必须", "不能", "不要", "规则"))


def infer_type(text: str) -> str:
    if any(marker in text for marker in ("测试", "犯错", "纠正", "以后不要", "不能只")):
        return "failure_pattern"
    if any(marker in text for marker in ("偏好", "默认", "回复", "沟通")):
        return "preference"
    if any(marker in text for marker in ("路径", "项目", "文件", "repo")):
        return "project_fact"
    return "workflow"


def infer_target(memory_type: str, requested: str | None) -> str:
    if requested:
        return requested
    return TYPE_TARGETS.get(memory_type, "agent/DECISIONS.md")


def is_fresh(root: Path, text: str) -> bool:
    for raw in re.findall(r"(?:/[\w .@%+-]+)+\.[A-Za-z0-9]+", text):
        if not Path(raw).exists():
            return False
    for raw in re.findall(r"\b(?:[\w.-]+/)+[\w.-]+\.[A-Za-z0-9]+\b", text):
        if not (root / raw).exists():
            return False
    return True


def rewrite_narrow(text: str) -> str:
    text = re.sub(r"[^，。]{0,16}今天很烦[，,][^，。]*[，。]", "", text)
    text = re.sub(r"因为[^，。]*没意义[，,]", "", text)
    text = text.strip(" -。")
    if "以后" in text:
        text = text[text.index("以后") + 2 :].strip(" ：:")
    return text.rstrip("。") + "。"


def command_remember(args: argparse.Namespace) -> int:
    root = args.root
    findings = guard_text(root, args.text)
    if findings:
        print(f"safety_blocked: {findings[0].kind}")
        return 1
    memory_type = args.type or infer_type(args.text)
    explicit = is_explicit(args.text, args.source_type)
    if is_guess(args.text) or not explicit:
        print("discarded: weak_or_speculative_signal")
        return 0
    target = infer_target(memory_type, args.target)
    record = MemoryRecord(
        memory_id=memory_id_for(args.text, target),
        content=args.text.strip(),
        type=memory_type,
        source_event=args.source_event,
        first_seen_at=now_iso(),
        last_seen_at=now_iso(),
        status="observed",
        target=target,
        explicit=explicit,
        reusable=is_reusable(args.text, memory_type),
        fresh=is_fresh(root, args.text),
        session_id=args.session_id,
    )
    append_jsonl(session_path(root, args.session_id), asdict(record))
    print(f"observed: {record.memory_id}")
    return 0


def iter_records(root: Path, session_id: str | None = None) -> list[dict]:
    paths = [session_path(root, session_id)] if session_id else sorted((runtime_root(root) / "session_cache").glob("*.jsonl"))
    records: list[dict] = []
    for path in paths:
        records.extend(read_jsonl(path))
    return records


def replace_record(root: Path, session_id: str, memory_id: str, updates: dict) -> None:
    path = session_path(root, session_id)
    records = read_jsonl(path)
    for record in records:
        if record.get("memory_id") == memory_id:
            record.update(updates)
    write_jsonl(path, records)


def target_file(root: Path, target: str) -> Path:
    if target not in SOURCE_TARGETS:
        return root / "agent/DECISIONS.md"
    return root / target


def memory_line(memory_id: str, content: str) -> str:
    return f"- <!-- memory_id:{memory_id} --> {content.rstrip('。')}。"


def file_contains_memory(path: Path, memory_id: str, content: str) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    return memory_id in text or normalize_content(content) in normalize_content(text)


def append_memory(root: Path, record: dict, content: str) -> bool:
    path = target_file(root, record["target"])
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(f"# {path.stem}\n", encoding="utf-8")
    if file_contains_memory(path, record["memory_id"], content):
        return False
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n" + memory_line(record["memory_id"], content) + "\n")
    return True


def audit(root: Path, action: str, record: dict, content: str, target: str | None = None, rollback_patch: str = "") -> None:
    append_jsonl(
        audit_path(root),
        {
            "action": action,
            "memory_id": record.get("memory_id", ""),
            "content": content,
            "target_file": target or record.get("target", ""),
            "reason": record.get("reason", action),
            "source_event": record.get("source_event", ""),
            "created_at": now_iso(),
            "confidence": "auto",
            "rollback_patch": rollback_patch,
        },
    )


def deprecated_ids(root: Path) -> set[str]:
    return {item.get("memory_id", "") for item in read_jsonl(deprecated_path(root))}


def mark_deprecated(root: Path, memory_id: str, content: str, target: str, reason: str) -> None:
    item = {"memory_id": memory_id, "content": content, "target_file": target, "reason": reason, "created_at": now_iso()}
    existing = read_jsonl(deprecated_path(root))
    if not any(row.get("memory_id") == memory_id for row in existing):
        append_jsonl(deprecated_path(root), item)
    audit(root, "deprecate", {"memory_id": memory_id, "target": target, "reason": reason}, content, target, rollback_patch=memory_line(memory_id, content))


def enforce_hot_limits(root: Path) -> None:
    for rel, limit in HOT_LIMITS.items():
        path = root / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if len(text) <= limit:
            continue
        trimmed = text[: limit - 80].rstrip() + "\n\n<!-- auto-trimmed by memory-improve -->\n"
        path.write_text(trimmed, encoding="utf-8")
        audit(root, "modify", {"memory_id": f"hot-limit-{safe_slug(rel)}", "target": rel, "reason": "hot memory over limit"}, "trimmed hot memory", rel, rollback_patch="restore previous hot memory from git/audit")


def refresh_hot_draft(root: Path) -> None:
    source_parts = []
    for rel in ("agent/CURRENT_STATE.md", "agent/DECISIONS.md", "tasks/lessons.md"):
        path = root / rel
        if path.exists():
            lines = [line for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip() and "旧" not in line]
            source_parts.extend(lines[:5])
    draft = root / "memory/hot/MEMORY.draft.md"
    draft.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text("# MEMORY draft\n" + "\n".join(source_parts)[:2300] + "\n", encoding="utf-8")


def command_improve(args: argparse.Namespace) -> int:
    root = args.root
    promoted: list[str] = []
    modified: list[str] = []
    deprecated: list[str] = []
    discarded: list[str] = []
    safety_blocked = 0
    seen: set[tuple[str, str]] = set()
    for record in iter_records(root, args.session_id):
        if record.get("status") not in {"observed", "shadow"}:
            continue
        findings = guard_text(root, record["content"])
        if findings:
            safety_blocked += 1
            replace_record(root, record["session_id"], record["memory_id"], {"status": "rejected"})
            audit(root, "reject", record, record["content"])
            continue
        fresh = is_fresh(root, record["content"])
        key = (record["target"], normalize_content(record["content"]))
        if not fresh:
            deprecated.append(record["content"])
            mark_deprecated(root, record["memory_id"], record["content"], record["target"], "fresh gate failed")
            replace_record(root, record["session_id"], record["memory_id"], {"status": "deprecated", "fresh": False})
            continue
        if key in seen:
            discarded.append(record["content"])
            audit(root, "merge", record, record["content"])
            replace_record(root, record["session_id"], record["memory_id"], {"status": "discarded"})
            continue
        seen.add(key)
        if not record.get("explicit") or not record.get("reusable") or not record.get("target"):
            discarded.append(record["content"])
            audit(root, "discard", record, record["content"])
            replace_record(root, record["session_id"], record["memory_id"], {"status": "discarded"})
            continue
        content = rewrite_narrow(record["content"])
        if content != record["content"]:
            modified.append(content)
        if append_memory(root, record, content):
            promoted.append(content)
            audit(root, "promote", record, content)
        else:
            audit(root, "merge", record, content)
        replace_record(root, record["session_id"], record["memory_id"], {"status": "promoted", "content": content})
    enforce_hot_limits(root)
    if args.refresh_hot_draft:
        refresh_hot_draft(root)
    print("Memory updated")
    print_summary_section("Promoted", promoted)
    print_summary_section("Modified", modified)
    print_summary_section("Deprecated", deprecated)
    print_summary_section("Discarded", discarded)
    print(f"Safety blocked: {safety_blocked}")
    return 0


def print_summary_section(title: str, items: list[str]) -> None:
    print(f"{title}:")
    for index, item in enumerate(items[:8], 1):
        print(f"{index}. {item}")
    if not items:
        print("- none")


def iter_source_files(root: Path) -> list[tuple[str, str, Path]]:
    result: list[tuple[str, str, Path]] = []
    for source, authority, prefixes in SOURCE_GROUPS:
        for prefix in prefixes:
            base = root / prefix
            if not base.exists():
                continue
            paths = [base] if base.is_file() else sorted(base.rglob("*"))
            for path in paths:
                if path.is_file() and path.suffix in TEXT_SUFFIXES:
                    result.append((source, authority, path))
    return result


def query_matches(text: str, query: str) -> bool:
    terms = [term for term in re.split(r"\s+", query.strip()) if term]
    return any(term.lower() in text.lower() for term in terms)


def snippet(text: str, query: str) -> str:
    for line in text.splitlines():
        if query_matches(line, query):
            return line.strip()[:180]
    return text.strip().splitlines()[0][:180] if text.strip() else ""


def command_recall(args: argparse.Namespace) -> int:
    root = args.root
    deprecated = deprecated_ids(root)
    rows: list[str] = []
    for source, authority, path in iter_source_files(root):
        text = path.read_text(encoding="utf-8", errors="replace")
        if not query_matches(text, args.query):
            continue
        active_lines = []
        blocked_lines = []
        for line in text.splitlines():
            match = re.search(r"memory_id:([A-Za-z0-9_.-]+)", line)
            if match and match.group(1) in deprecated:
                blocked_lines.append(line)
            elif query_matches(line, args.query):
                active_lines.append(line)
        rel = rel_path(path, root)
        for line in active_lines or ([] if blocked_lines else [snippet(text, args.query)]):
            rows.append(f"[{source} | {authority}] {rel} :: {line.strip()[:180]}")
        for line in blocked_lines:
            rows.append(f"[deprecated | blocked] {rel} :: {line.strip()[:180]}")
    for record in iter_records(root):
        if query_matches(record.get("content", ""), args.query):
            rows.append(f"[session_cache | low] session:{record.get('session_id')} :: {record.get('content')[:180]}")
    if not rows:
        print("no recall results")
        return 1
    for row in rows:
        print(row)
    if not args.context_only:
        print("Final answer generation is intentionally not implemented in the CLI runtime.")
    return 0


def rel_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def find_memory_in_sources(root: Path, memory_id: str | None, instruction: str | None) -> tuple[str, Path, str] | None:
    target_index = None
    if instruction:
        match = re.search(r"第\s*(\d+)\s*条", instruction)
        if match:
            target_index = int(match.group(1))
    candidates: list[tuple[str, Path, str]] = []
    for _, _, path in iter_source_files(root):
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            match = re.search(r"memory_id:([A-Za-z0-9_.-]+)", line)
            if match:
                candidates.append((match.group(1), path, line))
    if memory_id:
        return next((item for item in candidates if item[0] == memory_id), None)
    if target_index and 1 <= target_index <= len(candidates):
        return candidates[target_index - 1]
    return candidates[0] if candidates else None


def remove_memory_line(path: Path, line_to_remove: str) -> None:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    lines = [line for line in lines if line != line_to_remove]
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def command_forget(args: argparse.Namespace) -> int:
    root = args.root
    found = find_memory_in_sources(root, args.memory_id, args.instruction)
    if not found:
        print("memory_not_found")
        return 1
    memory_id, path, line = found
    content = re.sub(r"^-\s*<!--\s*memory_id:[^>]+-->\s*", "", line).strip()
    if args.permanent:
        remove_memory_line(path, line)
        audit(root, "forget", {"memory_id": memory_id, "target": rel_path(path, root), "reason": "explicit permanent delete"}, content, rel_path(path, root), rollback_patch=line)
        print(f"Permanently deleted: {memory_id}")
        return 0
    mark_deprecated(root, memory_id, content, rel_path(path, root), "user correction")
    print(f"Deprecated: {memory_id}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=None)
    sub = parser.add_subparsers(dest="command", required=False)

    start = sub.add_parser("start")
    start.add_argument("--choice", default=None, help="N=create, C=connect, B=backup.")
    start.add_argument("--answers", type=Path, default=None)
    start.add_argument("--name", default=None)
    start.add_argument("--language", default=None)
    start.add_argument("--work-type", default=None)
    start.add_argument("--communication-style", default=None)
    start.add_argument("--project", action="append", default=None)
    start.add_argument("--confirmation-rule", action="append", default=None)
    start.add_argument("--never-store", action="append", default=None)
    start.add_argument("--interactive", action="store_true")
    start.add_argument("--workspace", type=Path, default=None)
    start.add_argument("--target", type=Path, default=None)
    start.add_argument("--agent", choices=sorted(AGENT_BRIDGE_TARGETS), default=None)
    start.add_argument("--append", action="store_true")
    start.add_argument("--force", action="store_true")
    start.add_argument("--print", dest="print_only", action="store_true")
    start.add_argument("--output", type=Path, default=None)
    start.add_argument("--backup-dir", type=Path, default=None)
    start.add_argument("--home", type=Path, default=None, help="Home folder used for ~/.journeymem. Mainly useful for tests.")
    start.add_argument("--library", default=None, help="Memory library name or path to select from registry.")
    start.add_argument("--library-index", type=int, default=None, help="1-based memory library choice from registry.")
    start.add_argument("--backup", type=Path, default=None, help="Backup zip to restore before connecting.")

    init = sub.add_parser("init")
    init.add_argument("--answers", type=Path, default=None, help="JSON answers for non-interactive initialization.")
    init.add_argument("--name", default=None)
    init.add_argument("--language", default=None)
    init.add_argument("--work-type", default=None)
    init.add_argument("--communication-style", default=None)
    init.add_argument("--project", action="append", default=None)
    init.add_argument("--confirmation-rule", action="append", default=None)
    init.add_argument("--never-store", action="append", default=None)
    init.add_argument("--interactive", action="store_true", help="Prompt for missing answers when stdin is a TTY.")
    init.add_argument("--force", action="store_true", help="Overwrite generated starter files if they already exist.")
    init.add_argument("--home", type=Path, default=None, help="Home folder used for ~/.journeymem. Mainly useful for tests.")

    new = sub.add_parser("new")
    new.add_argument("--answers", type=Path, default=None, help="JSON answers for tests or automation.")
    new.add_argument("--name", default=None)
    new.add_argument("--language", default=None)
    new.add_argument("--work-type", default=None)
    new.add_argument("--communication-style", default=None)
    new.add_argument("--project", action="append", default=None)
    new.add_argument("--confirmation-rule", action="append", default=None)
    new.add_argument("--never-store", action="append", default=None)
    new.add_argument("--interactive", action="store_true", help="Prompt for missing answers when stdin is a TTY.")
    new.add_argument("--force", action="store_true", help="Overwrite generated starter files if they already exist.")
    new.add_argument("--home", type=Path, default=None, help="Home folder used for ~/.journeymem. Mainly useful for tests.")

    share = sub.add_parser("share")
    share.add_argument("--agent", choices=sorted(AGENT_BRIDGE_TARGETS), required=True)
    share.add_argument("--workspace", type=Path, default=None, help="Workspace folder where the agent bridge should be written.")
    share.add_argument("--target", type=Path, default=None, help="Explicit bridge file path. Overrides --workspace default.")
    share.add_argument("--append", action="store_true", help="Append a marked bridge block to an existing target file.")
    share.add_argument("--force", action="store_true", help="Overwrite an existing target file, or allow replacing an existing bridge block.")
    share.add_argument("--print", dest="print_only", action="store_true", help="Print the bridge text instead of writing a file.")

    connect = sub.add_parser("connect")
    connect.add_argument("--agent", choices=sorted(AGENT_BRIDGE_TARGETS), default=None)
    connect.add_argument("--workspace", type=Path, default=None, help="Project folder to connect.")
    connect.add_argument("--target", type=Path, default=None, help="Explicit Agent connection file path.")
    connect.add_argument("--append", action="store_true", help="Append a marked connection block to an existing file.")
    connect.add_argument("--force", action="store_true", help="Overwrite an existing connection file.")
    connect.add_argument("--print", dest="print_only", action="store_true", help="Print the connection text instead of writing a file.")
    connect.add_argument("--home", type=Path, default=None, help="Home folder used for ~/.journeymem. Mainly useful for tests.")
    connect.add_argument("--library", default=None, help="Memory library name or path to select from registry.")
    connect.add_argument("--library-index", type=int, default=None, help="1-based memory library choice from registry.")
    connect.add_argument("--backup", type=Path, default=None, help="Backup zip to restore before connecting.")

    install = sub.add_parser("install")
    install.add_argument("--agent", choices=("auto", "all", *AGENT_INSTALL_TARGETS), default="all")
    install.add_argument("--workspace", type=Path, default=None, help="Project folder where Agent helper files should be installed.")
    install.add_argument("--home", type=Path, default=None, help="Home folder for user-level helpers. Mainly useful for tests.")
    install.add_argument("--force", action="store_true", help="Overwrite installed helper files.")

    backup = sub.add_parser("backup")
    backup.add_argument("--output", type=Path, default=None, help="Backup zip file path.")
    backup.add_argument("--backup-dir", type=Path, default=None, help="Folder for generated backups.")
    backup.add_argument("--home", type=Path, default=None, help="Home folder used for ~/.journeymem. Mainly useful for tests.")

    remember = sub.add_parser("remember")
    remember.add_argument("--session-id", default="default")
    remember.add_argument("--text", required=True)
    remember.add_argument("--type", choices=sorted(TYPE_TARGETS), default=None)
    remember.add_argument("--target", choices=sorted(SOURCE_TARGETS), default=None)
    remember.add_argument("--source-event", default="session")
    remember.add_argument("--source-type", choices=["user_message", "user_correction", "file_fact", "tool_result"], default="user_message")

    recall = sub.add_parser("recall")
    recall.add_argument("--query", required=True)
    recall.add_argument("--context-only", action="store_true")

    improve = sub.add_parser("improve")
    improve.add_argument("--session-id", default=None)
    improve.add_argument("--refresh-hot-draft", action="store_true")

    forget = sub.add_parser("forget")
    forget.add_argument("--memory-id", default=None)
    forget.add_argument("--instruction", default=None)
    forget.add_argument("--permanent", action="store_true")
    return parser


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv[1:])
    if args.command is None:
        print_memory_menu()
        return 0
    home = getattr(args, "home", None)
    if args.root is None:
        if args.command == "install":
            args.root = default_library_root(home)
        elif args.command in {"init", "new"}:
            args.root = default_library_root(home)
        elif args.command == "backup":
            default = default_library_root(home)
            args.root = default if is_memory_library(default) else repo_root()
        elif args.command == "start":
            args.root = None
        elif args.command == "connect":
            args.root = None
        else:
            args.root = repo_root()
    if args.root is not None:
        args.root = args.root.expanduser().resolve()
    if args.command == "start":
        return command_start(args)
    if args.command in {"init", "new"}:
        return command_init(args)
    if args.command == "share":
        return command_share(args)
    if args.command == "connect":
        return command_connect(args)
    if args.command == "install":
        return command_install(args)
    if args.command == "backup":
        return command_backup(args)
    if args.command == "remember":
        return command_remember(args)
    if args.command == "recall":
        return command_recall(args)
    if args.command == "improve":
        return command_improve(args)
    if args.command == "forget":
        return command_forget(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
