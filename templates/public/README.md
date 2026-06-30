# Public Memory Template

Use this template with the CLI initializer:

```bash
scripts/memory --root ./my-agent-memory init --answers templates/public/answers.example.json
```

The user should not hand-write Markdown files. The CLI creates the starter runtime, then Agents maintain it through:

```text
remember -> recall -> improve -> forget
```

Before publishing this starter kit, keep private runtime data out of this directory. Only fake users, fake projects, and fake paths belong here.
