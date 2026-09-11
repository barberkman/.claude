---
name: commit-tr
description: Write a single-line Turkish commit message for the current changes and print it to the chat, without committing anything. Use only when the user explicitly invokes this skill by name (/commit-tr); never trigger on your own, not even when the user asks for a commit or for a commit message.
---

# commit-tr

Produce one Turkish commit subject line describing the current changes, print
it, and stop. No commit, no staging, no file writes, no summary.

## 1. Read the changes

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

## 2. Write the line

- Turkish, passive past (edilgen çatı, -DI'lı geçmiş zaman): "... eklendi",
  "... düzeltildi", "... kaldırıldı", "... güncellendi". Never the imperative
  ("ekle", "düzelt") — the history records what was done, it does not give
  orders.
- The passive promotes the object to subject, so it loses the accusative
  suffix: "uzun çalışma dizini kısaltıldı", not "uzun çalışma dizinini
  kısaltıldı".
- One line only. No body, no footnotes, no trailing period. First letter
  capitalized.
- Aim for ~50 characters; hard stop at 72.
- Real Turkish characters — ç ğ ı İ ö ş ü — never their ASCII lookalikes.
- Identifiers stay verbatim: file names, paths, flags, function names and
  config keys appear exactly as they do in the code (`settings.json`,
  `--no-verify`, `statusline.py`). Attach Turkish suffixes with an apostrophe
  when needed: `settings.json'a`, `statusline.py'de`.
- Terms Turkish developers keep in English stay in English — commit, branch,
  hook, cache, skill, statusline. Don't force a translation ("dal",
  "önbellek") unless the repo's own history uses one.
- Name the behavior that changed, not the file that was touched:
  "Statusline'da uzun dizin yolu kısaltıldı", not "statusline.py güncellendi".
- One line, one change. If the diff does several unrelated things, describe the
  dominant one rather than chaining them with "ve ... ve ...".
- Match the repository's own subject convention: check `git log --oneline -10`.
  If subjects carry prefixes (`feat:`, `fix(ui):`), keep the prefix in English
  and write the rest in Turkish. Otherwise, plain subject.

## 3. Output

Print the message as a single-line code block and nothing else — no preamble,
no explanation, no file list, no offer to commit. The user's next action is to
copy it.

```
Statusline'da uzun çalışma dizini kısaltıldı
```

Never run `git commit` or `git add` here, and never write the message to a
file. Committing is a separate request; wait for it.
