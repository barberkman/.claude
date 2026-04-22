# Behavioral Guidelines

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## Workflow

**Scope rule:** Only make code changes that fall within the scope of what was requested. Don't take initiative to refactor, modernize, or "fix" adjacent code. If you notice something worth changing outside that scope, mention it — don't do it.

**Mode rule:**
- **Direct requests** (e.g., "fix this", "add X", "refactor Y"): implement immediately within the requested scope. No confirmation needed.
- **Discussion questions** (e.g., "why?", "how can I fix this?", "what's wrong?"): explain and propose. Wait for confirmation before modifying any project files.

## Code Intelligence

Prefer LSP tools over Grep/Glob/Read for code navigation when available:
- `goToDefinition` to jump to source
- `findReferences` to see all usages
- `hover` for type info

After editing code, check LSP diagnostics before declaring the task complete. A task is not done until diagnostics are clean or the remaining issues are explicitly acknowledged.

## Committing

When the user says "commit the changes" (or similar):

1. Generate a one-line commit message with detailed descriptions as footnotes from the current diff.
2. Commit all changes as a **single commit** — do NOT split into multiple commits.
3. Stage the changed files with `git add`.
4. Commit using **only** the generated message — do NOT append `Co-Authored-By` or any other trailers.
5. **Do NOT push** — only commit locally.

## Output

After completing a task, always provide a summary that includes:

1. **What was done** — brief description of the changes and why.
2. **Files changed** — grouped by action:
   - **Created**: new files added to the project.
   - **Modified**: existing files that were edited.
   - **Deleted**: files that were removed.

## Plan Mode

When calling `ExitPlanMode`, post a short TL;DR in the accompanying chat message (2–4 lines): the goal, the approach in one sentence, and roughly what will change. Keep the plan file itself fully detailed — the chat summary is just for skimming.

**Plan mode is strictly read-only.** Do not modify files by any means until `ExitPlanMode` is called. This includes Bash write patterns: `sed -i`, `tee`, output redirection (`>`, `>>`), heredocs to files (`cat <<EOF > file`), `python -c "...write..."`, `git commit`, `git add`, `gh pr ...`, and MCP write tools. Describe changes in the plan — don't apply them.