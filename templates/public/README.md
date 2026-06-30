# Public Memory Template

Use this template as a demo fixture with the CLI initializer:

```bash
scripts/memory --root ./my-agent-memory init --answers templates/public/answers.example.json
```

For a real user, prefer the Agent-led first-run wizard in `docs/first-run-wizard.md`. The first question should identify whether the user is new or wants to share an existing memory runtime with another Agent/workspace. The user should not hand-write Markdown files.

If the user is new, the CLI creates the starter runtime. Then Agents maintain it through:

```text
remember -> recall -> improve -> forget
```

Share this same runtime with Agent workspaces through pointer-only bridge files:

```bash
scripts/memory --root ./my-agent-memory share --agent codex --workspace ./my-project
scripts/memory --root ./my-agent-memory share --agent claude --workspace ./my-project
scripts/memory --root ./my-agent-memory share --agent cursor --workspace ./my-project
```

Before publishing this starter kit, keep private runtime data out of this directory. Only fake users, fake projects, and fake paths belong here.
