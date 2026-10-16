#!/bin/sh
# Install (or update) the Robin-Video skill for Claude Code into ~/.claude/skills/robin-video.
# Usage: sh install.sh        (set CLAUDE_SKILLS_DIR to install somewhere else)
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="$HERE/robin-video"
DEST="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}/robin-video"

if [ ! -f "$SRC/SKILL.md" ]; then
  echo "Can't find robin-video/SKILL.md next to this script. Unzip the whole folder and run install.sh from it."
  exit 1
fi

mkdir -p "$DEST"
if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete --exclude '.venv' --exclude '__pycache__' --exclude '*.pyc' --exclude '.DS_Store' "$SRC/" "$DEST/"
else
  rm -rf "$DEST" && mkdir -p "$DEST" && cp -R "$SRC/." "$DEST/"
fi
chmod +x "$DEST/scripts/hf" "$DEST/scripts/setup_voice.sh"
echo "✓ Robin-Video installed at $DEST"

missing=0
if command -v uv >/dev/null 2>&1; then
  (cd "$DEST/scripts" && uv sync --quiet) && echo "✓ Document tools ready (uv)"
else
  echo "✗ uv not found: install it with 'brew install uv' (needed to read PDFs, decks and Word files)"; missing=1
fi
if command -v ffmpeg >/dev/null 2>&1 && command -v ffprobe >/dev/null 2>&1; then
  echo "✓ ffmpeg found"
else
  echo "✗ ffmpeg not found: install it with 'brew install ffmpeg'"; missing=1
fi
if command -v node >/dev/null 2>&1 && node -e 'process.exit(+process.versions.node.split(".")[0] >= 22 ? 0 : 1)'; then
  echo "✓ Node.js $(node --version) found"
else
  echo "✗ Node.js 22 or newer not found: install it with 'brew install node'"; missing=1
fi

echo
if [ "$missing" -eq 0 ]; then
  echo "All set. Restart Claude Code, then try:  /robin-video your-document.pdf"
else
  echo "Install the missing tools above, then run 'sh install.sh' again."
fi
echo "Optional narration (--voice): run $DEST/scripts/setup_voice.sh once."
