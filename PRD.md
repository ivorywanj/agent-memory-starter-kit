# PRD: JourneyMem First Screen Must Start With memory new / memory connect

Status: Draft for review
Owner: project maintainer
Date: 2026-07-02

## Problem

JourneyMem's public first screen still leads with installation or repository setup language in some surfaces. This causes external Agents, especially TRAE Work, to treat `ivorywanj/agent-memory-starter-kit` as a normal code repository to clone, inspect, or summarize before showing the intended JourneyMem menu.

The intended first user choice is not clone or install. The intended first choice is:

```text
What do you want to do?
1. memory new - Create a memory library
2. memory connect - Connect this Agent to an existing memory library

Other command:
- memory backup - Back up a memory library
```

## Goal

Make every public first screen route users and Agents to the two primary setup intents before any clone, install, repository, or troubleshooting path:

- `memory new`: first-time user creates a memory library.
- `memory connect`: current Agent connects to an existing memory library.

The fix is accepted only when the local checks pass, Codex passes a realistic preflight, and a real external TRAE Work trial, operated through Computer Use, returns the correct first response without clone/inspect behavior.

## Non-Goals

- Do not redesign JourneyMem's memory model.
- Do not rename `memory`, `memory new`, `memory connect`, or `memory backup`.
- Do not add dependencies, hosted services, accounts, vector databases, or web UI behavior.
- Do not change backup semantics.
- Do not commit, push, publish, or create a release without explicit maintainer confirmation.

## User Flow

### Expected Public First Screen

1. User lands on GitHub README or JourneyMem Start Page.
2. The first visible action shows the JourneyMem menu with `memory new` and `memory connect`.
3. Install instructions appear only after the menu or in a clearly marked fallback section.
4. Manual clone appears only as terminal fallback, not as the primary quickstart.

### Expected Agent Behavior

1. User gives an Agent one of the accepted JourneyMem entry prompts.
2. Agent does not clone, inspect, summarize repository structure, or ask what to do with the repo.
3. Agent shows the two-choice JourneyMem menu.
4. Agent runs `memory new` only after the user chooses create/new.
5. Agent runs `memory connect` only after the user chooses connect/existing.

## Scope

Update only the public package surfaces and checks that control first-screen behavior:

- `README.md`
- `index.html`
- `docs/index.html`
- `tests/test_public_package.py`
- `scripts/public_release_check.py`
- Related first-screen wording only if required by those checks

Implementation should be surgical. CLI runtime behavior is already correct and should not be rewritten unless a failing test proves otherwise.

## Quantitative Acceptance Metrics

### Documentation and Start Page

- `PRD.md` exists at the public package root.
- In `README.md`, `memory new` and `memory connect` both appear before the first `git clone`, `curl -fsSL`, or `./install.sh` command.
- In `README.md`, clone-first exposure before the first JourneyMem menu is `0`.
- In both `index.html` and `docs/index.html`, the content before `<!-- first-screen-end -->` contains:
  - `memory new`
  - `memory connect`
- In both `index.html` and `docs/index.html`, the content before `<!-- first-screen-end -->` does not contain:
  - `git clone`
  - `curl -fsSL`
  - `./install.sh`

### Automated Tests

These commands must pass:

```bash
python3 scripts/memory
python3 tests/test_public_package.py
python3 scripts/public_release_check.py
python3 scripts/memory_guard.py
git diff --check
```

---

# Addendum: Installer Completion Must Show The First-Use Choices

Status: Draft for implementation
Owner: project maintainer
Date: 2026-07-02

## Problem

The README now teaches users to install JourneyMem first, then run `memory`. However, the installer completion output only says "Start now" and prints the command. A non-technical user or an Agent can still miss what should happen next: choose between creating a new memory library and connecting to an existing one.

The installer should not automatically create or connect a memory library. It should make the next choice visible immediately after install succeeds.

## Goal

After `install.sh` finishes successfully, the terminal output must directly show the first-use choices:

