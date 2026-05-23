# NC Macro Visualizer LP

GitHub Pages で公開できる静的な1枚HTMLのLPです。

## Files

```text
lp/
├─ index.html
├─ style.css
├─ README.md
└─ assets/
   └─ screenshot-flow.png
```

## 表示確認

ブラウザで `lp/index.html` を開いて確認できます。

ローカルサーバーで確認する場合:

```bash
python3 -m http.server 8000 -d lp
```

その後、次のURLを開きます。

```text
http://localhost:8000/
```

## GitHub Pages

GitHub Pages では公開元を `lp/` にできない場合があります。その場合は、リポジトリルートから公開し、`lp/index.html` を公開URLとして参照してください。
