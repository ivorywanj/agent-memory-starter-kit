# First-Run Wizard

Use this prompt when Agent Memory Starter Kit runs for a new user for the first time.

```text
You are setting up my local Agent Memory runtime.

Use the existing Agent Memory Starter Kit architecture. Do not invent a new memory system.

Goal:
- Learn my basic profile and preferences quickly.
- Ask one question at a time.
- Help me answer with examples and defaults.
- Do not ask me to hand-write Markdown.
- After the interview, run scripts/memory init with my answers.

Rules:
- If I am unsure, let me say "skip" or "use default".
- Do not ask all questions at once.
- Do not read, scan, index, or import any project workspace folder during setup.
- Workspace paths are routing pointers only.
- Do not store secrets, tokens, database URLs, webhook URLs, private keys, raw sessions, customer data, or account data.

Question 1/7:
What should Agents call you?

You can answer with a name, nickname, or "skip".
Examples: Alex / Sam / Lin

Question 2/7:
What language should Agents use by default?

Examples: English / Chinese / match the language I use

Question 3/7:
What kind of work do you do?

Answer in one sentence. Examples:
- indie product builder
- software engineer working on backend services
- researcher and content creator
- designer building prototypes

Question 4/7:
What are your current 1-3 projects? If a project has a workspace folder, include it.

Use this format when you know the folder:
Project name | workspace folder

Examples:
- Example SaaS | ~/projects/example-saas
- Personal blog | /Users/alex/work/blog
- Portfolio site | not sure yet

If you only know the project name, that is enough. I will store the workspace as not provided.

Question 5/7:
How should Agents communicate with you?

You can choose or write your own:
- conclusion first, then short reasoning
- ask before making risky assumptions
- concise and direct
- explain tradeoffs in plain language

Question 6/7:
Which actions require confirmation?

Default recommended:
- public send
- production deploy
- database migration
- destructive action
- installing new dependencies
- git push

You can answer "use default" or add more.

Question 7/7:
What must never be stored in memory?

Default recommended:
- secrets
- API keys
- tokens
- webhook URLs
- database URLs
- private keys
- raw sessions
- customer data
- account data

After collecting answers:
1. Summarize what will be recorded.
2. Run scripts/memory init with the user's answers.
3. Report only the summary and correction syntax:
   - "第 1 条改成..."
   - "删除第 2 条"
   - "这条不要记"
```

## CLI Mapping

Use `--project "Project name | workspace folder"` when a workspace pointer is provided.

Example:

```bash
scripts/memory --root ./my-agent-memory init \
  --name "Alex" \
  --language "English" \
  --work-type "indie product builder" \
  --communication-style "conclusion first, plain language" \
  --project "Example SaaS | ~/projects/example-saas" \
  --confirmation-rule "public send" \
  --never-store "secrets"
```

Workspace pointers are saved for later task routing. They are not read during initialization.
