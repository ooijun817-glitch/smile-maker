# 動く浮世絵(北斎)

北斎の3枚の絵を AI(Kling)で動かしてつなぎ、iPhone で全画面・音なしでくり返し流す。
自分で使うだけのアプリで、App Store には出さない。

流れる順番(1周 約14秒):
1. 神奈川沖浪裏:波がうねり、高く立ち上がる
2. 波が崩れてしぶきが画面を覆い、晴れると赤富士(凱風快晴)
3. 赤富士に雷雲が湧き、稲妻が走って黒富士(山下白雨)
4. 黒富士から波へ、1秒の重ね合わせで戻る

## フォルダ

| 場所 | 中身 |
| --- | --- |
| `images/` | Met の3枚を 1920×1296 にそろえたもの(`tools/prepare_images.py` で作成) |
| `prompts.json` | 区間ごとの指示文(別途もらうものを貼る) |
| `segments/` | 区間ごとの動画、最後のコマ、確認用の5コマ並べ |
| `tools/kling.py` | Kling に送る・待つ・受け取る |
| `tools/make_segment.py` | 区間を1つ作る |
| `tools/join.py` | 3区間をつないで1本にする |
| `ios/` | iPhone アプリ(Xcode で開く) |
| `SOURCES.md` | 絵の出どころとライセンス |

## 使い方

### 1. 鍵を置く
`.env.example` を `.env` という名前でコピーし、Kling の鍵(アクセスキーとシークレットキー)を書く。
`.env` は `.gitignore` に入っているので GitHub には保存されない。

### 2. 指示文を貼る
`prompts.json` の `seg1`〜`seg3` の `prompt` に貼る。空の区間は作られない。

### 3. 区間を1つずつ作る
```
python3 tools/make_segment.py seg1 --dry-run   # 送る内容の確認だけ
python3 tools/make_segment.py seg1             # 区間1を作る(5秒、約0.35ドルの見込み)
python3 tools/make_segment.py seg2             # 区間1の最後のコマから始め、赤富士に着地
python3 tools/make_segment.py seg3             # 区間2の最後のコマから始め、黒富士に着地
```
気に入らなければ、同じ区間をもう一度作れば上書きされる。区間1を作り直したら、区間2・3も作り直す。

### 4. つなぐ
```
python3 tools/join.py
```
`ios/HokusaiLoop/hokusai-loop.mp4` ができる。区間2・3の先頭1コマ(前の区間の最後と同じ絵)は
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
