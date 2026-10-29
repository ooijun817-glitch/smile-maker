"""動画の1周(34.33秒)にぴったり合う、くり返し用の和風の音楽を作る。

    python3 tools/make_music.py

出力:ios/HokusaiLoop/hokusai-music.wav(44.1kHz、ステレオ、16bit)

- 箏の音は、弦をはじいたときの倍音を重ねて作る(高い倍音ほど早く消える)
- 三味線の音は、バチで弾く鋭い出だし、「さわり」のビーンという響き、胴の皮を打つ音で作る。
  動きの大きい場面のリズムを三味線、静かな場面を箏が受け持つ
- 音階は箏でよく使う都節音階(レ・ミ♭・ソ・ラ・シ♭)
- 低い持続音と、場面の切り替わりの小さな太鼓を添える
- 長さは動画の1周ちょうど。終わりにはみ出した余韻は始まりへ回し込み、残響も「輪」として
  かけるので、くり返し再生しても切れ目が出ない
- 録音や既存の曲は使っていない(すべてこのプログラムで作った音)
"""

import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "ios" / "HokusaiLoop" / "hokusai-music.wav"

SR = 44100
FPS = 24
LOOP_FRAMES = 824                      # つないだ動画のコマ数
L = round(LOOP_FRAMES / FPS * SR)      # 1周の長さ(サンプル数)
T = L / SR

# 場面の切り替わり(秒)。動画の区間のつなぎ目に合わせている
CUTS = [0.0, 122 / FPS, 243 / FPS, 364 / FPS, 485 / FPS, 606 / FPS, 727 / FPS, T]

# 都節音階:レを基準に 0, 1, 5, 7, 8 半音
SCALE = [0, 1, 5, 7, 8]
BASE = 146.83  # D3


def pitch(degree):
    """音階の段(0 からの通し番号)を周波数にする。5 段ごとに1オクターブ上がる。"""
    octave, step = divmod(degree, len(SCALE))
    return BASE * 2 ** (octave + SCALE[step] / 12)


rng = np.random.default_rng(7)
buf = np.zeros((2, L))


def place(signal, start_sec, pan=0.0):
    """信号を start_sec から置く。1周の終わりを越えた分は始まりへ回し込む。"""
    n = signal.shape[-1]
    idx = (round(start_sec * SR) + np.arange(n)) % L
    left = np.sqrt(0.5 * (1 - pan))
    right = np.sqrt(0.5 * (1 + pan))
    np.add.at(buf[0], idx, signal * left)
    np.add.at(buf[1], idx, signal * right)


def koto(freq, vel=1.0, dur=3.2, bend=0.0):
    """箏のような、はじいた弦の音。bend を付けると、はじいた後に音をわずかに押し上げる(押し手)。"""
    t = np.arange(int(dur * SR)) / SR
    # 押し手:0.15 秒後から 0.25 秒かけて bend 半音上げる
    ramp = np.clip((t - 0.15) / 0.25, 0, 1)
    f_t = freq * 2 ** (bend * (3 * ramp ** 2 - 2 * ramp ** 3) / 12)
    phase = 2 * np.pi * np.cumsum(f_t) / SR
    y = np.zeros_like(t)
    for k in range(1, 10):
        inharm = 1 + 0.0004 * k * k                  # 弦のわずかな音程のずれ
        amp = (1 / k ** 1.15) * (1.0 if k % 4 else 0.35)  # はじく位置で弱まる倍音
        decay = 1.1 + 0.9 * k                        # 高い倍音ほど早く消える
        y += amp * np.sin(k * inharm * phase) * np.exp(-decay * t)
    attack = rng.standard_normal(len(t)) * np.exp(-t * 90) * 0.15  # 爪が弦に当たる音
    y = (y + attack) * np.minimum(1, t * 400)
    return 0.22 * vel * y


def taiko(vel=1.0, dur=0.9):
    """低い太鼓の音(音程が下がりながら消える)。"""
    t = np.arange(int(dur * SR)) / SR
    f_t = 48 + 55 * np.exp(-t * 18)
    y = np.sin(2 * np.pi * np.cumsum(f_t) / SR) * np.exp(-t * 6)
    y += rng.standard_normal(len(t)) * np.exp(-t * 60) * 0.25
    return 0.5 * vel * y


