#!/bin/sh
# Install (or update) the Robin-Video skill into ~/.claude/skills/robin-video from this folder.
set -e
SRC="$(cd "$(dirname "$0")/robin-video" && pwd)"
DEST="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}/robin-video"
mkdir -p "$DEST"
rsync -a --delete --exclude '.venv' --exclude '__pycache__' --exclude '*.pyc' --exclude '.DS_Store' "$SRC/" "$DEST/"
chmod +x "$DEST/scripts/hf" "$DEST/scripts/setup_voice.sh"
echo "Robin-Video installed at $DEST"
command -v uv >/dev/null 2>&1 && (cd "$DEST/scripts" && uv sync --quiet && echo "Python tools ready (uv)") || echo "Install uv (https://docs.astral.sh/uv/) for document ingestion."
command -v ffmpeg >/dev/null 2>&1 || echo "Install ffmpeg (brew install ffmpeg) for rendering and delivery."
node -e 'process.exit(+process.versions.node.split(".")[0] >= 22 ? 0 : 1)' 2>/dev/null || echo "HyperFrames needs Node.js 22 or newer."
