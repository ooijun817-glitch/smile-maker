# smile maker

塊根植物・多肉植物・サボテンの静的サイトです（コレクション、生育カレンダー、読みもの、Instagram への誘導）。
Instagram: https://www.instagram.com/smile_maker__zzz/

## ファイル

- `index.html`：公開するページ（`src/build.py` が生成するので、直接は編集しない）
- `style.css`：見た目（ライト・ダーク対応）
- `main.js`：コレクションの絞り込み、生育カレンダーの今月の印、IDコピー
- `img/`：写真（Web用に縮小済み）
- `src/body.html`：ページ本文（`index.html` の元）
- `src/build.py`：サイト名、Instagram ID、コレクションのデータ。`index.html` を作り直す

## 更新のしかた

```sh
python3 -m pip install pillow   # 初回のみ
python3 src/build.py            # index.html を作り直す
```

- 株の情報は `src/build.py` の `specimens` を編集する
- サイト名と Instagram ID は `src/build.py` 冒頭の `NAME` / `HANDLE` で変える
- 本文は `src/body.html` を編集する

## まだのこと

- 読みもの記事のページ（一覧のリンク先は今は `#journal`）
- `og:image`（絶対URLが必要なので、ドメインが決まってから追加する）
