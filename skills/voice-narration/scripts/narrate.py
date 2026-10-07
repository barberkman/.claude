"""Narrate text with Kokoro neural TTS into a loudness-normalised CBR MP3 plus a timing JSON.

Input is a .txt file (segments separated by blank lines), a .json file (a list of segment strings,
or a list of lists of pre-split sentences), or --text. Each segment is split into sentences, every
sentence is synthesised separately, and the JSON records where each segment and sentence starts and
ends, so a player can drive captions and seek to any segment.

    narrate.py script.txt --out narration.mp3
    narrate.py script.json --voice af_heart,bm_george --out audio/narration.mp3   # one file per voice
    narrate.py --text "Hello there." --out hello.mp3
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HOME = Path(os.environ.get('KOKORO_HOME') or Path(os.environ.get('LOCALAPPDATA') or Path.home() / '.cache') / 'kokoro-tts')
VENV_PY = HOME / 'venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')

try:
    import numpy as np
    import kokoro_onnx  # noqa: F401  (imported here only to detect the environment)
except ImportError:
    if VENV_PY.exists() and Path(sys.executable).resolve() != VENV_PY.resolve():
        sys.exit(subprocess.call([str(VENV_PY), __file__, *sys.argv[1:]]))
    sys.exit(f'Kokoro is not installed. Run: python "{Path(__file__).with_name("setup.py")}"')

SR = 24000
LANGS = {'a': 'en-us', 'b': 'en-gb', 'e': 'es', 'f': 'fr-fr', 'h': 'hi', 'i': 'it', 'p': 'pt-br'}
# English voices, best first, with the overall grade from the model card (hexgrad/Kokoro-82M VOICES.md).
VOICES = {
    'af_heart': 'A', 'af_bella': 'A-', 'af_nicole': 'B-', 'bf_emma': 'B-', 'am_michael': 'C+', 'am_fenrir': 'C+',
    'am_puck': 'C+', 'af_aoede': 'C+', 'af_kore': 'C+', 'af_sarah': 'C+', 'bm_george': 'C', 'bm_fable': 'C',
    'bf_isabella': 'C', 'af_alloy': 'C', 'af_nova': 'C', 'af_sky': 'C-', 'bm_lewis': 'D+', 'af_jessica': 'D',
    'af_river': 'D', 'am_echo': 'D', 'am_eric': 'D', 'am_liam': 'D', 'am_onyx': 'D', 'bf_alice': 'D', 'bf_lily': 'D',
    'bm_daniel': 'D', 'am_santa': 'D-', 'am_adam': 'F+',
}
OTHER_LANGUAGE_VOICES = ['ef_dora', 'em_alex', 'em_santa', 'ff_siwis', 'hf_alpha', 'hf_beta', 'hm_omega', 'hm_psi', 'if_sara',
                         'im_nicola', 'pf_dora', 'pm_alex', 'pm_santa']


def describe(v):
    accent = {'a': 'US English', 'b': 'UK English'}.get(v[0], LANGS.get(v[0], v[0]))
    return f"{v:<12} {accent:<11} {'female' if v[1] == 'f' else 'male':<7} grade {VOICES.get(v, '-')}"

# --- text preparation ------------------------------------------------------------------------
SENTENCE_END = re.compile(r'(?<=[.!?])\s+(?=[A-Z0-9"\'(])')
# Code-ish tokens a TTS model mispronounces. Order matters: specific before general.
LEXICON = [
    (r'C\+\+', 'C plus plus'), (r'C#', 'C sharp'), (r'\bJSON\b', 'Jason'), (r'\bYAML\b', 'yammel'),
    (r'\bSQL\b', 'sequel'), (r'\bGUI\b', 'gooey'), (r'\bWASM\b', 'wasm'),
    (r'\.json\b', ' dot Jason'), (r'\.py\b', ' dot pie'), (r'\.md\b', ' dot M D'), (r'\.txt\b', ' dot text'),
    (r'\.js\b', ' dot J S'), (r'\.ts\b', ' dot T S'), (r'\.cpp\b', ' dot C P P'), (r'\.hpp\b', ' dot H P P'),
    (r'\.h\b', ' dot H'), (r'\.cs\b', ' dot C S'), (r'\.bat\b', ' dot bat'), (r'\.sh\b', ' dot S H'),
    (r'\.exe\b', ' dot exe'), (r'\.dll\b', ' dot D L L'), (r'\.csv\b', ' dot C S V'), (r'\.html?\b', ' dot H T M L'),
    (r'\.qml\b', ' dot Q M L'), (r'\.cmake\b', ' dot cmake'), (r'\.ini\b', ' dot I N I'),
    (r'(\d)\s*ms\b', r'\1 milliseconds'), (r'(\d)\s*Hz\b', r'\1 hertz'), (r'(\d)\s*MB\b', r'\1 megabytes'),
    (r'(\d)\s*GB\b', r'\1 gigabytes'), (r'(\d)\s*KB\b', r'\1 kilobytes'), (r'→', ' to '), (r'&&', ' and '),
]
WORDS_IN_CAPS = {'OK', 'AND', 'OR', 'NOT', 'IF', 'THE', 'ALL', 'NONE', 'TRUE', 'FALSE', 'NULL', 'ON', 'OFF', 'YES', 'NO', 'TODO', 'FIXME'}


def speakable(text, lexicon):
    """Rewrite one sentence so code identifiers are read naturally; captions keep the original text."""
    for word, say in lexicon.items():
        text = re.sub(r'(?<![\w.])' + re.escape(word) + r'(?![\w])', say, text)
    for pat, rep in LEXICON:
        text = re.sub(pat, rep, text)
    text = text.replace('_', ' ')
    text = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', text)          # camelCase → camel Case
    text = re.sub(r'\b([A-Z]{2,5})(s?)\b', lambda m: m.group(0) if m.group(1) in WORDS_IN_CAPS else ' '.join(m.group(1)) + m.group(2), text)
    return re.sub(r'\s{2,}', ' ', text).strip()


def split_sentences(segment, max_len=190, soft=160):
    """Sentence-sized pieces keep Kokoro's prosody stable and give fine-grained caption timing."""
    out = []
    for sent in SENTENCE_END.split(segment.strip()):
        if len(sent) <= max_len:
            out.append(sent)
            continue
        cur = ''
        for part in re.split(r'(?<=[,;:])\s+', sent):
            if cur and len(cur) + 1 + len(part) > soft:
                out.append(cur)
                cur = part
            else:
                cur = f'{cur} {part}' if cur else part
        if cur:
            out.append(cur)
    return [s for s in out if s.strip()]