```text
What do you want to do?
1. memory new - Create a memory library
2. memory connect - Connect this Agent to an existing memory library

Other command:
- memory backup - Back up a memory library
```

It should still tell the user how to run `memory`, but the completion output itself should make the create/connect choice visible.

## Non-Goals

- Do not auto-run `memory new`.
- Do not auto-run `memory connect`.
- Do not make `install.sh` interactive.
- Do not change the memory library creation or connection semantics.

## Quantitative Acceptance Metrics

- `sh install.sh` exits with status `0` in the existing clean-home fixture.
- The successful installer output contains `JourneyMem installed`.
- The successful installer output contains `What do you want to do?`.
- The successful installer output contains both `1. memory new - Create a memory library` and `2. memory connect - Connect this Agent to an existing memory library`.
- The successful installer output contains `- memory backup - Back up a memory library`.
- The installer still does not create a default personal memory library until the user chooses `memory new`.
- Existing local gates still pass:

```bash
python3 tests/test_public_package.py
python3 scripts/public_release_check.py
python3 scripts/memory_guard.py
git diff --check
```

The automated checks must fail on the previous install-first first screen and pass only when `memory new` / `memory connect` are first-screen-visible.

### Real Agent Acceptance

Codex can be used first as a local preflight. The final gate must still use Computer Use to operate the external TRAE Work app directly.

Do not use defensive or over-specified prompts for acceptance, such as prompts that say "do not clone", "do not inspect", or "reply exactly with this menu". The test must imitate a real user who has seen the public README or Start Page.

Collect first visible responses for four scenarios:

- `valid_default`
- `skill_trigger`
- `start_page`
- `github_fallback`

Each TRAE Work transcript must pass these measurable checks:

- `menu_hit = 1`
- `clone_or_inspect = 0`
- `noisy_phrase_count = 0`
- `folder_prompt_on_valid_default = 0`
- `question_count <= 1`
- `command_available = 1`

The TRAE gate command must pass:

```bash
python3 scripts/score_agent_entry_transcripts.py \
  --input /private/tmp/journeymem-entry-trials/transcripts \
  --require-agents trae \
  --require-scenarios valid_default,skill_trigger,start_page,github_fallback \
  --require-trae-trials 4
```

The final PRD gate must pass:

```bash
python3 scripts/prd_acceptance_check.py \
  --transcripts /private/tmp/journeymem-entry-trials/transcripts \
  --require-trae-trials 4 \
  --run-local-checks
```

## TRAE Work Test Protocol

1. First run the same scenarios in Codex as a preflight. Codex preflight can fail fast before spending time in external TRAE Work.
2. Create a fresh trial pack:

```bash
python3 scripts/prepare_agent_entry_trials.py \
  --output /private/tmp/journeymem-entry-trials \
  --force
```

3. Use Computer Use to open external TRAE Work.
4. For each scenario, paste a realistic user message into a fresh TRAE Work conversation:

```text
valid_default: memory
skill_trigger: $journeymem
start_page: I want to use JourneyMem from this Start Page: https://ivorywanj.github.io/agent-memory-starter-kit/
github_fallback: 我想使用这个记忆库：https://github.com/ivorywanj/agent-memory-starter-kit
```

5. The generated `prompts/trae-*.prompt.txt` files may be used only if they contain the realistic user messages above and do not include defensive instructions.
6. Save only the first visible TRAE Work response into the matching file under `/private/tmp/journeymem-entry-trials/transcripts/`.
7. Do not include follow-up messages, tool logs, screenshots, secrets, account data, or private workspace data.
8. Run the transcript scorer and PRD gate.

If Computer Use reaches a login, permission, upload, external submission, or sensitive-data transmission step, stop and request confirmation at action time.

---

# Addendum: TRAE Requires Native Skill Package Layout

Status: Draft for implementation
Owner: project maintainer
Date: 2026-07-03

## Problem

