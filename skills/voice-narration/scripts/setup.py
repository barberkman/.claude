"""Install the Kokoro TTS environment once: a venv plus the model files, in KOKORO_HOME.

KOKORO_HOME defaults to %LOCALAPPDATA%\\kokoro-tts (or ~/.cache/kokoro-tts). Safe to re-run:
existing pieces are kept, missing ones are added.

    python setup.py [--copy-models-from DIR]
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

HOME = Path(os.environ.get('KOKORO_HOME') or Path(os.environ.get('LOCALAPPDATA') or Path.home() / '.cache') / 'kokoro-tts')
VENV_PY = HOME / 'venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
MODEL_URL = 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/'
MODEL_FILES = {'kokoro-v1.0.onnx': 300_000_000, 'voices-v1.0.bin': 25_000_000}
PACKAGES = ['kokoro-onnx', 'soundfile', 'lameenc', 'numpy']


def base_python():
    """onnxruntime wheels lag new Python releases, so prefer an established minor version."""
    if os.name == 'nt' and shutil.which('py'):
        for v in ('3.12', '3.11', '3.13', '3.10'):
            if subprocess.run(['py', f'-{v}', '-c', 'pass'], capture_output=True).returncode == 0:
                return ['py', f'-{v}']
    return [sys.executable]


def fetch(name, min_size, copy_from):
    dst = HOME / name
    if dst.exists() and dst.stat().st_size >= min_size:
        return 'present'
    src = Path(copy_from) / name if copy_from else None
    if src and src.exists():
        shutil.copy2(src, dst)
        return 'copied'
    # curl uses the Windows certificate store; Python's own SSL check fails behind the corporate proxy.
    cmd = ['curl', '-L', '--fail', '--silent', '--show-error', '-o', str(dst), MODEL_URL + name]
    if os.name == 'nt':
        cmd.insert(1, '--ssl-no-revoke')
    subprocess.run(cmd, check=True)
    return 'downloaded'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--copy-models-from', help='folder that already holds kokoro-v1.0.onnx and voices-v1.0.bin')
    args = ap.parse_args()
    HOME.mkdir(parents=True, exist_ok=True)
    if not VENV_PY.exists():
        subprocess.run(base_python() + ['-m', 'venv', str(HOME / 'venv')], check=True)
    subprocess.run([str(VENV_PY), '-m', 'pip', 'install', '--quiet', '--disable-pip-version-check', *PACKAGES], check=True)
    for name, size in MODEL_FILES.items():
        print(f'{name}: {fetch(name, size, args.copy_models_from)}')
    subprocess.run([str(VENV_PY), '-c', 'import kokoro_onnx, lameenc, soundfile, numpy'], check=True)
    print(f'Kokoro ready in {HOME}')


if __name__ == '__main__':
    main()
