#!/bin/sh
# Rebuild dist/robin-video-skill.zip (skill + recipient README + installer) from the current source.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STAGE="$(mktemp -d)/robin-video-skill"
mkdir -p "$STAGE"
cp "$ROOT/packaging/README.md" "$ROOT/packaging/install.sh" "$STAGE/"
rsync -a --exclude '.venv' --exclude '__pycache__' --exclude '*.pyc' --exclude '.DS_Store' "$ROOT/robin-video/" "$STAGE/robin-video/"
chmod +x "$STAGE/install.sh" "$STAGE/robin-video/scripts/hf" "$STAGE/robin-video/scripts/setup_voice.sh"
mkdir -p "$ROOT/dist"
rm -f "$ROOT/dist/robin-video-skill.zip"
(cd "$(dirname "$STAGE")" && COPYFILE_DISABLE=1 zip -r -X -q "$ROOT/dist/robin-video-skill.zip" robin-video-skill -x '*.DS_Store')
rm -rf "$(dirname "$STAGE")"
echo "Built $ROOT/dist/robin-video-skill.zip ($(du -h "$ROOT/dist/robin-video-skill.zip" | cut -f1))"
