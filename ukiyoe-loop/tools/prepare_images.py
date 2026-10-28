"""7枚の絵を集めて、同じ大きさ(1920×1296)の画面にそろえる。

    python3 tools/prepare_images.py [取得済みの元画像があるフォルダ]

出力:images/1-great-wave.jpg 〜 7-hokusai-portrait.jpg

そろえ方は3通り:
- fit  :横長の絵。紙の余白を切り、縦横比が合わない分は中央を残して端を少しだけ切る
- pad  :縦長の絵(写楽、北斎肖像)。画面の中央に置き、左右を絵の地の色で埋める。
         絵との境目は、ぼかしてなじませる
- crop :とても横長の屏風(鳳凰図)。決めた範囲だけを切り出す

鳳凰図屏風と北斎肖像は、出どころのはっきりした大きい画像がまだ手に入っていないので、
いただいた画像を仮に使っている。仮の素材は work/sources/ に置き(GitHub に保存しない)、
できた画像も images/ ではなく work/images/ に出す。
"""

import io
import sys
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "images"
OUT_TEMP = ROOT / "work" / "images"  # 仮の素材から作ったもの(保存しない)
SOURCES_TEMP = ROOT / "work" / "sources"
SIZE = (1920, 1296)
MET = "https://images.metmuseum.org/CRDImages/as/original/{}.jpg"

# (出力名, 元画像, そろえ方, 範囲 left, top, right, bottom ※元画像の画素)
# 範囲は明るさの変わり目から求めた印刷面に、さらに数十 px 内側へ寄せたもの。
PRINTS = [
    ("1-great-wave.jpg", ("met", "DP130155"), "fit", None),
    ("2-red-fuji.jpg", ("met", "DP141062"), "fit", (109 + 25, 89 + 25, 3765 - 25, 2607 - 25)),
    ("3-phoenix.jpg", ("temp", "phoenix.jpg"), "crop", (430, 0, 793, 245)),
    ("4-ejiri.jpg", ("met", "DP140977"), "fit", (94 + 25, 106 + 25, 3877 - 25, 2702 - 25)),
    ("5-sharaku.jpg", ("met", "DP130228"), "pad", (44 + 20, 36 + 20, 2497 - 20, 3757 - 20)),
    # 洗馬は四隅が丸いので、角が入らないよう多めに内側へ寄せる
    ("6-seba.jpg", ("met", "DP120447"), "fit", (93 + 70, 220 + 60, 3765 - 70, 2554 - 60)),
    ("7-hokusai-portrait.jpg", ("temp", "hokusai-portrait.jpg"), "pad", (34, 22, 668, 960)),
]


def load(source, cache_dir):
    kind, name = source
    if kind == "temp":
        path = SOURCES_TEMP / name
        if not path.exists():
            return None
        return Image.open(path)
    cached = cache_dir / f"{name}.jpg" if cache_dir else None
    if cached and cached.exists():
        return Image.open(cached)
    with urllib.request.urlopen(MET.format(name)) as r:
        return Image.open(io.BytesIO(r.read()))


def fit(im, size):
    """縦横比を合わせるために中央を残して少しだけ切り、指定の大きさにする。"""
    tw, th = size
    w, h = im.size
    target = tw / th
    if w / h > target:
        nw = round(h * target)
        x = (w - nw) // 2
        im = im.crop((x, 0, x + nw, h))
    else:
        nh = round(w / target)
        y = (h - nh) // 2
        im = im.crop((0, y, w, y + nh))
    return im.resize(size, Image.LANCZOS)


def pad(im, size, feather=0.14):
    """縦長の絵を中央に置き、左右を絵の地の色で埋める。境目はぼかしてなじませる。"""
    tw, th = size
    w = round(im.width * th / im.height)
    body = im.resize((w, th), Image.LANCZOS)
    # 地の色:絵の上の左右の隅(人物がいない背景)の中央値。端の縁は色が褪せて
    # 明るいことが多いので、少し内側(幅 4〜16%、高さ 4〜24%)から取る。
    a = np.asarray(body).reshape(th, w, 3)
    y0, y1 = th * 4 // 100, th * 24 // 100
    x0, x1 = w * 4 // 100, w * 16 // 100
    corners = np.concatenate([a[y0:y1, x0:x1].reshape(-1, 3), a[y0:y1, w - x1:w - x0].reshape(-1, 3)])
    ground = tuple(int(v) for v in np.median(corners, axis=0))
    canvas = Image.new("RGB", size, ground)
    x = (tw - w) // 2
    # 絵の左右の端だけを、地の色へ向かって薄くしていくマスク
    f = max(2, round(w * feather))
    ramp = np.ones(w, np.float32)
    ramp[:f] = np.linspace(0, 1, f)
    ramp[-f:] = np.linspace(1, 0, f)
    mask = Image.fromarray((np.tile(ramp, (th, 1)) * 255).astype(np.uint8))
    canvas.paste(body, (x, 0), mask.filter(ImageFilter.GaussianBlur(f / 4)))
    return canvas


def main():
    cache_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    OUT.mkdir(exist_ok=True)
    for name, source, mode, box in PRINTS:
        im = load(source, cache_dir)
        if im is None:
            print(f"{name}: 仮の素材 work/sources/{source[1]} がないので飛ばします")
            continue
        im = im.convert("RGB")
        if box:
            im = im.crop(box)
        out = pad(im, SIZE) if mode == "pad" else fit(im, SIZE)
        dest_dir = OUT_TEMP if source[0] == "temp" else OUT
        dest_dir.mkdir(parents=True, exist_ok=True)
        out.save(dest_dir / name, quality=92, optimize=True)
        print(f"{name}: {source[1]}({mode})-> {dest_dir.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