After the GitHub-link-first-screen fix, real TRAE Work validation can still fail before JourneyMem instructions run. TRAE may treat the GitHub link as a generic skill creation task, invoke its built-in `skill-creator`, clone the repository, and prepare to run `scripts/memory new`.

Clicking `Skip` can stop damage during testing, but it is not a normal user path and does not count as acceptance.

TRAE's local skill documentation requires user skills to live at:

```text
.trae/skills/<skill-name>/SKILL.md
```

Root `SKILL.md` alone is not enough for TRAE-native skill installation.

## Goal

Ship JourneyMem as a TRAE-recognizable user skill as well as a public GitHub package.

TRAE should be able to install or use the existing JourneyMem skill at `.trae/skills/journeymem/SKILL.md` instead of creating a new skill, cloning the repository as a project, or running `memory new`.

## Required Changes

- Generate `.trae/skills/journeymem/SKILL.md` in the public package.
- The TRAE-native skill must start with the same `memory new` / `memory connect` menu.
- README, root `SKILL.md`, and `AGENTS.md` must point TRAE `skill-creator` to the existing TRAE skill folder.
- Public checks must fail if `.trae/skills/journeymem/SKILL.md` is missing.
- Real TRAE validation must use normal user wording, including:

```text
我想使用这个记忆库：https://github.com/ivorywanj/agent-memory-starter-kit
```

## Quantitative Acceptance Metrics

- `public-export/.trae/skills/journeymem/SKILL.md` exists after export.
- The file has frontmatter `name: "journeymem"` and a description under 200 characters.
- Public tests assert that `SKILL.md`, `.trae/skills/journeymem/SKILL.md`, and `AGENTS.md` all contain the first-response menu.
- The release check fails if the TRAE-native skill file is missing.
- Real TRAE Work validation fails if the first user-visible step is a Run/allow prompt for `git clone`, `scripts/memory new`, or any personal-memory write before the `memory new` / `memory connect` menu.

## Rollout and Safety

- Do not commit or push until the maintainer explicitly asks.
- Before any commit or push, inspect `git diff`, scan for secrets, verify `.env*` files are not staged, and report the result.
- If any test fails because the implementation changes CLI behavior outside first-screen routing, stop and re-plan.
- If TRAE Work still clones, inspects, summarizes repository structure, or asks a generic repo question, the fix is not accepted.

## Open Questions

- None for the first implementation pass.

---

# Addendum: TRAE connect Must Persist Into New Conversations

Status: Draft for implementation
Owner: project maintainer
Date: 2026-07-02

## Problem

The menu-first fix makes TRAE Work show `memory new` / `memory connect`, but a connected TRAE Work conversation can still fail the real user outcome: after `memory connect`, a new TRAE Work conversation answers "I do not know your name" instead of reading the connected JourneyMem memory library.

This means the first-screen behavior is correct, but the connection is not reliably active across fresh TRAE Work conversations.

## Goal

After `memory connect` for TRAE Work, a fresh TRAE Work conversation in the connected workspace must know how to load the shared memory library before answering personal-memory questions such as "What do you call me?" or "你怎么称呼我".

## Non-Goals

- Do not copy the full user profile into the TRAE workspace.
- Do not store secrets, raw sessions, or full private memory history inside generated TRAE helper files.
- Do not overwrite existing TRAE native memory; JourneyMem may only upsert its own marked bridge block.
- Do not require users to paste defensive prompts into every new conversation.
- Do not add a hosted service, database, vector index, or background daemon.

## Expected User Flow

1. User runs `memory connect` in TRAE Work or selects the connected TRAE Work workspace.
2. JourneyMem writes TRAE-readable connection files into that workspace and upserts a bounded JourneyMem bridge into TRAE native memory.
3. User opens a new TRAE Work conversation in the same connected workspace.
4. User asks a natural memory question, for example:

```text
你怎么称呼我
```

5. TRAE Work reads the connected memory library startup files and answers from JourneyMem, not from guesswork.

## Quantitative Acceptance Metrics

