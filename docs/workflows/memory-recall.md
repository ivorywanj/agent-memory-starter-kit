---
name: memory-recall
description: Retrieve memory evidence with source and authority tags. Trigger with /memory-recall.
---

# /memory-recall

Purpose: retrieve relevant memory while making authority explicit.

## Run

```bash
python3 scripts/memory_runtime.py recall --query "<query>" --context-only
```

Use `--context-only` when debugging retrieval. It must show evidence only and skip final answer generation.

## Required Tags

Every result must include one source and one authority:

```text
[source_of_truth | high]
[hot_memory | medium]
[history_evidence | low]
[session_cache | low]
[observed_memory | low]
[deprecated | blocked]
```

Authority order:

```text
source_of_truth > hot_memory > history_evidence > session_cache > observed_memory
```

`deprecated` is blocked. It may appear as audit evidence but must not be used as a current fact.

## Rules

- Do not treat recall output as source-of-truth unless it comes from source-of-truth files.
- Include file path or session id for every evidence row.
- When sources conflict, trust source-of-truth files and surface the conflict.
- Do not read raw private sessions by default.

## Output

```text
[source_of_truth | high] tasks/lessons.md :: ...
[session_cache | low] session:<id> :: ...
[deprecated | blocked] tasks/lessons.md :: ...
```