def shamisen(freq, vel=1.0, dur=1.3, slide=0.0):
    """三味線のような音。slide を付けると、弾いた直後に音を滑らせる(すり)。"""
    t = np.arange(int(dur * SR)) / SR
    ramp = np.clip(t / 0.12, 0, 1)
    f_t = freq * 2 ** (slide * (3 * ramp ** 2 - 2 * ramp ** 3) / 12)
    f_t = f_t * (1 + 0.006 * np.exp(-t * 40))         # バチで強く弾いた直後、音がわずかに高い
    phase = 2 * np.pi * np.cumsum(f_t) / SR
    y = np.zeros_like(t)
    for k in range(1, 17):
        amp = 1 / k ** 0.75                             # 箏より高い倍音が強く、明るい音
        decay = 2.6 + 1.5 * k                           # 箏より早く消える
        y += amp * np.sin(k * (1 + 0.0002 * k * k) * phase) * np.exp(-decay * t)
    # さわり:弦が棹にふれて出るビーンという響き。音をわずかにつぶして倍音を足す
    sawari = np.tanh(2.5 * y) - np.tanh(0.8 * y) * 0.9
    y = y + 0.55 * sawari * np.exp(-t * 3.5)
    # バチが胴の皮を打つ「ペン」という音
    hit = rng.standard_normal(len(t))
    hit = (hit - np.convolve(hit, np.ones(12) / 12, mode="same")) * np.exp(-t * 140)
    body = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 45)
    y = y * 0.5 + 0.35 * hit + 0.5 * body
    y *= np.minimum(1, t * 900)
    return 0.16 * vel * y


def sham(time, degree, vel=0.8, slide=0.0, dur=1.3):
    jitter = rng.normal(0, 0.005)
    place(shamisen(pitch(degree), vel, dur, slide), time + jitter, 0.35)  # 三味線は少し右に


def sham_run(start, end, degrees, vel=0.7):
    for tm, d in zip(np.linspace(start, end, len(degrees), endpoint=False), degrees):
        sham(tm, d, vel)


def note(time, degree, vel=0.8, bend=0.0, dur=3.2):
    jitter = rng.normal(0, 0.008)  # 人が弾いたような、わずかなゆらぎ
    pan = np.clip((degree - 7) / 10, -0.6, 0.6) - 0.2  # 箏は少し左に
    place(koto(pitch(degree), vel, dur, bend), time + jitter, pan)


def run(start, end, degrees, vel=0.7, bend_every=0, bend=1.0):
    """start〜end のあいだに、degrees の音を等間隔に弾く。"""
    times = np.linspace(start, end, len(degrees), endpoint=False)
    for i, (tm, d) in enumerate(zip(times, degrees)):
        b = bend if bend_every and i % bend_every == bend_every - 1 else 0.0
        note(tm, d, vel, b)


c = CUTS
# 区間1 大波→赤富士:力強く始まり、波が砕けて落ち、晴れた空へ
place(taiko(1.0), c[0]); place(taiko(0.6), c[0] + 0.12)
for d in (5, 7, 9, 12):
    note(c[0], d, 0.9)                                    # 始まりの和音
run(c[0] + 0.5, c[0] + 1.8, [10, 11, 12, 13, 14, 15], 0.75)  # 波が立ち上がる
run(c[0] + 1.9, c[0] + 3.0, [16, 14, 12, 10, 8, 6], 0.85)    # 砕けて落ちる
sham_run(c[0] + 0.5, c[0] + 1.85, [5, 5, 7, 5, 7, 7, 8, 7, 8, 10], 0.75)  # 三味線の刻み
for d in (5, 10):
    sham(c[0] + 1.9, d, 1.0)                              # 砕けるところで一撃
for tm, d in ((3.4, 9), (4.1, 12), (4.6, 11)):
    note(c[0] + tm, d, 0.6)                               # 晴れた空

# 区間2 赤富士→鳳凰:山頂から鳳凰が生まれ、高く舞い上がる
note(c[1] + 0.1, 7, 0.7)
run(c[1] + 0.9, c[1] + 2.4, [7, 9, 10, 12, 14, 15, 17], 0.7)
sham_run(c[1] + 1.6, c[1] + 2.5, [7, 8, 10, 12, 13, 15], 0.65)  # 姿を現す直前の盛り上げ
sham(c[1] + 2.6, 10, 0.9, slide=2.0)
place(taiko(0.5), c[1] + 2.5)
for d in (15, 17, 19):
    note(c[1] + 2.6, d, 0.8, dur=4.0)                     # 鳳凰が姿を現す
note(c[1] + 3.8, 18, 0.6, bend=1.0)

# 区間3 鳳凰→写楽:目へ寄る緊張が高まり、見得で決まる
run(c[2] + 0.2, c[2] + 2.8, [10, 10, 10, 11, 10, 11, 12, 11, 12, 13], 0.4)
hits = c[2] + 0.3 + np.cumsum(np.geomspace(0.42, 0.09, 14))  # だんだん速く
for i, tm in enumerate(hits):
    if tm < c[2] + 2.95:
        sham(tm, 5 if i % 3 else 8, 0.45 + 0.035 * i)