- `memory connect --agent trae --workspace <workspace>` writes a TRAE connection rule that:
  - points to the shared memory library path,
  - explicitly marks the rule as always loaded when TRAE supports always-loaded rule metadata,
  - instructs TRAE to read `AGENTS.md`, `ONBOARDING.md`, `memory/hot/USER.md`, and `memory/hot/MEMORY.md` before answering personal-memory questions.
- Generated TRAE connection files must not contain copied user profile facts such as a real user name or project facts.
- `memory connect --agent trae` also upserts `~/.trae-cn/memory/user_profile.md` with a marked JourneyMem native memory bridge:
  - preserves existing TRAE native memory text,
  - includes the shared memory library path,
  - includes a bounded startup cache from `memory/hot/USER.md` and `memory/hot/MEMORY.md`,
  - blocks if the bridge text contains secret-shaped content.
- Unit tests must fail if the generated TRAE connection file does not include the always-loaded rule metadata and personal-memory trigger language, or if the TRAE native memory bridge is missing.
- A real TRAE Work UI smoke test must pass:
  - new conversation in the connected workspace,
  - user asks `你怎么称呼我`,
  - first answer uses the connected JourneyMem memory and does not say it does not know.

## Test Protocol

Local gates:

```bash
python3 tests/test_public_package.py
python3 scripts/public_release_check.py
python3 scripts/memory_guard.py
git diff --check
```

TRAE Work smoke test:

1. Create or reuse a JourneyMem library whose `memory/hot/USER.md` contains a non-guessable test name.
2. Run `memory connect --agent trae --workspace <trae-workspace>`.
3. Open TRAE Work with that workspace selected.
4. Start a new conversation and ask:

```text
你怎么称呼我
```

5. Pass only if TRAE answers with the stored JourneyMem name or test code without asking the user to provide it again.

---

# Addendum: TRAE Reinstall Then Connect Must Discover Existing Local Memory

Status: Draft for implementation
Owner: project maintainer
Date: 2026-07-02

## Problem

After uninstalling the active TRAE helper files, a real TRAE Work user can start again from the GitHub repository link, see a JourneyMem menu, choose to connect to an existing memory library, and still fail. TRAE Work may summarize the repository, show `git clone`, or look only in the current task folder for `AGENTS.md` instead of installing JourneyMem and running the local `memory connect` command.

The local JourneyMem registry can already contain a valid default library at `~/.journeymem/registry.json`. The failure is that the reinstall entry path does not reliably route TRAE to the installed local command that checks that registry.

## Goal

When a TRAE Work user starts from the public GitHub/Start Page entry after helper files were removed, JourneyMem must guide the Agent to install/activate the local `memory` command first. When the user chooses connect/existing, the flow must run `memory connect` or `~/.local/bin/memory connect`, which checks the local registry/default path before asking for a folder.

## Non-Goals

- Do not require users to paste a defensive test prompt.
- Do not make users manually browse for `/Users/.../Agent Memory` when a valid local registry exists.
- Do not treat the GitHub repository as the memory library.
- Do not ask TRAE to inspect, summarize, or clone the repo as the primary flow.
- Do not move, copy, import, or overwrite the shared memory library.

## Expected User Flow

1. TRAE helper files and TRAE native memory are absent or stale.
2. User gives TRAE a normal JourneyMem entry, for example:

```text
https://github.com/ivorywanj/agent-memory-starter-kit 我想用这个journeymem记忆系统
```

3. TRAE installs or activates JourneyMem using the hosted installer, not by summarizing the repo.
4. TRAE shows the first-use menu.
5. User says:

```text
连接到一个已有的记忆库
```

6. TRAE runs the local connect command. It must check `~/.journeymem/registry.json` and the default JourneyMem library path before asking for a folder.
7. If exactly one valid local memory library exists, TRAE connects automatically and reports the connected library path.

## Quantitative Acceptance Metrics

- Public README and Start Page Agent prompts must contain the concrete hosted installer command:

```bash
curl -fsSL https://raw.githubusercontent.com/ivorywanj/agent-memory-starter-kit/main/install.sh | bash
```

