"""絵とマスクを作る。

    python3 tools/build_assets.py [元画像のパス]

元画像を省くと Met から取得する。出力:
  assets/great-wave.jpg  表示用に縮めた絵(長辺 3000px)
  assets/masks.png       範囲マスク  R=大波 / G=波の先(爪) / B=海面
  assets/mask-preview.jpg 確認用(絵にマスクを色で重ねたもの。アプリでは使わない)

マスクは「ざっくりした多角形」を塗り、大きくぼかしたもの。
境目を広くぼかすことで、切り抜きの雑さが動きに出ないようにしている。
座標は絵の幅・高さを 1 とした割合(左上が 0,0)。
"""

import io
import sys
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

SOURCE_URL = "https://images.metmuseum.org/CRDImages/as/original/DP130155.jpg"
LONG_SIDE = 3000
MASK_SCALE = 0.25  # マスクは絵の 1/4 の解像度で十分(どうせ大きくぼかす)

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

# ---- 範囲(絵を見ながら調整する) ----
# 大波:波の胴体全体。富士山と小舟の上半分にはかからないようにする。
WAVE = []
# 波の先:白い爪が並ぶ部分だけ。
CLAWS = []
# 海面:手前の波と小舟のあたり(次の段階で使う)。
SEA = []

# ぼかし幅(絵の幅に対する割合)
BLUR = {"wave": 0.035, "claws": 0.02, "sea": 0.035}


def load_source(arg):
    if arg:
        return Image.open(arg)
    with urllib.request.urlopen(SOURCE_URL) as r:
        return Image.open(io.BytesIO(r.read()))


def paint(size, polys, blur_frac):
    w, h = size
    im = Image.new("L", size, 0)
    d = ImageDraw.Draw(im)
    for poly in polys:
        d.polygon([(x * w, y * h) for x, y in poly], fill=255)
    return im.filter(ImageFilter.GaussianBlur(blur_frac * w))


def main():
    src = load_source(sys.argv[1] if len(sys.argv) > 1 else None).convert("RGB")
    scale = LONG_SIDE / max(src.size)
    art = src.resize((round(src.width * scale), round(src.height * scale)), Image.LANCZOS)
    ASSETS.mkdir(exist_ok=True)
    art.save(ASSETS / "great-wave.jpg", quality=90, optimize=True, progressive=True)

    msize = (round(art.width * MASK_SCALE), round(art.height * MASK_SCALE))
    r = paint(msize, WAVE, BLUR["wave"])
    g = paint(msize, CLAWS, BLUR["claws"])
    b = paint(msize, SEA, BLUR["sea"])
    masks = Image.merge("RGB", (r, g, b))
    masks.save(ASSETS / "masks.png", optimize=True)

    # 確認用の重ね合わせ
    big = masks.resize(art.size, Image.BILINEAR)
    tint = Image.new("RGB", art.size)
    tint.paste((230, 40, 30), mask=big.getchannel("R"))
    tint.paste((30, 220, 60), mask=big.getchannel("G"))
    tint.paste((30, 80, 230), mask=big.getchannel("B"))
    alpha = Image.eval(Image.merge("RGB", big.split()).convert("L"), lambda v: int(v * 0.5))
    Image.composite(tint, art, alpha).save(ASSETS / "mask-preview.jpg", quality=80)
    print("art", art.size, "masks", masks.size)


if __name__ == "__main__":
    main()
