#!/bin/sh
set -e
REPO_ROOT="$(git rev-parse --show-toplevel)"
SRC_DIR="$REPO_ROOT/skills/acecamp-minutes-ingest/git-hooks"
DST_DIR="$REPO_ROOT/.git/hooks"

mkdir -p "$DST_DIR"
cp "$SRC_DIR/pre-commit" "$DST_DIR/pre-commit"
chmod +x "$DST_DIR/pre-commit"

echo "Installed hook: .git/hooks/pre-commit"
