# /memory-init

Use this when a new user needs a starter memory runtime and should not hand-write Markdown files.

## Command

```bash
scripts/memory --root ./my-agent-memory init --answers templates/public/answers.example.json
```

For direct flags:

```bash
scripts/memory --root ./my-agent-memory init \
  --name "Alex" \
  --language "English" \
  --work-type "indie product builder" \
  --communication-style "Conclusion first, plain language." \
  --project "Example SaaS" \
  --confirmation-rule "production deploy" \
  --never-store "secrets"
```

## Behavior

- Creates `AGENTS.md`, `ONBOARDING.md`, `CROSS_AGENT.md`, hot memory, source-of-truth skeletons, project ledger, and memory buffer READMEs.
- Runs safety scanning before writing generated files.
- Refuses to overwrite existing starter files unless `--force` is passed.
- Prints a short summary and correction syntax instead of asking the user to edit Markdown.

## User Correction

If the summary is wrong, the user should say:

```text
第 1 条不对
删除第 2 条
第 3 条改成...
```

The Agent should route corrections through `remember -> improve -> source-of-truth`, not ask the user to open Markdown files.
