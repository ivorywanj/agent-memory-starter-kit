#!/usr/bin/env python3
"""Lightweight remember/recall/improve/forget runtime for Agent Memory."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shlex
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

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
    "cursor": Path(".cursor/rules/agent-memory.mdc"),
    "generic": Path("AGENT_MEMORY.md"),
}
AGENT_LABELS = {
    "codex": "Codex",
    "claude": "Claude Code",
    "cursor": "Cursor",
    "generic": "Generic Agent",
}


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


def agent_bridge_text(root: Path, agent: str) -> str:
    label = AGENT_LABELS[agent]
    root_text = str(root)
    memory_cmd = shlex.quote(str(root / "scripts/memory"))
    root_arg = shlex.quote(root_text)
    return f"""# Agent Memory Bridge

This {label} workspace uses a shared Agent Memory runtime.

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
    probe = runtime_root(root) / ".guard-probe.md"
    probe.parent.mkdir(parents=True, exist_ok=True)
    probe.write_text(text, encoding="utf-8")
    try:
        return memory_guard.scan_file(probe, root)
    finally:
        try:
            probe.unlink()
        except OSError:
            pass


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
    parser.add_argument("--root", type=Path, default=repo_root())
    sub = parser.add_subparsers(dest="command", required=True)

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

    share = sub.add_parser("share")
    share.add_argument("--agent", choices=sorted(AGENT_BRIDGE_TARGETS), required=True)
    share.add_argument("--workspace", type=Path, default=None, help="Workspace folder where the agent bridge should be written.")
    share.add_argument("--target", type=Path, default=None, help="Explicit bridge file path. Overrides --workspace default.")
    share.add_argument("--append", action="store_true", help="Append a marked bridge block to an existing target file.")
    share.add_argument("--force", action="store_true", help="Overwrite an existing target file, or allow replacing an existing bridge block.")
    share.add_argument("--print", dest="print_only", action="store_true", help="Print the bridge text instead of writing a file.")

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
    args.root = args.root.resolve()
    if args.command == "init":
        return command_init(args)
    if args.command == "share":
        return command_share(args)
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
