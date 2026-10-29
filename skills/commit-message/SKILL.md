---
name: commit-message
description: Write a commit message (one subject line plus short footnote lines) for the current changes and print it to the chat, without committing anything. English by default; Turkish only when the user explicitly asks for Turkish. Use when the user invokes /commit-message, or when a commit workflow (e.g. the project's CLAUDE.md) says to generate the commit message.
---

# commit-message

Produce a commit message for the current changes: one subject line, then
footnotes with the details. Print it and stop. No commit, no staging, no file
writes, no summary.

## 1. Pick the language

English, unless the user explicitly asks for Turkish — e.g. `/commit-message
tr`, `/commit-message turkish`, "Türkçe yaz", "commit in Turkish". Don't infer
Turkish from the conversation language, the repo's history, or a previous
commit; only an explicit request switches it.

## 2. Read the changes

Staged first — that is what the user is about to commit:

```
git status --porcelain
git diff --staged --stat && git diff --staged
```

If nothing is staged, describe the working tree instead: `git diff --stat &&
git diff`, plus the untracked files listed by `git status --porcelain` — read
the new ones, since `git diff` never shows them and a new file usually carries
the intent of the whole change.

If there is nothing to describe, say so in one line and stop.

Read enough of the diff to know *why* the change was made. A message that names
the files that moved is a worse message than one that names the behavior that
changed.

## 3. Write the subject line

Both languages:

- One line, no trailing period. First letter capitalized.
- Aim for ~50 characters; hard stop at 72.
- Identifiers stay verbatim: file names, paths, flags, function names and
  config keys appear exactly as they do in the code (`settings.json`,
  `--no-verify`, `statusline.py`).
- Name the behavior that changed, not the file that was touched.
- One line, one change. If the diff does several unrelated things, describe the
  dominant one rather than chaining them with "and"/"ve"; the footnotes carry
  the rest.
- Match the repository's own subject convention: check `git log --oneline -10`.
  If subjects carry prefixes (`feat:`, `fix(ui):`), keep the prefix in English.
  Otherwise, plain subject.

### English (default)

- Imperative mood: "Add ...", "Fix ...", "Remove ...", "Update ..." — the
  subject completes "This commit will ...". Never "Added" or "Adds".
- "Shorten long working directory in statusline", not "Update statusline.py".

### Turkish (only when asked)

- Passive past (edilgen çatı, -DI'lı geçmiş zaman): "... eklendi",
  "... düzeltildi", "... kaldırıldı", "... güncellendi". Never the imperative
  ("ekle", "düzelt") — the history records what was done, it does not give
  orders.
- The passive promotes the object to subject, so it loses the accusative
  suffix: "uzun çalışma dizini kısaltıldı", not "uzun çalışma dizinini
  kısaltıldı".
- Real Turkish characters — ç ğ ı İ ö ş ü — never their ASCII lookalikes.
- Attach Turkish suffixes to identifiers with an apostrophe when needed:
  `settings.json'a`, `statusline.py'de`.
- Terms Turkish developers keep in English stay in English — commit, branch,
  hook, cache, skill, statusline. Don't force a translation ("dal",
  "önbellek") unless the repo's own history uses one.
- "Statusline'da uzun dizin yolu kısaltıldı", not "statusline.py güncellendi".

## 4. Write the footnotes

After one blank line, 1-5 lines starting with `- `, each one change and, where
it is not obvious, why it was made. Same language and style as the subject.
Describe behaviour, not file lists. Keep each line under ~100 characters.

## 5. Output

Print the message as one code block and nothing else — no preamble, no
explanation, no offer to commit. The user's next action is to copy it.

```
Shorten long working directory in statusline

- Show the home directory as ~
- Truncate the middle of paths over 40 characters with …
```

Turkish:

```
Statusline'da uzun çalışma dizini kısaltıldı

- Ana dizin yolu ~ ile gösterildi
- 40 karakteri aşan yolların ortası … ile kısaltıldı
```

Never run `git commit` or `git add` from this skill, and never write the
message to a file. When the user invokes /commit-message directly, print the
message and stop — the user commits themselves. Only when a commit workflow
(the user asked to commit, and e.g. CLAUDE.md says to use this skill) invoked
it, hand the message back and continue with that workflow's next step.
