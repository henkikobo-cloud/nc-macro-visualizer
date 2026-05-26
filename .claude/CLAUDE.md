# CLAUDE.md（nctool プロジェクト）
最終更新: 2026-05-26

---

## プロジェクト概要

**NC Macro Visualizer**：FANUC系NCマクロを人間が読みやすいフローチャートへ翻訳する読解支援ツール。

- 対象ユーザー：NCマクロ初心者・現場作業者（PC操作が得意でない人）
- 主要インターフェース：Webデモ（一般ユーザー）・CLI（開発者）
- 絶対にしないこと：実機動作の保証・NCプログラムの実行・加工シミュレーション

---

## アーキテクチャ

```
src/nc_macro_visualizer/
├─ parser/        正規表現ベースNCパーサ（ParsedLine を生成）
├─ analyzer/      AnalysisResult を生成（変数・制御フロー・警告の集約）
├─ models/        データクラス群（ParsedLine / AnalysisResult 等）
├─ renderer/      旧レンダラー（markdown / json_renderer / mermaid）
├─ renderers/     新レンダラー（pad_html / pad_text）
├─ flowchart/     BeginnerFlow・CFG・structurizer（v0.2.0〜）
├─ profiles/      FANUCマクロ定義（Mコード説明・unknown判定）
└─ cli/           CLIエントリポイント（main.py）

web/              Webデモ（静的HTML/CSS/JS・GitHub Pages対応）
lp/               LP・OGP画像
tests/            pytestテスト群（52件）
samples/          サンプルNCファイル（01〜06）
schemas/          JSON Schema定義
docs/             設計ドキュメント・計画書
```

### データフロー

```
NC テキスト
  → parser（ParsedLine[]）
  → analyzer（AnalysisResult）
  → flowchart/builder（BeginnerFlow）
  → renderer/renderers（JSON / Markdown / HTML 出力）
```

---

## CLI 出力形式

| フラグ | 出力ファイル | バージョン |
|--------|-------------|-----------|
| デフォルト | `report.md` `analysis.json` `flow.mmd` | v0.1.0〜 |
| `--beginner` | `beginner_flow.json` | v0.2.0〜 |
| `--nassi` | `nassi_shneiderman.html` | v0.2.0〜 |
| `--text` | `structured_text.md` | v0.2.0〜 |
| `--pad-html` | `pad.html` | v0.3.0-dev |
| `--pad-text` | `pad.txt` | v0.3.0-dev |
| `--cfg` | `cfg.json` | v0.3.0-dev |
| `--all-views` | 全出力 | v0.3.0-dev |

---

## 開発規約

### バージョン管理
- `pyproject.toml` の version を実態に合わせて更新すること
- 現在の実態：v0.3.0-dev（CHANGELOG参照）

### テスト
- 変更前後に必ず実行すること
```bash
.venv/bin/python -m pytest
```
- 既存 52 件が全パスしていることを確認してから PR を出す
- 新機能追加時は対応するテストも追加する

### パーサの扱い
- 現状は正規表現ベース（AST未実装）
- 複雑なNCへの対応には構造的な限界がある
- パーサの大規模改修は別バージョンで計画する（TODO.md 参照）

### Mコードポリシー（厳守）
- 未知のMコードを意味推測・勝手に解釈しない
- 未知Mコードの表示：`意味の確認が必要なMコード`
- サポートメッセージ：`機械の説明書、PMC、ビルダー設定を確認してください。`

### Web/Python の分離
- Web デモ（`web/app.js`）は JS 独自実装
- Python エンジンの出力スキーマに寄せていくが、完全統合は v0.3.0 アウトオブスコープ
- Pyodide 統合は将来課題

---

## よく使うコマンド

```bash
# テスト実行
.venv/bin/python -m pytest

# CLIで全ビュー生成（動作確認用）
python3 nctool.py samples/04_variables.nc -o output --all-views

# Webデモをローカルで確認
python3 -m http.server 8000
# → http://localhost:8000/web/

# LPをローカルで確認
# → http://localhost:8000/lp/
```

---

## 有料化方針（現時点）

戦略書上は **Stream C・フェーズ3（18〜36ヶ月後）** に位置づけ。

**今フェーズでやること：**
- 開発進捗をSNSで積極発信する
- Webデモの品質を上げて「試してみたい」と思わせる

**今フェーズでやらないこと：**
- 有料版の実装
- 決済導線の構築
- SaaS化

---

## AI組織での役割分担

| タスク | 担当 |
|--------|------|
| 設計判断・コード品質・アーキテクチャ | Claude Code |
| 開発進捗のSNS投稿文生成 | Codex CLI |
| 競合調査・類似ツール調査 | Antigravity CLI |
| 実際のSNS投稿・画像生成 | Python スクリプト |

**Claude Code が定型のコンテンツ生成をしない。SNS投稿文はCodexに委任する。**

---

## 参照ドキュメント

- `docs/project_policy_spec_status.md`：製品ポリシー・仕様・現状（最重要）
- `docs/v0.3_nassi_shneiderman_plan.md`：v0.3.0 設計方針
- `TODO.md`：既知の課題・次の実装優先度
- `CHANGELOG.md`：バージョン別の変更履歴
- `limitations.md`：ツールの限界・スコープ外
- `schemas/`：JSON Schema定義（実装前に必ず確認）
