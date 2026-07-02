# Agent Entry Transcript Scoring

Use this workflow to verify real Codex and TRAE Work first responses before publishing or recommending JourneyMem to external users. Cursor transcripts are optional evidence.

## What To Capture

For each Agent trial, save only the first visible Agent response after the user types `memory` or follows the JourneyMem setup prompt.

Use JSONL. One line is one trial:

```json
{"id":"trae-valid-default-1","agent":"trae","scenario":"valid_default","text":"What do you want to do?\n1. memory new - Create a memory library\n2. memory connect - Connect this Agent to an existing memory library"}
```

Fields:

- `id`: stable trial id.
- `agent`: `codex`, `trae`, or optional `cursor`.
- `scenario`: one of `valid_default`, `skill_trigger`, `start_page`, or `github_fallback`.
- `text`: the first visible Agent response.

Alternatively, save raw first responses as text files in a folder. The scorer infers the Agent and scenario from the filename:

```text
transcripts/
  codex-valid-default-1.txt
  codex-skill-trigger-1.txt
  codex-start-page-1.txt
  codex-github-fallback-1.txt
  trae-valid-default-1.txt
  trae-skill-trigger-1.txt
  trae-start-page-1.txt
  trae-github-fallback-1.txt
```

Each file should contain only the first visible Agent response.
Optional Cursor evidence can be saved as `cursor-valid-default-1.txt`, but it is not required by the PRD gate.

The generated prompt files are intentionally one line so Agent input boxes do not split the instruction into partial messages.

## Run The Scorer

To create a collection pack for real Codex and TRAE Work trials:

```bash
python3 scripts/prepare_agent_entry_trials.py --output agent-entry-trials
```

If Codex CLI is available on this machine, collect the Codex transcript automatically:

```bash
python3 scripts/collect_codex_entry_transcript.py --trial-pack agent-entry-trials --scenario valid-default
python3 scripts/collect_codex_entry_transcript.py --trial-pack agent-entry-trials --scenario skill-trigger
python3 scripts/collect_codex_entry_transcript.py --trial-pack agent-entry-trials --scenario start-page
python3 scripts/collect_codex_entry_transcript.py --trial-pack agent-entry-trials --scenario github-fallback
```

Optional: if Cursor CLI is available and the account has Agent usage available, collect the Cursor transcript automatically:

```bash
python3 scripts/collect_cursor_entry_transcript.py --trial-pack agent-entry-trials
```

To see exactly what evidence is still missing:

```bash
python3 scripts/agent_entry_readiness.py --trial-pack agent-entry-trials
```

To save a manually copied first response with the correct filename:

```bash
python3 scripts/save_agent_entry_transcript.py --trial-pack agent-entry-trials --agent trae --scenario start-page --input /path/to/first-response.txt
```

```bash
python3 scripts/score_agent_entry_transcripts.py   --input templates/public/agent-entry-transcripts.example.jsonl   --require-agents codex,trae   --require-scenarios valid_default,skill_trigger,start_page,github_fallback   --require-trae-trials 3
```

For raw transcript folders:

```bash
python3 scripts/score_agent_entry_transcripts.py   --input transcripts   --require-agents codex,trae   --require-scenarios valid_default,skill_trigger,start_page,github_fallback   --require-trae-trials 3
```

## Run The PRD Gate

The full PRD gate fails until real Codex and TRAE Work first-response transcripts cover all required scenarios:

```bash
python3 scripts/prd_acceptance_check.py   --transcripts transcripts   --require-trae-trials 3   --run-local-checks
```

For focused Agent transcript scoring during iteration:

```bash
python3 scripts/prd_acceptance_check.py   --mode transcript-only   --transcripts transcripts   --require-trae-trials 3
```

## Pass Criteria

- `memory new` and `memory connect` are visible.
- TRAE Work clone/inspect behavior count = 0.
- Repository-structure summaries = 0.
- Setup-analysis paragraphs = 0.
- Folder-path prompt on valid default = 0.
- First-response question count <= 1.
- `--require-agents codex,trae` passes for release gating.
- `--require-scenarios valid_default,skill_trigger,start_page,github_fallback` passes for release gating.
- `--require-trae-trials 3` passes for release gating.
