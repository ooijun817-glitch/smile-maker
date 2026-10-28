# 動く浮世絵

北斎を中心に、写楽・広重も加えた7枚の浮世絵を AI(Kling)で動かしてつなぎ、iPhone で
全画面・音なしでくり返し流す。駅のデジタルサイネージのように、趣きある日本と現代らしさ、生きるが如くのダイナミックな動きで目を引く。
自分で使うだけのアプリで、App Store には出さない。

流れ(1周 約34秒):神奈川沖浪裏 → 赤富士 → 八方睨み鳳凰図 → 写楽 → 北斎肖像 → 駿州江尻
→ 洗馬(広重)→ 神奈川沖浪裏に戻る(1秒の重ね合わせで最初へ)。くわしくは [STORYBOARD.md](STORYBOARD.md)。

## フォルダ

| 場所 | 中身 |
| --- | --- |
| `images/` | 7枚を 1920×1296 にそろえたもの(`tools/prepare_images.py` で作成)。仮の素材から作った2枚は `work/images/` |
| `STORYBOARD.md` | 絵コンテ(流れ・見せ場・指示文の日本語の意味) |
| `prompts.json` | 区間ごとの指示文(下書き入り) |
| `segments/` | 区間ごとの動画、最後のコマ、確認用の5コマ並べ |
| `tools/kling.py` | Kling に送る・待つ・受け取る |
| `tools/make_segment.py` | 区間を1つ作る |
| `tools/join.py` | 区間を順につないで1本にする |
| `ios/` | iPhone アプリ(Xcode で開く) |
| `SOURCES.md` | 絵の出どころとライセンス |

## 使い方

### 1. 鍵を置く
`.env.example` を `.env` という名前でコピーし、Kling の鍵(アクセスキーとシークレットキー)を書く。
`.env` は `.gitignore` に入っているので GitHub には保存されない。

### 2. 指示文を確かめる
`prompts.json` に7区間ぶんの下書きが入っている。日本語の意味は `STORYBOARD.md`。

### 3. 区間を1つずつ作る
```
python3 tools/make_segment.py seg1 --dry-run   # 送る内容の確認だけ
python3 tools/make_segment.py seg1             # 神奈川沖浪裏から始め、赤富士に着地(5秒、約0.35ドルの見込み)
python3 tools/make_segment.py seg2             # 区間1の最後のコマから始め、八方睨み鳳凰図に着地
…
python3 tools/make_segment.py seg7             # 区間6の最後のコマから始め、神奈川沖浪裏に着地
```
気に入らなければ、同じ区間をもう一度作れば上書きされる。ある区間を作り直したら、そのあとの区間も作り直す。

### 4. つなぐ
```
python3 tools/join.py
```
`ios/HokusaiLoop/hokusai-loop.mp4` ができる。区間2以降の先頭1コマ(前の区間の最後と同じ絵)は
捨てるので、つなぎ目で止まらない。

### 5. iPhone に入れる(Mac で)
1. `ios/HokusaiLoop.xcodeproj` を Xcode(16 以降)で開く
2. 左の HokusaiLoop → Signing & Capabilities → Team に自分の Apple アカウントを選ぶ
   (Bundle Identifier が使えないと言われたら、`jp.personal.HokusaiLoop` を別の名前に変える)
3. iPhone をつないで ▶ で実行
4. 初回は iPhone の 設定 → 一般 → VPN とデバイス管理 で、自分の開発者アプリを信頼する
   (iPhone の「デベロッパモード」をオンにする必要がある場合もある)

無料の Apple アカウントで入れたアプリは7日で開けなくなるので、そのときはもう一度 ▶ で入れ直す。

アプリの動き:
- 動画全体が見えるように収め、余白は黒
- 音なし。文字やボタンは出さない。ステータスバーとホームバーも隠す
- 前に出ているあいだは画面を自動で消さない
- `hokusai-loop.mp4` がまだないときは黒い画面のまま

## 必要なもの
- Python 3(Pillow)、ffmpeg
- 作業する環境から Kling の窓口(`api-singapore.klingai.com` など)と、動画の置き場所に接続できること
