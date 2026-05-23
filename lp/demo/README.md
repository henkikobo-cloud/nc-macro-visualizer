# NC Macro Visualizer Web Demo

ブラウザだけで動く宣伝・体験用デモです。GitHub Pagesで公開できます。

主対象は、NC初学者、経験の浅い人、PC操作があまり得意でない現場作業者です。

画面内の大きなボタンで次の操作ができます。

- NCファイルを選ぶ
- 解析する
- 結果を保存する

## 表示確認

ブラウザで `lp/demo/index.html` を開いて確認できます。

ローカルサーバーで確認する場合:

```bash
python3 -m http.server 8000 -d lp
```

その後、次のURLを開きます。

```text
http://localhost:8000/demo/
```

## 実装メモ

- 外部ライブラリは使っていません。
- サンプルNCは `app.js` 内に保持しています。
- 出力項目名は Python版の `analysis.json` に寄せています。
- Webデモは完全な解析エンジンではありません。代表サンプルと初心者向けの体験を優先した簡易解析です。
- 将来のファイルアップロード対応では、読み込んだテキストを `analyzeNcMacro(sourceName, code)` に渡す構成を想定しています。
