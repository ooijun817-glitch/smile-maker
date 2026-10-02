"""body.html から index.html（サイト本体）と artifact.html（プレビュー用の一枚もの）を作る"""
from pathlib import Path
from PIL import Image

NAME = "smile maker"
HANDLE = "smile_maker__zzz"
root = Path(__file__).resolve().parent.parent

specimens = [
  ("cactus", "サボテン", "黒竜", "Pterocactus tuberosus", "サボテン科", "アルゼンチン", "夏型", "黒い鉢", "texture", "逆光に白い細かな棘が光る、乾いた枝を何本も伸ばした黒竜の塊根の近景"),
  # type, 種類, 名前, 学名, 科, 原産地, 生育型, 鉢, 写真, 代替テキスト
  ("caudex", "塊根植物", "アデニア・アクレアータ", "Adenia aculeata", "トケイソウ科", "東アフリカ", "夏型", "黒土の丸鉢、歯車の台", "interior", "ひび割れた塊根から棘のある緑の茎を伸ばすアデニア・アクレアータ。古材の棚と木札を背景に黒い丸鉢に植わっている"),
  ("caudex", "塊根植物", "パキポディウム・グラキリス", "Pachypodium rosulatum var. gracilius", "キョウチクトウ科", "マダガスカル", "夏型", "骸骨のギター弾きを彫った焼締め鉢", "gracilius", "徳利形の幹が二つ並ぶグラキリス。骸骨がギターを弾く絵を彫った茶色の鉢に植わっている"),
  ("cactus", "サボテン", "晃山", "Leuchtenbergia principis", "サボテン科", "メキシコ", "夏型", "黒釉の手びねり鉢", "leuchtenbergia", "紙のような長い棘をまとった細長い疣を広げる晃山。凹凸のある黒釉の鉢に植わっている"),
  ("succulent", "多肉植物", "セロペギア・フスカ", "Ceropegia fusca", "キョウチクトウ科", "カナリア諸島", "冬型", "黒い鉢", "stems", "節のある灰白色の茎がまっすぐ伸びるセロペギア・フスカのモノクロ写真"),
  ("caudex", "塊根植物", "パキポディウム・ウィンゾリー", "Pachypodium windsorii", "キョウチクトウ科", "マダガスカル", "夏型", "炭化させたような棘の鉢", "pachy", "徳利形の幹から棘のある枝を伸ばすウィンゾリー。黒い棘状の鉢と歯車の台に載っている"),
]
def size(name):
    return Image.open(root / "img" / f"{name}.jpg").size

li = []
for t, kind, ja, latin, fam, origin, grow, pot, img, alt in specimens:
    wide = ""
    li.append(f'''<li class="specimen{wide}" data-type="{t}">
          <div class="plate"><img src="img/{img}.jpg" width="{size(img)[0]}" height="{size(img)[1]}" alt="{alt}" loading="lazy"></div>
          <div><h3>{ja}</h3><span class="latin">{latin}</span></div>
          <dl><dt>分類</dt><dd>{kind}・{fam}</dd><dt>原産地</dt><dd>{origin}</dd><dt>生育型</dt><dd>{grow}</dd><dt>鉢</dt><dd>{pot}</dd></dl>
        </li>''')

months = "".join(f'<th scope="col" data-m="{m}">{m}月</th>' for m in range(1, 13))
rows = [
  ("夏型", "パキポディウム・サボテンなど", {"g": [4,5,6,7,8,9,10], "s": [3,11]}),
  ("冬型", "亀甲竜・オトンナなど", {"g": [10,11,12,1,2,3], "s": [4,9]}),
  ("春秋型", "エケベリア・ハオルチアなど", {"g": [3,4,5,9,10,11], "s": [2,6,12]}),
]
label = {"g": "生育期", "s": "緩やか", "d": "休眠期"}
cal = []
for name, note, spec in rows:
    cells = []
    for m in range(1, 13):
        k = next((k for k, ms in spec.items() if m in ms), "d")
        cells.append(f'<td class="{k}" data-m="{m}" title="{m}月 {label[k]}"><span class="sr">{label[k]}</span></td>')
    cal.append(f'<tr><th scope="row">{name}<small>{note}</small></th>{"".join(cells)}</tr>')

body = (root / "src/body.html").read_text()
body = body.replace("{{NAME}}", NAME).replace("{{HANDLE}}", HANDLE).replace("{{SPECIMENS}}", "\n        ".join(li)).replace("{{MONTHS}}", months).replace("{{CALROWS}}", "".join(cal))

title = NAME
fonts = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;1,400&family=Zen+Antique&family=Zen+Kaku+Gothic+New:wght@400;500;700&display=swap">'
desc = "塊根植物・多肉植物・サボテンの育て方と、黒い鉢や古道具と合わせて部屋に置く楽しみ。はじめての一株の選び方から紹介しています。"

(root / "index.html").write_text(f'''<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta name="theme-color" content="#d3cbbe">
{fonts}
<link rel="stylesheet" href="style.css">
</head>
<body>
{body}
<script src="main.js"></script>
</body>
</html>
''')

css = (root / "style.css").read_text()
js = (root / "main.js").read_text()
out = Path(__import__("sys").argv[1]) if len(__import__("sys").argv) > 1 else root / "src/artifact.html"
out.write_text(f'<title>{title}</title>\n{fonts}\n<style>\n{css}</style>\n{body}\n<script>\n{js}</script>\n')
print("built", out)
