# Design Philosophy

NC Macro Visualizer は、NC マクロの「読解支援」を目的とするツールです。

現場に残った NC マクロは、制御構造、変数、ラベルジャンプ、サブプログラム呼び出しが絡み合い、初見では意図を追いにくいことがあります。このツールは、それらを実行するのではなく、人間が読むための手がかりに分解します。

## Principles

### 1. Do Not Pretend To Be A Machine

このツールは NC コントローラではありません。実機のパラメータ、PMC、ビルダー固有設定、マクロ変数の初期状態、工具補正、座標系、モーダル状態を再現しません。

そのため、出力は「動作結果」ではなく「読解用の整理情報」です。

### 2. Preserve Uncertainty

機械依存の情報を断定しません。

特に M コードは機械、メーカー、ビルダー、ユーザー改造に依存します。共通的に知られている M コード以外は `unknown` / `machine_specific` として扱い、意味を補完しません。

### 3. Prefer Explainable Output

出力は Markdown、JSON、Mermaid の 3 種類です。

- Markdown は人間のレビュー用です。
- JSON は他ツール連携や自動処理用です。
- Mermaid は処理フローの概観用です。

どの出力も、元の NC 行番号とコード断片を残す方針です。

### 4. Warn, Do Not Fail By Default

MVP では、未解決 `GOTO`、重複ラベル、未対応拡張子などを warning として出力します。

古い NC 資産には不完全な断片や外部依存が含まれることがあります。読解支援ツールとして、可能な限りレポートを生成し、問題点を明示する方針です。

### 5. Keep MVP Scope Small

v0.1.0 は regex ベースの軽量実装です。完全な AST やコントローラ方言対応よりも、まずは安全に読める成果物を出すことを優先しています。

## Current Architecture

- `parser`: 行単位のコメント除去、ラベル、変数、制御構文、M コード、呼び出しの抽出
- `analyzer`: 集計、warnings、変数依存、基本フローの構築
- `renderer`: Markdown、JSON、Mermaid 出力
- `profiles`: 共通 M コード説明
- `cli`: コマンドライン入口

## v0.1.0 Boundary

v0.1.0 は、次の境界で区切ります。

- 読解支援として有用なレポートを生成する。
- 実機動作、加工結果、M コード意味推定には踏み込まない。
- 不確実なものは warning または `unknown` として表現する。
- サンプル、テスト、出力形式を GitHub 公開できる状態にする。