def load_segments(args):
    if args.text:
        raw = [args.text]
    else:
        path = Path(args.input)
        if path.suffix.lower() == '.json':
            raw = json.loads(path.read_text(encoding='utf-8'))
            raw = raw.get('segments', raw) if isinstance(raw, dict) else raw
        else:
            raw = [p for p in re.split(r'\n\s*\n', path.read_text(encoding='utf-8')) if p.strip()]
    return [list(s) if isinstance(s, list) else split_sentences(' '.join(s.split())) for s in raw]


# --- synthesis -------------------------------------------------------------------------------
_kokoro = None


def _init(threads):
    global _kokoro
    import onnxruntime as ort
    from kokoro_onnx import Kokoro
    so = ort.SessionOptions()
    so.intra_op_num_threads, so.inter_op_num_threads = threads, 1
    session = ort.InferenceSession(str(HOME / 'kokoro-v1.0.onnx'), so, providers=['CPUExecutionProvider'])
    _kokoro = Kokoro.from_session(session, str(HOME / 'voices-v1.0.bin'))


def _synth(task):
    voice, index, sentences, speed, lang = task
    clips = []
    for s in sentences:
        audio, _ = _kokoro.create(s, voice=voice, speed=speed, lang=lang)
        clips.append(np.asarray(audio, dtype=np.float32))
    return voice, index, clips


