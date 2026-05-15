# Limitations

NC Macro Visualizer v0.1.0 には、意図的な制限があります。

## No Machine Behavior Guarantee

このツールは実機動作を保証しません。

NC プログラムを実行せず、コントローラ状態、機械パラメータ、PMC、ビルダー設定、工具補正、座標系、モーダル状態、外部入出力を再現しません。

## M Codes Are Machine-Dependent

M コードは機械依存です。

このツールは一般的な M コードにだけ共通説明を付けます。未知の M コードは `unknown` / `machine_specific` として扱います。

`unknown` を自動的に推測、補完、断定することはありません。

## Regex-Based MVP Parser

v0.1.0 のパーサは regex ベースです。

複雑な式、ネストした条件、コントローラごとの方言、特殊なコメント構文、行継続、間接参照などを完全には扱いません。

## Flowchart Is For Reading

Mermaid の `flow.mmd` は読解用の概観です。

実際の実行経路、モーダル状態、マクロ変数の値、外部サブプログラム、機械側の分岐を完全に表すものではありません。

## Variable Dependencies Are Line-Local

変数依存は、同一行の単純な代入式から抽出します。

例:

```nc
N10 #500 = #100 + #101
```

この場合、`#500 <- #100, #101` を抽出します。

式の意味評価、演算順序、条件付き代入の完全な意味解析は行いません。

## Warnings Are Conservative

未解決 `GOTO`、重複ラベル、未対応拡張子などは warning として出力します。

warning がないことは、NC プログラムが正しいことや安全であることを意味しません。

