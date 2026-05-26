#!/usr/bin/env bash
FILE="$1"
if [[ "$FILE" == *.py ]]; then
  echo "[post-edit] Pythonファイルを検出。pytest を自動実行します..."
  if ! .venv/bin/python -m pytest --tb=short -q; then
    echo "[警告] テストが失敗しました。コードを確認してください。"
  fi
fi
exit 0
