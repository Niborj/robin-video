#!/bin/sh
# One-time setup for Robin-Video narration with local Kokoro TTS (offline after the first model download).
# Creates an isolated Python 3.12 venv in ~/.cache/robin-video/voice-venv; voice.py finds it automatically.
set -e
command -v uv >/dev/null 2>&1 || { echo "uv is required: https://docs.astral.sh/uv/"; exit 1; }
mkdir -p "$HOME/.cache/robin-video"
cd "$HOME/.cache/robin-video"
[ -x voice-venv/bin/python ] || uv venv --python 3.12 voice-venv
uv pip install --python voice-venv/bin/python kokoro-onnx soundfile
voice-venv/bin/python -c "import kokoro_onnx, soundfile; print('Kokoro ready:', '$HOME/.cache/robin-video/voice-venv/bin/python')"
