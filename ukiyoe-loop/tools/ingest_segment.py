"""Figma Weave(の Kling)で作った区間の動画を取り込む。

    python3 tools/ingest_segment.py seg1 <動画の URL またはファイル> --model "O1 Pro" --run-id <Weave の番号>

Weave で動画を作るのは Claude が Weave の道具で行う(このスクリプトは Kling を呼ばない)。
このスクリプトは、できた動画を受け取って次のものを segments/ に作る:
  segN.mp4        動画
  segN_last.png   最後のコマ(次の区間の「最初の絵」になる。GitHub に上げて Weave に URL で渡す)
  segN_sheet.jpg  確認用に5コマ並べた画像
  segN.json       作ったときの記録(モデル、指示文、Weave の番号など)
"""

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kling  # noqa: E402  (download だけ使う)
import make_segment as ms  # noqa: E402

ROOT = ms.ROOT
SEGMENTS = ms.SEGMENTS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("segment", choices=sorted(ms.PLAN))
    ap.add_argument("source", help="動画の URL、または手元の mp4 ファイル")
    ap.add_argument("--model", default="", help="Weave で使った Kling のモデル名")
    ap.add_argument("--family", default="Kling First & Last Frame", help="Weave のモデルの種類(例: Kling 3)")
    ap.add_argument("--run-id", default="", help="Weave の実行番号")
    ap.add_argument("--duration", default="5")
    args = ap.parse_args()

    seg = args.segment
    SEGMENTS.mkdir(exist_ok=True)
    mp4 = SEGMENTS / f"{seg}.mp4"
    if args.source.startswith(("http://", "https://")):
        kling.download(args.source, mp4)
    else:
        shutil.copyfile(args.source, mp4)

    info = ms.extract_last_frame(mp4, SEGMENTS / f"{seg}_last.png")
    ms.contact_sheet(mp4, info, SEGMENTS / f"{seg}_sheet.jpg")

    prompts = json.loads((ROOT / "prompts.json").read_text(encoding="utf-8"))
    p = prompts.get(seg) or {}
    plan = ms.PLAN[seg]
    record = {
        "segment": seg, "service": "Figma Weave", "model": f"{args.family} {args.model}".strip(),
        "run_id": args.run_id, "duration": args.duration,
        "first": plan["first"].name, "tail": plan["tail"].name if plan["tail"] else None,
        "prompt": p.get("prompt", ""), "negative_prompt": p.get("negative_prompt", ""),
        "video": info, "made_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    (SEGMENTS / f"{seg}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{seg} を取り込みました: {info['width']}×{info['height']} {info['fps']:.0f}fps {info['frames']}コマ")


if __name__ == "__main__":
    main()
