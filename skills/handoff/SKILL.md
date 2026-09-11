---
name: handoff
description: Turn the current discussion into one standalone implementation prompt for a separate, independent Claude Code session — saying what to do and why, and leaving the technical details to whoever implements it. Use only when the user explicitly invokes this skill by name (/handoff); never trigger on your own, even when a conversation looks ready to hand off.
---

# Handoff

The user has been working something out with you and now wants to hand the
implementation to a different Claude Code session. Your output is that prompt,
which the user copies and pastes. You are writing a brief, not doing the work.

## Why the prompt takes this shape

The session that receives this prompt starts with no conversation history and
its own engineering judgment. Its judgment is fine — what it cannot get
anywhere else is **intent, constraints, and the decisions already made here**.
That is the whole payload.

So prescribing mechanism hurts twice: it wastes judgment that was going to be
applied anyway, and it silently freezes choices nobody actually made. When you
write "add a helper in `utils/`", the receiving session treats it as a
requirement — even though you invented it thirty seconds ago and the user never
saw it. Now it is locked in, in code, unexamined.

Conversely, under-specifying intent is the other failure: if the prompt omits a
constraint the user cares about, the receiving session cannot guess it and will
confidently build the wrong thing.

Aim for: everything the user decided, nothing you decided.

## 1. Gather from the discussion

Read back over the conversation and pull out:

- **The goal**, and the problem behind it — why this is wanted, not just what.
- **Decisions the user made**, including alternatives considered and rejected,
  and why. This is the highest-value content in the prompt; without it the
  receiving session re-litigates settled questions and may reach the opposite
  conclusion.
- **Hard constraints** — must / must not, compatibility, performance,
  behavior that cannot change.
- **Where the work lands** — repo-relative paths, existing patterns or
  utilities identified during the discussion, the module or layer involved.
- **What "done" looks like** — observable behavior, tests, commands to run.
- **What is out of scope** — especially things you two explicitly set aside.

Use only material that came from the discussion. If the prompt seems to need
something that was never discussed, that is a gap to ask about, not to fill in.

## 2. Close the gaps, then write

Before drafting, look for anything **materially undecided**: a point where two
reasonable readings lead to different implementations. Ask those in a single
`AskUserQuestion` call (group up to four), then write the prompt.

The discriminator for what to ask:

- **Ask about intent** — product behavior, scope boundaries, priorities,
  constraints, what happens in a case you two never covered. Only the user
  knows these.
- **Don't ask about implementation** — library choice, file layout, naming,
  error-handling style, test framework. Delegating exactly those is the point
  of this skill; asking the user to decide them defeats it.

If nothing material is open, skip straight to writing. Don't manufacture
questions to look thorough.

## 3. Write the prompt

Use these sections. Drop any section with nothing real to say — an empty
"Out of scope" heading is noise, and padding it with invented content is worse.

```
## Goal
<the outcome and why it's wanted, 1-2 sentences>

## Context
<where this lives, how it behaves today, relevant repo-relative paths,
existing code worth reusing>

## What to do
<the requirements, as outcomes>

## Decisions already made
<settled points; for each, the alternative rejected and why>

## Out of scope
<what not to touch>

## Done when
<criteria someone can actually check>
```

## What vs. how

**Don't** (prescribes mechanism):
> Add a `debounce` helper in `src/utils/timing.ts` and call it from the
> `onChange` handler with a 300ms timeout.

**Do** (states the outcome):
> Typing in the search box shouldn't fire a request per keystroke — it should
> wait until the user pauses.

**Don't:**
> Create a migration adding a nullable `archived_at timestamptz`, then filter
> on it in the repository query.

**Do:**
> Users need to archive a project without deleting it. Archived projects
> shouldn't appear in the default list, but must stay retrievable.

**The exception that matters:** a technical detail *the user decided* is a
constraint, and belongs in the prompt. The test is not "is this technical?" but
**"who decided this?"** If the user chose it, state it under *Decisions already
made*, with the reason. If you would be choosing it right now, leave it out.

## 4. Check the draft before printing it

- Does it stand alone read cold? No "as we discussed", no "the approach above",
  no pronoun pointing back at this conversation.
- Any sentence prescribing a mechanism you invented? Cut it, or turn it into
  the outcome it was serving.
- Are the *Done when* items checkable by someone who wasn't here?
- Anything the receiving session can read for itself — file contents, function
  bodies, config — referenced by path rather than pasted?
- Paths are repo-relative. Absolute paths, scratchpad directories, and other
  state of this session won't exist over there.
- Would a competent engineer reading only this build the right thing?

## 5. Output

Print the prompt as exactly one fenced code block, with at most one line of
chat around it — the user's next action is to copy it, so explanation and
summary just get in the way. Use a four-backtick fence if the prompt itself
contains a code block.

Say nothing about branches, commits, or pull requests unless the user said
where the work should land.
