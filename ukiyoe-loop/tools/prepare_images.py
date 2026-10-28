"""メトロポリタン美術館の3枚を取ってきて、同じ大きさにそろえる。

    python3 tools/prepare_images.py

出力:images/1-great-wave.jpg, 2-red-fuji.jpg, 3-ejiri.jpg(1920×1296)

- 赤富士・江尻の画像には紙の余白が写っているので、印刷面だけを切り出す。
  神奈川沖浪裏の画像は、はじめから印刷面だけ。
- 3枚とも縦横比がわずかに違う(1.45〜1.49)。動画をつなぐときに大きさを
  そろえる必要があるので、1920×1296(約 1.48)に合わせる。合わない分は
  中央を残して上下か左右を少しだけ切る(最大でも高さの 2% ほど)。
"""

import io
import sys
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "images"
SIZE = (1920, 1296)

# (出力名, Met の画像番号, 印刷面の範囲 left, top, right, bottom ※元画像の画素)
# 範囲は元画像の明るさの変わり目から求め、さらに 25px 内側に寄せて紙の縁が残らないようにした。
PRINTS = [
    ("1-great-wave.jpg", "DP130155", None),
    ("2-red-fuji.jpg", "DP141062", (109 + 25, 89 + 25, 3765 - 25, 2607 - 25)),
    ("3-ejiri.jpg", "DP140977", (94 + 25, 106 + 25, 3877 - 25, 2702 - 25)),
]
URL = "https://images.metmuseum.org/CRDImages/as/original/{}.jpg"


def fetch(image_id, cache_dir):
    cached = cache_dir / f"{image_id}.jpg" if cache_dir else None
    if cached and cached.exists():
        return Image.open(cached)
    with urllib.request.urlopen(URL.format(image_id)) as r:
        return Image.open(io.BytesIO(r.read()))


def fit(im, size):
    """縦横比を合わせるために中央を残して少しだけ切り、指定の大きさにする。"""
    tw, th = size
    w, h = im.size
    target = tw / th
    if w / h > target:  # 横に長い → 左右を切る
        nw = round(h * target)
        x = (w - nw) // 2
        im = im.crop((x, 0, x + nw, h))
    else:  # 縦に長い → 上下を切る
        nh = round(w / target)
        y = (h - nh) // 2
        im = im.crop((0, y, w, y + nh))
    return im.resize(size, Image.LANCZOS)


def main():
    cache_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else None  # 取得済みの元画像があるフォルダ(省略可)
    OUT.mkdir(exist_ok=True)
    for name, image_id, box in PRINTS:
        im = fetch(image_id, cache_dir).convert("RGB")
        if box:
            im = im.crop(box)
        fit(im, SIZE).save(OUT / name, quality=92, optimize=True)
        print(name, image_id, "->", SIZE)


if __name__ == "__main__":
    main()
