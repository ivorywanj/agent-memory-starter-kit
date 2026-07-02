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
github_fallback: I want to use JourneyMem. Here is the repo: https://github.com/ivorywanj/agent-memory-starter-kit
```

5. The generated `prompts/trae-*.prompt.txt` files may be used only if they contain the realistic user messages above and do not include defensive instructions.
6. Save only the first visible TRAE Work response into the matching file under `/private/tmp/journeymem-entry-trials/transcripts/`.
7. Do not include follow-up messages, tool logs, screenshots, secrets, account data, or private workspace data.
8. Run the transcript scorer and PRD gate.

If Computer Use reaches a login, permission, upload, external submission, or sensitive-data transmission step, stop and request confirmation at action time.

## Rollout and Safety

- Do not commit or push until the maintainer explicitly asks.
- Before any commit or push, inspect `git diff`, scan for secrets, verify `.env*` files are not staged, and report the result.
- If any test fails because the implementation changes CLI behavior outside first-screen routing, stop and re-plan.
- If TRAE Work still clones, inspects, summarizes repository structure, or asks a generic repo question, the fix is not accepted.

## Open Questions

- None for the first implementation pass.
