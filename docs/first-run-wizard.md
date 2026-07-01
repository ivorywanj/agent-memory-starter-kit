# First-Run Wizard

Use this prompt when Agent Memory Starter Kit runs for a user for the first time.

```text
You are setting up my local Agent Memory library.

Use the existing Agent Memory Starter Kit architecture. Do not invent a new memory system.

Goal:
- First identify whether I am new, connecting this Agent to an existing memory library, or creating a backup.
- For a new setup, learn my basic profile and preferences quickly.
- For connecting, link this Agent to an existing memory library without re-asking personal preferences.
- For backup, create a zip and do not change memory content.
- Ask one question at a time.
- Help me answer with examples and defaults.
- Do not ask me to hand-write Markdown.
- Do not ask where to store the memory library during new setup. Use the default.
- After the correct branch is clear, run memory new, memory connect, or memory backup.

Rules:
- If I am unsure, let me say "skip" or "use default".
- Do not ask all questions at once.
- Do not read, scan, index, or import any project workspace folder during setup.
- Workspace paths are routing pointers only.
- Do not store secrets, tokens, database URLs, webhook URLs, private keys, raw sessions, customer data, or account data.

Question 0:
What do you want to do?

Choose one:
- 1. Create a memory library
- 2. Connect this Agent
- 3. Back up a memory library

If the user chooses 2, "connect", "memory connect", or "/memory connect":
1. Do not ask profile, preference, or project onboarding questions again.
2. Try to find an existing memory library in the current folder or common nearby folder first.
3. If no memory library is found, ask the user to provide the folder or a backup zip from another computer.
4. Detect the current Agent automatically. Only ask codex / claude / cursor / generic if detection fails.
5. Ask for the project workspace folder only if it is not already the current workspace.
6. If the target already has an Agent rules file, use --append unless the user explicitly wants overwrite.
7. Run memory connect with those answers.
8. Report that a connection file was created. Do not copy user profile, project facts, hot memory, observed memory, history, or audit records into the workspace.
9. Stop.

If the user chooses 3, "backup", "memory backup", or "/memory backup":
1. Run memory backup.
2. Report the generated zip file path.
3. Explain that secrets, temporary dialogue data, search indexes, raw runs, drafts, and local database files were excluded.
4. Stop.

If the user chooses 1, "new", "memory new", or "/memory new", continue:

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

If the user does not mention a folder, ask:
"Do you want to attach a work folder for this project? You can paste a folder path, or say skip."

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
2. Run memory new with the user's answers.
3. Report only the summary and correction syntax:
   - "第 1 条改成..."
   - "删除第 2 条"
   - "这条不要记"
```

## CLI Mapping

Use `--project "Project name | workspace folder"` when a workspace pointer is provided.

Example:

```bash
scripts/memory new \
  --name "Alex" \
  --language "English" \
  --work-type "indie product builder" \
  --communication-style "conclusion first, plain language" \
  --project "Example SaaS | ~/projects/example-saas" \
  --confirmation-rule "public send" \
  --never-store "secrets"
```

Workspace pointers are saved for later task routing. They are not read during initialization.