- Public README and Start Page Agent prompts must contain the concrete fallback command:

```bash
~/.local/bin/memory connect
```

- Public README must not present `git clone https://github.com/ivorywanj/agent-memory-starter-kit.git` as a normal quickstart or Agent-facing fallback.
- Generated TRAE helper text must say that GitHub URL entry is not enough; if `memory` is unavailable, run the hosted installer, then run `~/.local/bin/memory connect` for connect/existing.
- Unit tests must fail if the Start Page TRAE prompt only says "use this install source: GitHub" without the hosted install command.
- Unit tests must fail if README still exposes `git clone` as the user-facing fallback.
- With a valid `~/.journeymem/registry.json`, `memory connect --agent trae --workspace <workspace>` must connect without asking for a folder path.
- External TRAE Work reinstall/connect smoke test must pass:
  - Begin from a fresh TRAE task after removing active helper files.
  - Use a realistic GitHub-link entry message.
  - Choose connect/existing in natural Chinese.
  - Pass only if TRAE installs/activates JourneyMem and connects to the existing local library without asking the user where the library is.

## Test Protocol

Local gates:

```bash
python3 tests/test_public_package.py
python3 scripts/public_release_check.py
python3 scripts/memory_guard.py
git diff --check
```

TRAE Work smoke test:

1. Remove active TRAE JourneyMem helper files or use a TRAE workspace without them.
2. Confirm `~/.journeymem/registry.json` points to one valid JourneyMem library.
3. Start a fresh TRAE Work task with:

```text
https://github.com/ivorywanj/agent-memory-starter-kit 我想用这个journeymem记忆系统
```

4. When TRAE shows the menu, choose:

```text
连接到一个已有的记忆库
```

5. Pass only if TRAE runs the local connect command and reports a successful connection to the existing local library. Asking "where is your memory library?" is a failure when the registry has one valid candidate.

---

# Addendum: README Quickstart Must Teach Fast Install First

Status: Draft for implementation
Owner: project maintainer
Date: 2026-07-02

## Problem

The README Quickstart currently starts with `memory` and the first-use menu. That protects Agents from clone-first behavior, but it is not the right shape for a human-facing Quickstart. A new user who opens the repository needs to know how to install JourneyMem quickly before they can type `memory`.

The menu-first rule is still correct for Agent behavior after install. It should not replace the human Quickstart installation path.

## Goal

Make the README Quickstart explain the fastest working path in this order:

1. Install JourneyMem once.
2. Run `memory`.
3. Choose `memory new` or `memory connect`.
4. Use `~/.local/bin/memory connect` as the fallback when PATH is not loaded.

Keep the Agent-facing prompt rules separate: Agents should still avoid repo inspection, avoid `git clone` as the visible setup step, and use the hosted installer before showing the menu.

## Non-Goals

- Do not restore clone-first setup.
- Do not hide the first-use menu.
- Do not make users read internal runtime terms before installation.
- Do not change CLI runtime behavior.

## Quantitative Acceptance Metrics

- In `README.md`, the first command under `## Quickstart` is:

```bash
curl -fsSL https://raw.githubusercontent.com/ivorywanj/agent-memory-starter-kit/main/install.sh | bash
```

- In `README.md`, the installer command appears before the first standalone `memory` command and before the first menu block.
- In `README.md`, the sequence `Install once -> Run -> Choose` is explicit.
- In `README.md`, `memory new` and `memory connect` still appear in the Quickstart menu.
- In `README.md`, `git clone https://github.com/ivorywanj/agent-memory-starter-kit.git` remains absent.
- Start Page first screen may keep the menu-first Agent positioning, but the "Command not available" section must still show the hosted installer.
- Unit tests and release checks must fail if README Quickstart starts with `memory` before the hosted installer.

## Test Protocol

Local gates:

```bash
python3 tests/test_public_package.py
python3 scripts/public_release_check.py
python3 scripts/memory_guard.py
git diff --check
```
