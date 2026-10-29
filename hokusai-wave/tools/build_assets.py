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

from PIL import Image, ImageChops, ImageDraw, ImageFilter

SOURCE_URL = "https://images.metmuseum.org/CRDImages/as/original/DP130155.jpg"
LONG_SIDE = 3000
MASK_SCALE = 0.25  # マスクは絵の 1/4 の解像度で十分(どうせ大きくぼかす)

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

# ---- 範囲(絵を見ながら調整する) ----
# 大波:背から波頭、内側の面、根元まで。左の小舟は波に乗せて一緒に動かす
# (舟だけ止めると、大きく動く波とのあいだがねじれて見えるため)。
WAVE = [[
    (0.00, 0.40), (0.05, 0.35), (0.11, 0.30), (0.17, 0.23), (0.23, 0.16),
    (0.30, 0.11), (0.38, 0.09), (0.45, 0.11), (0.52, 0.17), (0.57, 0.25),
    (0.59, 0.33), (0.55, 0.41), (0.48, 0.42), (0.43, 0.47), (0.42, 0.56),
    (0.43, 0.64), (0.40, 0.72), (0.30, 0.76), (0.24, 0.76), (0.15, 0.72),
    (0.05, 0.58), (0.00, 0.52),
]]
# 波の先:波頭の縁で、白い爪が空に向かって並ぶ部分。
CLAWS = [[
    (0.22, 0.24), (0.27, 0.17), (0.34, 0.10), (0.41, 0.08), (0.48, 0.12),
    (0.55, 0.20), (0.60, 0.28), (0.60, 0.37), (0.55, 0.43), (0.49, 0.40),
    (0.45, 0.30), (0.40, 0.20), (0.33, 0.20), (0.27, 0.27),
]]
# 海面:手前の波と小舟のあたり(次の段階で使う)。
SEA = []

# 動かさないところ:富士山、題字と落款。ほかのマスクのぼかしがここに
# にじみ出ても、最後にここだけはゼロへ戻す。
STILL = [
    [(0.54, 0.74), (0.60, 0.66), (0.625, 0.645), (0.65, 0.66), (0.71, 0.74)],  # 富士山
    [(0.04, 0.05), (0.11, 0.05), (0.11, 0.31), (0.04, 0.31)],                  # 題字
    [(0.01, 0.12), (0.045, 0.12), (0.045, 0.32), (0.01, 0.32)],                # 落款
]

# ぼかし幅(絵の幅に対する割合)
BLUR = {"wave": 0.06, "claws": 0.05, "sea": 0.035, "still": 0.015}


def load_source(arg):
    if arg:
        return Image.open(arg)
    with urllib.request.urlopen(SOURCE_URL) as r:
        return Image.open(io.BytesIO(r.read()))


def paint(size, polys, blur_frac, grow=False):
    """多角形を塗ってぼかす。grow=True のときは、ぼかしても元の形の内側が
    ほぼ 1 のまま残るよう、先にぼかし幅の 2 倍だけ太らせておく。"""
    w, h = size
    im = Image.new("L", size, 0)
    d = ImageDraw.Draw(im)
    for poly in polys:
        d.polygon([(x * w, y * h) for x, y in poly], fill=255)
    radius = blur_frac * w
    if grow:
        im = im.filter(ImageFilter.MaxFilter(int(radius * 2) * 2 + 1))
    return im.filter(ImageFilter.GaussianBlur(radius))


def main():
    src = load_source(sys.argv[1] if len(sys.argv) > 1 else None).convert("RGB")
    scale = LONG_SIDE / max(src.size)
    art = src.resize((round(src.width * scale), round(src.height * scale)), Image.LANCZOS)
    ASSETS.mkdir(exist_ok=True)
    art.save(ASSETS / "great-wave.jpg", quality=90, optimize=True, progressive=True)

    msize = (round(art.width * MASK_SCALE), round(art.height * MASK_SCALE))
    keep = ImageChops.invert(paint(msize, STILL, BLUR["still"], grow=True))
    r = ImageChops.multiply(paint(msize, WAVE, BLUR["wave"]), keep)
    g = ImageChops.multiply(paint(msize, CLAWS, BLUR["claws"]), keep)
    b = paint(msize, SEA, BLUR["sea"])
    masks = Image.merge("RGB", (r, g, b))
    masks.save(ASSETS / "masks.png", optimize=True)

    # 確認用の重ね合わせ
    big = masks.resize(art.size, Image.BILINEAR)
    tint = Image.new("RGB", art.size)
    tint.paste((230, 40, 30), mask=big.getchannel("R"))
    tint.paste((30, 220, 60), mask=big.getchannel("G"))
    tint.paste((30, 80, 230), mask=big.getchannel("B"))
    alpha = ImageChops.lighter(ImageChops.lighter(*big.split()[:2]), big.getchannel("B"))
    alpha = Image.eval(alpha, lambda v: int(v * 0.55))
    Image.composite(tint, art, alpha).save(ASSETS / "mask-preview.jpg", quality=80)
    print("art", art.size, "masks", masks.size)


if __name__ == "__main__":
    main()
