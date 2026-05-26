#!/usr/bin/env bash
BRANCH=$(git branch --show-current 2>/dev/null)
if [[ "$BRANCH" == "main" ]]; then
  echo "[ブロック] mainブランチへの直接編集は禁止されています。" >&2
  echo "feature ブランチを作成してから作業してください: git checkout -b feature/xxx" >&2
  exit 2
fi
exit 0
