# NC Macro Visualizer

NC Macro Visualizer は、FANUC 系の NC マクロを人間が読みやすい形に変換するための CLI ツールです。

このツールの目的は「読解支援」です。NC プログラムの実行、加工シミュレーション、工具軌跡生成、実機動作保証は行いません。

## Status

- Version: `v0.1.0`
- Scope: MVP stage 1 complete
- Interface: CLI
- Primary outputs:
  - Markdown report: `report.md`
  - Structured JSON: `analysis.json`
  - Mermaid flowchart: `flow.mmd`

## What This Tool Does

- NC マクロ内の `N` ラベルを抽出します。
- `#100` や `#<RESULT>` のような変数を抽出します。
- 変数の代入、参照、出現回数を整理します。
- 代入式から行単位の変数依存を抽出します。
- `IF ... GOTO`、`GOTO`、`IF ... THEN`、基本的な `WHILE ... DO` / `END` を検出します。
- `M98`、`G65` のサブプログラム / マクロ呼び出しを検出します。
- 一般的な M コードには共通説明を付けます。
- 未解決 `GOTO`、重複ラベル、未対応拡張子を warning として出力します。
- Mermaid 形式で読解用の処理フローを出力します。

## What This Tool Does Not Do

- 実機での動作を保証しません。
- NC プログラムを実行、エミュレート、検証しません。
- 加工結果、工具軌跡、干渉、衝突、サイクルタイムを推定しません。
- 機械固有 M コードの意味を推測しません。
- `unknown` と判定した M コードを勝手に解釈しません。
- コントローラごとの方言差を完全には吸収しません。

詳細は [limitations.md](limitations.md) を参照してください。

## Install

Python 3.10 以上を想定しています。

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[test]"
```

依存ライブラリなしでも CLI 本体は動きます。`pytest` はテスト用の optional dependency です。

## Usage

```bash
python3 nctool.py samples/04_variables.nc -o output
```

生成物:

```text
output/
├─ report.md
├─ analysis.json
└─ flow.mmd
```

## Sample Input

`samples/04_variables.nc`:

```nc
%
O1004
N10 #500 = #100 + #101
N20 #<RESULT> = #500
N30 IF [#<RESULT> GT 0] THEN #102 = 1
N40 M30
%
```

サブプログラム / マクロ呼び出しの代表例:

```nc
%
O1003
N10 M98 P2000
N20 G65 P3000 A1.0 B2.0
N30 M30
%
```

## Output Example: flow.mmd

```mermaid
flowchart TD
    START(["START"])
    END(["END"])
    N10["N10 #500 = #100 + #101"]
    N20["N20 #&lt;RESULT&gt; = #500"]
    N30{"N30 IF [#&lt;RESULT&gt; GT 0] THEN #102 = 1"}
    END_N40(["N40 M30<br/>END"])
    N30_THEN["THEN #102 = 1"]
    START --> N10
    N10 -->|next| N20
    N20 -->|next| N30
    N30 -->|THEN| N30_THEN
    N30_THEN --> END_N40
    N30 -->|NO| END_N40
    END_N40 --> END
```

## Output Example: analysis.json

抜粋:

```json
{
  "source_name": "04_variables.nc",
  "line_count": 7,
  "variable_summary": [
    {
      "name": "#100",
      "assignments": [],
      "references": [3],
      "count": 1
    },
    {
      "name": "#500",
      "assignments": [3],
      "references": [4],
      "count": 2
    }
  ],
  "controls": [
    {
      "line_no": 5,
      "kind": "IF_THEN",
      "target": null,
      "condition": "[#<RESULT> GT 0]",
      "text": "N30 IF [#<RESULT> GT 0] THEN #102 = 1"
    }
  ],
  "variable_dependencies": [
    {
      "line_no": 3,
      "target": "#500",
      "sources": ["#100", "#101"],
      "text": "N10 #500 = #100 + #101"
    },
    {
      "line_no": 4,
      "target": "#<RESULT>",
      "sources": ["#500"],
      "text": "N20 #<RESULT> = #500"
    }
  ],
  "warnings": []
}
```

## Output Example: report.md

抜粋:

```markdown
# NC Macro Visualizer Report: 04_variables.nc

## Summary

- Lines: 7
- Labels: 4
- Variables: 7
- IF/GOTO/WHILE/THEN: 1
- M codes: 1
- Calls: 0
- Warnings: 0

> This report is for understanding NC macro assets. It does not guarantee real machine behavior.

## Variable Dependencies

| Line | Target | Sources | Code |
| ---: | --- | --- | --- |
| 3 | `#500` | `#100`, `#101` | `N10 #500 = #100 + #101` |
| 4 | `#<RESULT>` | `#500` | `N20 #<RESULT> = #500` |
```

## M Code Policy

M コードは機械や PMC、ビルダー設定に強く依存します。

NC Macro Visualizer は、一般的な M コードに限って共通説明を付けます。未知の M コードは `unknown` / `machine_specific` として扱い、意味を推測しません。

## Tests

```bash
python3 -m unittest discover -s tests
```

`pytest` を導入している環境では次でも実行できます。

```bash
.venv/bin/python -m pytest
```

## Documentation

- [Design Philosophy](docs/design.md)
- [Limitations](limitations.md)
- [Changelog](CHANGELOG.md)
- [Release Notes v0.1.0](RELEASE_NOTES_v0.1.0.md)
- [License](LICENSE)
