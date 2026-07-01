# Public Memory Template

Use this template as a demo fixture with the CLI setup command:

```bash
scripts/memory new --answers templates/public/answers.example.json
```

For a real user, prefer the Agent-led first-run wizard in `docs/first-run-wizard.md`. The first question should identify whether the user wants to create a memory library, connect this Agent, or create a backup. The user should not hand-write Markdown files.

If the user is new, the CLI creates the starter memory library. Then Agents maintain it through:

```text
remember -> recall -> improve -> forget
```

Connect this same memory library with Agent workspaces through pointer-only connection files:

```bash
scripts/memory connect --agent codex --workspace ./my-project
scripts/memory connect --agent claude --workspace ./my-project
scripts/memory connect --agent cursor --workspace ./my-project
```

Before publishing this starter kit, keep private memory data out of this directory. Only fake users, fake projects, and fake paths belong here.
