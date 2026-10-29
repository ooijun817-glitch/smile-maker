"""区間(seg1, seg2, …)を順につないで、くり返し再生用の1本にする。

    python3 tools/join.py
    python3 tools/join.py --out 出力.mp4 a.mp4 b.mp4 c.mp4   # 区間を指定するとき

つなぎ方:
- 区間2以降は「前の区間の最後のコマ」から始まるので、先頭の1コマが前の区間の
  最後と重なる。そのままつなぐと同じ絵が2コマ続いて一瞬止まって見えるため、
  区間2以降の先頭1コマを捨ててからつなぐ。
- 最後(神奈川沖浪裏に着地)から最初(神奈川沖浪裏)へ戻るところは、1秒の重ね合わせにする。
  つないだ全体を S(N コマ)、重ね合わせを F コマとすると、出来上がりは
      [S の最後の F コマ と 最初の F コマ を重ねたもの] + [S の F 〜 N-F コマ]
  になる。最後のコマ(S の N-F-1)の次に先頭(S の N-F)が来るので、くり返し
  再生しても途切れない。長さは N-F コマ。
- 音は入れない。
"""

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_IN = sorted((ROOT / "segments").glob("seg[0-9]*.mp4"), key=lambda p: int(p.stem[3:]))
DEFAULT_OUT = ROOT / "ios" / "HokusaiLoop" / "hokusai-loop.mp4"
CROSSFADE_SECONDS = 1.0


def probe(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,r_frame_rate,nb_read_frames", "-of", "json", str(path)],
        check=True, capture_output=True, text=True).stdout
    s = json.loads(out)["streams"][0]
    num, den = s["r_frame_rate"].split("/")
    return {"width": s["width"], "height": s["height"], "fps": float(num) / float(den),
            "rate": s["r_frame_rate"], "frames": int(s["nb_read_frames"])}


def build_filter(infos, width, height, rate, fade):
    parts = []
    labels = []
    for i, _ in enumerate(infos):
        skip = 0 if i == 0 else 1  # 区間2以降は先頭1コマ(前の区間の最後と同じ絵)を捨てる
        parts.append(
            f"[{i}:v]trim=start_frame={skip},setpts=PTS-STARTPTS,"
            f"scale={width}:{height}:flags=lanczos,setsar=1,fps={rate},format=yuv420p[v{i}]")
        labels.append(f"[v{i}]")
    total = sum(info["frames"] - (0 if i == 0 else 1) for i, info in enumerate(infos))
    parts.append("".join(labels) + f"concat=n={len(infos)}:v=1:a=0[all]")
    parts.append("[all]split=3[s1][s2][s3]")
    parts.append(f"[s1]trim=end_frame={fade},setpts=PTS-STARTPTS[head]")
    parts.append(f"[s2]trim=start_frame={fade}:end_frame={total - fade},setpts=PTS-STARTPTS[mid]")
    parts.append(f"[s3]trim=start_frame={total - fade},setpts=PTS-STARTPTS[tail]")
    # 重ね合わせ:k コマ目(0 始まり)は 末尾×(1-k/F) + 先頭×(k/F)
    parts.append(f"[tail][head]blend=all_expr='A*(1-N/{fade})+B*(N/{fade})'[xf]")
    parts.append("[xf][mid]concat=n=2:v=1:a=0[out]")
    return ";".join(parts), total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="*", type=Path, default=DEFAULT_IN)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--crf", type=int, default=18)
    args = ap.parse_args()

    for p in args.inputs:
        if not p.exists():
            raise SystemExit(f"{p} がありません")
    infos = [probe(p) for p in args.inputs]
    first = infos[0]
    width, height = first["width"] - first["width"] % 2, first["height"] - first["height"] % 2
    rate = first["rate"]
    for p, info in zip(args.inputs, infos):
        if abs(info["fps"] - first["fps"]) > 0.01:
            print(f"注意: {p.name} のコマ数/秒が {info['fps']:.2f} で、最初の区間({first['fps']:.2f})と違います。"
                  "合わせるときにコマが増減します。")
    fade = round(first["fps"] * CROSSFADE_SECONDS)
    graph, total = build_filter(infos, width, height, rate, fade)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-v", "error", "-y"]
    for p in args.inputs:
        cmd += ["-i", str(p)]
    cmd += ["-filter_complex", graph, "-map", "[out]", "-an",
            "-c:v", "libx264", "-preset", "slow", "-crf", str(args.crf),
            "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", rate, "-movflags", "+faststart",
            str(args.out)]
    subprocess.run(cmd, check=True)
    out = probe(args.out)
    print(f"つなぎ終わりました: {args.out}")
    print(f"  {out['width']}×{out['height']} {out['fps']:.2f}fps {out['frames']}コマ"
          f"(約 {out['frames'] / out['fps']:.1f} 秒)。区間の合計 {total} コマ − 重ね合わせ {fade} コマ")
    if out["frames"] != total - fade:
        print("注意: コマ数が計算と合いません。")


if __name__ == "__main__":
    main()
