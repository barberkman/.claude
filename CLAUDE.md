## Committing

When the user says "commit the changes" (or similar):

1. Generate a one-line commit message with detailed descriptions as footnotes from the current diff
2. Always commit all changes as a **single commit** — do NOT split into multiple commits
3. Stage the changed files with `git add`
4. Commit using **only** the generated message — do NOT append `Co-Authored-By` or any other trailers
5. **Do NOT push** — only commit locally

## Workflow

- Direct requests (e.g., "fix this", "add X", "refactor Y"): implement immediately without asking for confirmation.
- Discussion questions (e.g., "why?", "how can I fix this?", "what's wrong?"): present the proposed solution and get confirmation before modifying any project files.

## Code Intelligence

Prefer LSP over Grep/Glob/Read for code navigation:

- goToDefinition to jump to source
- findReferences to see all usages
- hover for type info
After editing code, check LSP diagnostics before moving on.

## Output

After completing a task, always provide a summary that includes:

1. **What was done** — brief description of the changes and why
2. **Files changed** — list every file that was created, modified, or deleted, grouped by action:
   - **Created**: new files added to the project
   - **Modified**: existing files that were edited
   - **Deleted**: files that were removed

## Rules

- **Only make code changes that are explicitly requested.** Do NOT take initiative to modify, add, refactor, or fix code beyond what was asked.
- If you notice something that could be improved, you may suggest it — but do NOT make the change unless the user approves.

## Plan Mode

When calling `ExitPlanMode`, always post a short TL;DR in the chat message that accompanies it (2–4 lines): the goal, the approach in one sentence, and roughly what will change. Keep the plan file itself fully detailed — the chat summary is just so I can skim without opening the file.
