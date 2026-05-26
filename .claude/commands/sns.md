# /sns

開発進捗のSNS投稿文をCodex CLIに生成させる。

## 手順
1. 最新コミット3件を `git log --oneline -3` で取得
2. 以下のプロンプトでCodex CLIを呼び出す（Claude Codeは投稿文を生成しない）

```
codex "nctoolの開発進捗として、以下の変更をX（Twitter）投稿文に変換してください。
henkikoboペルソナ（製造業18年・AIと自動化を実体験から語る）で書くこと。
AIっぽい表現（〜が重要です、〜を意識しましょう等）は使わない。
変更内容: {git_log}"
```

3. 生成された投稿文を確認・承認後、Pythonスクリプトで投稿する
