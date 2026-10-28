"""区間を1つ作る。

    python3 tools/make_segment.py seg1            # 区間1を作る
    python3 tools/make_segment.py seg2 --dry-run  # 送る内容だけ確かめる(Kling には送らない)

区間ごとの「最初の絵」と「最後の絵」:
  seg1  最初=神奈川沖浪裏                 最後=指定なし(波が高く立ち上がったところで終わる)
  seg2  最初=区間1の最後のコマ             最後=赤富士(本物の絵に着地させる)
  seg3  最初=区間2の最後のコマ             最後=駿州江尻(本物の絵に着地させる)

できるもの(segments/):
  segN.mp4        Kling から受け取った動画
  segN_last.png   最後のコマ(次の区間の「最初の絵」になる)
  segN_sheet.jpg  確認用に5コマ並べた画像
  segN.json       作ったときの記録(モデル、指示文、task_id など。鍵は含まない)
"""

import argparse
import base64
import io
import json
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kling  # noqa: E402

ROOT = kling.ROOT
IMAGES = ROOT / "images"
SEGMENTS = ROOT / "segments"

PLAN = {
    "seg1": {"first": IMAGES / "1-great-wave.jpg", "tail": None},
    "seg2": {"first": SEGMENTS / "seg1_last.png", "tail": IMAGES / "2-red-fuji.jpg"},
    "seg3": {"first": SEGMENTS / "seg2_last.png", "tail": IMAGES / "3-ejiri.jpg"},
}
DURATION = "5"


def to_b64_jpeg(path):
    """Kling には base64(先頭の data: は付けない)で渡す。10MB 以内に収まるよう JPEG にする。"""
    im = Image.open(path).convert("RGB")
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=95)
    if buf.tell() > 9.5 * 1024 * 1024:
        raise SystemExit(f"{path} が大きすぎます")
    return base64.b64encode(buf.getvalue()).decode()


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,r_frame_rate,nb_read_frames", "-of", "json", str(path)],
        check=True, capture_output=True, text=True).stdout
    s = json.loads(out)["streams"][0]
    num, den = s["r_frame_rate"].split("/")
    return {"width": s["width"], "height": s["height"], "fps": float(num) / float(den),
            "frames": int(s["nb_read_frames"])}


def extract_last_frame(video, dest):
    """最後のコマを1枚、劣化なしの PNG で取り出す。"""
    info = probe(video)
    last = info["frames"] - 1
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video),
                    "-vf", f"select=eq(n\\,{last})", "-vsync", "0", "-frames:v", "1", str(dest)], check=True)
    return info


def contact_sheet(video, info, dest, n=5):
    """確認用:最初から最後まで均等に n コマ並べる。"""
    frames = []
    for i in range(n):
        idx = round(i * (info["frames"] - 1) / (n - 1))
        out = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vf", f"select=eq(n\\,{idx})",
                              "-vsync", "0", "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"],
                             check=True, capture_output=True).stdout
        frames.append(Image.open(io.BytesIO(out)).convert("RGB"))
    w = 480
    h = round(w * frames[0].height / frames[0].width)
    sheet = Image.new("RGB", (w * n + 8 * (n - 1), h), "black")
    for i, im in enumerate(frames):
        sheet.paste(im.resize((w, h), Image.LANCZOS), (i * (w + 8), 0))
    sheet.save(dest, quality=85)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("segment", choices=sorted(PLAN))
    ap.add_argument("--dry-run", action="store_true", help="Kling には送らず、送る内容だけ表示する")
    args = ap.parse_args()

    seg = args.segment
    plan = PLAN[seg]
    prompts = json.loads((ROOT / "prompts.json").read_text(encoding="utf-8"))
    p = prompts.get(seg) or {}
    prompt = (p.get("prompt") or "").strip()
    negative = (p.get("negative_prompt") or "").strip()
    if not prompt:
        raise SystemExit(f"prompts.json の {seg}.prompt が空です。指示文を貼ってから実行してください。")
    if not plan["first"].exists():
        raise SystemExit(f"最初の絵 {plan['first'].name} がありません。前の区間を先に作ってください。")

    cfg = kling.config()
    print(f"{seg}: 最初={plan['first'].name}  最後={plan['tail'].name if plan['tail'] else '指定なし'}  "
          f"モデル={cfg['model']}({cfg['mode']}) {DURATION}秒")
    image_b64 = to_b64_jpeg(plan["first"])
    tail_b64 = to_b64_jpeg(plan["tail"]) if plan["tail"] else None
    if args.dry_run:
        print(f"  指示文: {prompt[:120]}{'…' if len(prompt) > 120 else ''}")
        print(f"  最初の絵 {len(image_b64) // 1024}KB / 最後の絵 {len(tail_b64) // 1024 if tail_b64 else 0}KB")
        print("  --dry-run なので送っていません。")
        return

    client = kling.Kling(cfg)
    task_id = client.create_image2video(image_b64, prompt, tail_b64, negative, duration=DURATION)
    print(f"  受付番号 {task_id}。完成を待っています…")
    video = client.wait(task_id)

    SEGMENTS.mkdir(exist_ok=True)
    mp4 = SEGMENTS / f"{seg}.mp4"
    kling.download(video["url"], mp4)
    info = extract_last_frame(mp4, SEGMENTS / f"{seg}_last.png")
    contact_sheet(mp4, info, SEGMENTS / f"{seg}_sheet.jpg")
    record = {
        "segment": seg, "task_id": task_id, "model": cfg["model"], "mode": cfg["mode"],
        "duration": DURATION, "first": plan["first"].name,
        "tail": plan["tail"].name if plan["tail"] else None,
        "prompt": prompt, "negative_prompt": negative, "video": info,
        "made_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    (SEGMENTS / f"{seg}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  できました: {mp4.relative_to(ROOT)}  {info['width']}×{info['height']} "
          f"{info['fps']:.0f}fps {info['frames']}コマ")


if __name__ == "__main__":
    main()
