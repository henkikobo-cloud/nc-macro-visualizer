# /release

バージョン更新・CHANGELOG更新・gitタグ付けを行う。

## 引数
$ARGUMENTS にバージョン番号を指定（例: /release 0.3.0）

## 手順
1. `pyproject.toml` の `version` を指定バージョンに更新
2. `CHANGELOG.md` に新バージョンセクションを追加（日付・変更内容）
3. `git add pyproject.toml CHANGELOG.md`
4. `git commit -m "【Claude Code】v{version} リリース準備"`
5. `git tag v{version}`
6. タグ一覧を表示して確認

## 注意
- main ブランチへの直接コミットは pre-edit フックでブロックされる
- release ブランチ（例: release/0.3.0）で作業すること