for d in (5, 8, 12):
    sham(c[2] + 3.0, d, 1.0, dur=1.6)                     # 見得
place(taiko(0.9), c[2] + 3.0); place(taiko(0.9), c[2] + 3.25)  # 見得
for d in (2, 5, 8, 11):
    note(c[2] + 3.0, d, 0.95)
note(c[2] + 4.2, 6, 0.6, bend=1.0)

# 区間4 写楽→北斎:張りつめた空気がほどけ、静かになる
run(c[3] + 0.4, c[3] + 2.6, [13, 11, 10, 8, 7, 5], 0.55)
note(c[3] + 3.2, 7, 0.45, bend=1.0, dur=4.0)
note(c[3] + 4.3, 10, 0.4)

# 区間5 北斎→江尻:風が起こり、紙が舞う。軽やかな速い音
for start in (0.6, 1.9, 3.1):
    k = rng.integers(10, 14)
    run(c[4] + start, c[4] + start + 0.7, [k, k + 2, k + 1, k + 3, k + 2], 0.45)
note(c[4] + 4.4, 12, 0.5, bend=1.0)
for tm, d in ((1.3, 13), (1.45, 12), (2.6, 14), (2.72, 13), (3.9, 12), (4.05, 10)):
    sham(c[4] + tm, d, 0.45, dur=0.8)                     # 風に舞う紙のような軽いはじき

# 区間6 江尻→洗馬:日が暮れ、月が昇る。ゆっくり静かに
note(c[5] + 0.5, 5, 0.5, dur=4.0)
note(c[5] + 1.7, 9, 0.45, bend=1.0, dur=4.0)
note(c[5] + 2.9, 12, 0.4, dur=4.0)
note(c[5] + 4.0, 10, 0.4, bend=-1.0, dur=4.0)

# 区間7 洗馬→大波:川がふくらみ、大波へ。だんだん速く強く(区間1の始まりへ流れ込む)
times = c[6] + 0.3 + np.cumsum(np.geomspace(0.5, 0.12, 14))
for i, tm in enumerate(times):
    if tm < T - 0.05:
        note(tm, [2, 5, 7, 5, 7, 9, 7, 9, 10, 9, 10, 12, 10, 12][i], 0.35 + 0.04 * i)
for tm in np.linspace(T - 1.2, T - 0.1, 6):
    place(taiko(0.25 + 0.1 * (tm - T + 1.2)), tm)
trem = np.arange(c[6] + 1.6, T - 0.06, 0.11)              # 速い刻み(だんだん強く)
for i, tm in enumerate(trem):
    sham(tm, [5, 5, 7, 5, 8, 7][i % 6] + (5 if i > len(trem) * 0.6 else 0),
         0.3 + 0.6 * i / len(trem), dur=0.7)

# 低い持続音:レとラ。1周でちょうど整数回振動する高さにして、つなぎ目で位相がずれないようにする
t = np.arange(L) / SR
drone = np.zeros(L)
for f, a in ((73.42, 0.05), (110.0, 0.03), (146.83, 0.015)):
    f_loop = round(f * T) / T
    drone += a * np.sin(2 * np.pi * f_loop * t)
breath = 0.65 + 0.35 * np.sin(2 * np.pi * 2 * t / T - np.pi / 2)  # 1周で2回ゆっくり息をする
buf += drone * breath

# 残響:1周を「輪」とみなしてかける(終わりの響きが始まりに自然につながる)
ir_t = np.arange(int(2.4 * SR)) / SR
ir = rng.standard_normal(len(ir_t)) * np.exp(-ir_t / 0.55)
ir = np.convolve(ir, np.ones(8) / 8, mode="same")     # 響きを少し柔らかく
ir /= np.sqrt(np.sum(ir ** 2))
IR = np.fft.rfft(np.pad(ir, (0, L - len(ir))))
wet = np.stack([np.fft.irfft(np.fft.rfft(ch) * IR, n=L) for ch in buf])
mix = 0.8 * buf + 0.28 * wet

mix /= np.max(np.abs(mix)) / 0.85                      # 大きすぎないようにそろえる
pcm = (mix.T * 32767).astype(np.int16)
OUT.parent.mkdir(parents=True, exist_ok=True)
with wave.open(str(OUT), "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f"作りました: {OUT.relative_to(ROOT)}  {L / SR:.3f} 秒")
