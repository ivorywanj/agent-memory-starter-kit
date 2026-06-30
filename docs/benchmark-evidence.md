# Benchmark Evidence

Status: public summary

The private development runtime passed a 60-row real-model benchmark before this public package was extracted.

Scope:

```text
T01-T20 x current_codex/v1_only/fused = 60 rows
```

Final fused result:

| Metric | Result |
|---|---:|
| Background hit rate | 94% |
| Preference compliance | 99% |
| Safety violations | 0 |
| Source-of-truth accuracy | 100% |
| Tool command validity | 100% |
| Repeated mistakes | 0 |
| Full-runtime accidental loads | 0 |
| Average score | 4.8 |

Both gates passed:

- Fusion Gate: validates compact startup, recall/source-of-truth separation, tool command validity, conflict resolution, and token discipline.
- Auto Improve Gate: validates `remember -> recall -> improve -> forget` behavior, source tagging, safety blocking, deprecation, and growth control.

Raw model outputs, prompts, logs, and private runtime paths are intentionally not included in this public package.
