---
name: voice-narration
description: Generate natural-sounding narration audio offline with the Kokoro neural TTS model; the user picks one or more of 28 English voices (af_heart, the best-rated, is recommended). Use when the user wants a voice-over, narration, spoken audio, an explainer or video voice, text read aloud into an audio file, or wants to replace robotic browser/SAPI speech. Produces a loudness-normalised CBR MP3 plus a timing JSON (per segment and per sentence) for captions and seeking. Runs locally, so the text never leaves the machine.
---

# voice-narration

Turn a script into natural speech with Kokoro (82M-parameter open-source TTS, Apache 2.0),
running locally on the CPU. Default to voice **`af_heart`**: it is the only voice its authors
grade A. Never send the user's text to an online TTS service instead; scripts often describe
internal code.

Everything heavy lives in `KOKORO_HOME` (default `%LOCALAPPDATA%\kokoro-tts`): a Python venv and
the two model files (~350 MB). Keep it out of the skill folder and out of project folders.

## 1. Make sure the environment exists

```
python "<skill>/scripts/setup.py"
```

Idempotent: it creates the venv (prefers Python 3.12, since onnxruntime wheels lag new Python
releases), installs `kokoro-onnx soundfile lameenc numpy`, and fetches `kokoro-v1.0.onnx` and
`voices-v1.0.bin` from the kokoro-onnx GitHub release. If the files already sit somewhere, add
`--copy-models-from <dir>` instead of downloading.

Behind the corporate proxy, Python's own SSL check fails ("Missing Authority Key Identifier") and
plain curl fails with error 35. The script therefore downloads with `curl --ssl-no-revoke`, which
uses the Windows certificate store. pip works normally.

## 2. Choose the voice

The user picks the voice; `af_heart` is only the recommendation.

- If the user already named a voice (in the request, as the skill argument such as
  `/voice-narration bm_george`, or in an earlier render for this project, whose JSON records
  `voice`), use it without asking.
- Otherwise ask once with AskUserQuestion before rendering anything long:
  - header `Voice`, question "Which voice should narrate?"
  - options, in this order: **Heart — US female, grade A (Recommended)**; **Bella — US female,
    A−**; **Michael — US male, C+**; **George — UK male, C**.
  - mention in the question that "Other" accepts any voice id from the table below
    (for example `bf_emma` or `am_puck`). Validate the answer with `--list-voices`.
- If the user is unsure, render a short sample in a few voices first and let them listen:
  `narrate.py --text "<one or two sentences from their script>" --voice af_heart,af_bella,am_michael,bm_george --out samples/voice-sample.mp3`
  produces `samples/voice-sample.<voice>.mp3` per voice in a few seconds.
- They can pick several voices; pass them comma-separated and every voice gets its own file.
- `narrate.py --list-voices` prints every voice with accent, gender and grade.

## 3. Prepare the script

- Write it for the ear: short sentences, one idea each, no parentheses or bullet fragments.
- Give the narration as segments. A segment is the unit a player seeks to or syncs an animation
  step with (a slide, a scene beat, a paragraph). In a `.txt` file, separate segments with a blank
  line; in `.json`, give a list of strings.
- Keep identifiers in the text as written (`genMatlab.py`, `ModelBase`, `C++`). `narrate.py`
  rewrites them for speech only ("gen Matlab dot pie", "Model Base", "C plus plus"); the timing
  JSON keeps the original text for captions. Use `--plain` for ordinary prose.
- For project-specific words, pass `--lexicon words.json` with exact spellings, e.g.
  `{"AnSiF": "Ansif", "PSMW": "P S M W", "FFSv1": "F F S v 1"}`. Listen for mispronounced names
  and add them here rather than misspelling the script.

## 4. Render

```
python "<skill>/scripts/narrate.py" script.txt --voice <chosen voice> --out narration.mp3
python "<skill>/scripts/narrate.py" script.json --voice af_heart,bm_george --out audio/narration.mp3
python "<skill>/scripts/narrate.py" --text "One quick sentence." --out test.mp3
```

`narrate.py` re-launches itself inside the venv, so any `python` works. It synthesises sentence by
sentence in parallel, joins them with short pauses (`--gap 0.14`, `--segment-gap 0.22`), normalises
speech to about -20 dBFS with a peak limiter, and writes:

- `narration.mp3`: 24 kHz mono, constant bitrate (`--bitrate 32`). Keep it CBR: browsers seek
  CBR MP3 accurately, so timestamps in the JSON stay valid after a seek.
- `narration.json`: `dur`, `segments` (`[start, end]` seconds per segment), `sentences` (per
  segment, `[start, end]` per sentence) and `texts` (the original sentences, for captions).
  `--wav` also writes a WAV.

With several voices, files are named `<stem>.<voice>.mp3`. Speed on this machine (16 cores):
about 2x faster than real time with the default 8 workers × 2 threads, so a 30-minute script takes
~5-6 minutes per voice. For long jobs, run it in the background and tell the user the estimate.

Verify before handing over: the printed duration should be plausible for the word count
(~150 words per minute), and `soundfile.read()` of the MP3 should match `dur` within a fraction of
a second. You cannot listen to the result; say so and let the user judge the voice.

## 5. Use it in a web page or video

- Play one MP3 per voice and drive everything from `audio.currentTime`: show the caption whose
  sentence range contains it, and pause at the end of a segment while the visuals catch up.
- To jump to segment *i*, set `audio.currentTime = segments[i][0]`. Wait for `loadedmetadata` before
  the first seek, and start playback from a click (autoplay rules).
- `audio.playbackRate` changes speed without changing pitch; divide JSON times by the rate for
  display.
- Publish the MP3 next to the page (`audio/mpeg`); an artifact page fetches it by relative path.

## Voices

English voices, with the authors' overall grades (from the model card's VOICES.md). Prefer the top
of the list. `a` = American (`en-us`), `b` = British (`en-gb`), `f`/`m` = female/male.

| Grade | Voices |
|---|---|
| A | `af_heart` (default) |
| A− | `af_bella` |
| B− | `af_nicole` (slow, whispery: about 50% longer audio), `bf_emma` |
| C+ | `am_michael`, `am_fenrir`, `am_puck`, `af_aoede`, `af_kore`, `af_sarah` |
| C | `bm_george`, `bm_fable`, `bf_isabella`, `af_alloy`, `af_nova` |
| C− | `af_sky` |
| D+ / D | `bm_lewis`, `af_jessica`, `af_river`, `am_echo`, `am_eric`, `am_liam`, `am_onyx`, `bf_alice`, `bf_lily`, `bm_daniel` |
| D− / F+ | `am_santa`, `am_adam` |

Good picks when the user wants variety: male US `am_michael`, female UK `bf_emma`, male UK
`bm_george`. The model also has Spanish, French, Hindi, Italian, Portuguese, Japanese and Chinese
voices (`e`, `f`, `h`, `i`, `p`, `j`, `z` prefixes); only use them for text in that language.

## Troubleshooting

- `Kokoro is not installed` or missing model files: run `setup.py`.
- Clipped words or odd stress in a long sentence: split it; sentences over ~190 characters are
  already cut at commas.
- A word is read wrong: add it to `--lexicon`; don't change the visible script.
- Voice sounds rushed or slow: `--speed 0.9`…`1.1`; keep the same speed for every segment.