def loudness(pcm, target_rms=0.1, ceiling=0.95, block=120):
    """Bring active speech to about -20 dBFS RMS, then catch peaks with a smoothed limiter."""
    active = pcm[np.abs(pcm) > 1e-3]
    rms = float(np.sqrt(np.mean(active ** 2))) if active.size else 1.0
    y = pcm * (target_rms / max(rms, 1e-6))
    n = -(-len(y) // block) * block
    env = np.abs(np.pad(y, (0, n - len(y)))).reshape(-1, block).max(axis=1)
    env = np.maximum(env, np.maximum(np.concatenate([[0.0], env[:-1]]), np.concatenate([env[1:], [0.0]])))
    gain = np.repeat(np.minimum(1.0, ceiling / np.maximum(env, 1e-9)), block)[:len(y)]
    gain = np.convolve(gain, np.ones(240) / 240, mode='same')
    return np.clip(y * gain, -0.99, 0.99)


def assemble(voice, segments, clips, args, out_mp3):
    import lameenc
    parts, seg_times, sent_times, cur = [], [], [], 0.0
    for i in range(len(segments)):
        times = []
        for clip in clips[i]:
            times.append([round(cur, 3), round(cur + len(clip) / SR, 3)])
            parts += [clip, np.zeros(int(args.gap * SR), np.float32)]
            cur += len(clip) / SR + args.gap
        parts.append(np.zeros(int(args.segment_gap * SR), np.float32))
        cur += args.segment_gap
        seg_times.append([times[0][0], times[-1][1]] if times else [round(cur, 3), round(cur, 3)])
        sent_times.append(times)
    pcm = loudness(np.concatenate(parts)) if parts else np.zeros(1, np.float32)
    pcm16 = (pcm * 32767).astype('<i2')
    enc = lameenc.Encoder()
    enc.set_bit_rate(args.bitrate)
    enc.set_in_sample_rate(SR)
    enc.set_channels(1)
    enc.set_quality(2)
    out_mp3.parent.mkdir(parents=True, exist_ok=True)
    out_mp3.write_bytes(enc.encode(pcm16.tobytes()) + enc.flush())
    if args.wav:
        import soundfile as sf
        sf.write(out_mp3.with_suffix('.wav'), pcm16, SR, subtype='PCM_16')
    meta = {'voice': voice, 'sample_rate': SR, 'bitrate_kbps': args.bitrate, 'dur': round(cur, 3),
            'segments': seg_times, 'sentences': sent_times, 'texts': segments}
    out_mp3.with_suffix('.json').write_text(json.dumps(meta, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    return cur


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('input', nargs='?', help='.txt (blank-line separated segments) or .json (list of segments)')
    ap.add_argument('--text', help='narrate this text instead of a file')
    ap.add_argument('--out', default='narration.mp3', help='output MP3; with several voices, <stem>.<voice>.mp3')
    ap.add_argument('--voice', default='af_heart', help='voice id, or a comma-separated list (default af_heart)')
    ap.add_argument('--speed', type=float, default=1.0, help='speaking rate, 0.8-1.2 sounds natural')
    ap.add_argument('--lang', help='espeak language; default follows the voice prefix (a: en-us, b: en-gb)')
    ap.add_argument('--plain', action='store_true', help='skip the code-term pronunciation rewrite (plain prose)')
    ap.add_argument('--lexicon', help='JSON object of extra pronunciations, e.g. {"AnSiF": "Ansif", "PSMW": "P S M W"}')
    ap.add_argument('--gap', type=float, default=0.14, help='silence between sentences, seconds')
    ap.add_argument('--segment-gap', type=float, default=0.22, help='extra silence after each segment, seconds')
    ap.add_argument('--bitrate', type=int, default=32, help='CBR MP3 bitrate in kbps (32 is clear for speech)')
    ap.add_argument('--workers', type=int, default=max(1, min(8, (os.cpu_count() or 2) // 2)))
    ap.add_argument('--threads', type=int, default=2, help='ONNX threads per worker')
    ap.add_argument('--wav', action='store_true', help='also write a 16-bit WAV next to the MP3')
    ap.add_argument('--list-voices', action='store_true', help='print the available voices with their grades and exit')
    args = ap.parse_args()
    if args.list_voices:
        print('\n'.join(describe(v) for v in VOICES))
        print('other languages (use only for text in that language): ' + ', '.join(OTHER_LANGUAGE_VOICES))
        return
    if not args.text and not args.input:
        ap.error('give an input file or --text')
    unknown = [v.strip() for v in args.voice.split(',') if v.strip() and v.strip() not in VOICES and v.strip() not in OTHER_LANGUAGE_VOICES]
    if unknown:
        sys.exit(f'Unknown voice: {", ".join(unknown)}. Run with --list-voices to see the choices.')
    for f in ('kokoro-v1.0.onnx', 'voices-v1.0.bin'):
        if not (HOME / f).exists():
            sys.exit(f'Missing {HOME / f}. Run: python "{Path(__file__).with_name("setup.py")}"')

    segments = load_segments(args)
    lexicon = json.loads(Path(args.lexicon).read_text(encoding='utf-8')) if args.lexicon else {}
    spoken = [[s if args.plain else speakable(s, lexicon) for s in seg] for seg in segments]
    voices = [v.strip() for v in args.voice.split(',') if v.strip()]
    out = Path(args.out)
    tasks = [(v, i, spoken[i], args.speed, args.lang or LANGS.get(v[0], 'en-us')) for v in voices for i in range(len(spoken))]
    done = {v: {} for v in voices}
    t0 = time.time()

    from multiprocessing import Pool
    with Pool(min(args.workers, len(tasks)) or 1, initializer=_init, initargs=(args.threads,)) as pool:
        for voice, i, clips in pool.imap_unordered(_synth, tasks):
            done[voice][i] = clips
            if len(done[voice]) == len(segments):
                target = out if len(voices) == 1 else out.with_name(f'{out.stem}.{voice}{out.suffix}')
                dur = assemble(voice, segments, [done[voice][k] for k in range(len(segments))], args, target)
                print(f'{voice}: {dur / 60:.1f} min -> {target} ({target.stat().st_size / 1e6:.2f} MB) '
                      f'[{time.time() - t0:.0f}s elapsed]', flush=True)


if __name__ == '__main__':
    main()
