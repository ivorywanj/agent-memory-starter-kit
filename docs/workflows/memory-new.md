# /memory new

Use this workflow when the user is creating a memory library for the first time.

## User Experience

Ask one question at a time. Do not ask where to store the memory library. Use the default location created by the CLI.

Questions:

1. What should Agents call you?
2. What language should Agents use by default?
3. What kind of work do you do?
4. What are your current 1-3 projects?
5. How should Agents communicate with you?
6. Which actions require confirmation?
7. What must never be stored in memory?

For question 4, guide the user to attach a work folder:

```text
If this project has a work folder, paste it too. Example: Example SaaS | ~/projects/example-saas. You can also say skip.
```

## Agent Command

```bash
scripts/memory new
```

For non-interactive tests:

```bash
scripts/memory new --answers templates/public/answers.example.json
```

## Pass Criteria

- The user does not hand-write Markdown.
- Setup asks one question at a time.
- Project folders are saved only as pointers.
- The setup does not read, scan, index, or import project folder contents.
- Secret-shaped answers are blocked by the guard.
