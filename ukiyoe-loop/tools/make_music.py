"""動画の1周(34.30秒)にぴったり合う、くり返し用の和風の音楽を作る。

    python3 tools/make_music.py

出力:ios/HokusaiLoop/hokusai-music.wav(44.1kHz、ステレオ、16bit)

- 箏の音は、弦をはじいたときの倍音を重ねて作る(高い倍音ほど早く消える)
- 三味線の音は、バチで弾く鋭い出だし、「さわり」のビーンという響き、胴の皮を打つ音で作る。
  動きの大きい場面のリズムを三味線、静かな場面を箏が受け持つ
- 音階は箏でよく使う都節音階(レ・ミ♭・ソ・ラ・シ♭)
- 太鼓は2種類:低く大きく響く大太鼓と、高く締まった音の締太鼓。場面ごとに約130拍/分で刻む。
  写楽の見得では歌舞伎の拍子木を鳴らす
- 低い持続音を薄く敷く
- 人の掛け声(よーっ、はっ、いやーっ、それっ、日本一)を場面の山場に入れる。
  掛け声は Figma Weave の音声 AI(Qwen-3 TTS)で作り、sounds/ に切り分けて置いている
- 長さは動画の1周ちょうど。終わりにはみ出した余韻は始まりへ回し込み、残響も「輪」として
  かけるので、くり返し再生しても切れ目が出ない
- 録音や既存の曲は使っていない(すべてこのプログラムで作った音)
"""

import wave
from pathlib import Path

import numpy as np

SOUNDS = Path(__file__).resolve().parent.parent / "sounds"

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "ios" / "HokusaiLoop" / "hokusai-music.wav"

SR = 44100
# 1周の長さは、アプリに入れる動画に合わせる。
# 画質を上げた動画(1秒60コマ)。12区間になった(2026-10-29)ので約59秒。
# LOOP_FRAMES は、アプリに入れる動画のコマ数(ffprobe で数える)に合わせる。
FPS = 60
LOOP_FRAMES = 3556
L = round(LOOP_FRAMES / FPS * SR)      # 1周の長さ(サンプル数)
T = L / SR

# 場面の切り替わり(秒)。区間のつなぎ目(元の1秒24コマの動画でのコマ位置)に合わせている
SEG_START = [0, 122, 243, 364, 485, 606, 727, 847, 967, 1087, 1207, 1327]
CUTS = [n / 24 for n in SEG_START] + [T]

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
    return 0.17 * vel * y


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
    return 0.27 * vel * y


def sham(time, degree, vel=0.8, slide=0.0, dur=1.3):
    jitter = rng.normal(0, 0.005)
    place(shamisen(pitch(degree), vel, dur, slide), time + jitter, 0.1)  # 三味線は前に、ほぼ中央


def sham_run(start, end, degrees, vel=0.7):
    for tm, d in zip(np.linspace(start, end, len(degrees), endpoint=False), degrees):
        sham(tm, d, vel)


# 円い皮が振動するときの響きの比(低い音を 1 とする)。和太鼓らしい、音程のずれた重なりになる
MEMBRANE = [(1.00, 1.0, 1.0), (1.59, 0.55, 1.6), (2.14, 0.35, 2.3), (2.30, 0.30, 2.6),
            (2.65, 0.22, 3.2), (2.92, 0.16, 3.8), (3.16, 0.12, 4.5), (3.50, 0.08, 5.5)]


def drumhead(f0, dur, decay, drop=0.06):
    """皮の響き。f0 は一番低い音、decay は低い音の消える速さ(小さいほど長く響く)。
    打った直後は皮が強く張るので、音がわずかに高く、すぐ落ち着く。"""
    t = np.arange(int(dur * SR)) / SR
    bend = 1 + drop * np.exp(-t * 12)
    y = np.zeros_like(t)
    for ratio, amp, dk in MEMBRANE:
        phase = 2 * np.pi * np.cumsum(f0 * ratio * bend) / SR + rng.uniform(0, 2 * np.pi)
        y += amp * np.sin(phase) * np.exp(-decay * dk * t)
    return t, y


def odaiko(vel=1.0, dur=3.2):
    """長胴太鼓(大太鼓)の「ドーン」。低く、長く響く。"""
    t, y = drumhead(78, dur, 1.15)
    y += 0.8 * np.sin(2 * np.pi * 52 * t) * np.exp(-t * 2.2) * np.minimum(1, t * 200)  # 腹に響く低い鳴り
    # 胴の木の鳴りと、撥が皮に当たる音(高すぎない、こもった音)
    n = rng.standard_normal(len(t))
    soft = np.convolve(n, np.ones(40) / 40, mode="same")
    y += soft * np.exp(-t * 18) * 3.0
    y += np.convolve(n, np.ones(6) / 6, mode="same") * np.exp(-t * 90) * 0.5
    y *= np.minimum(1, t * 600)
    return 0.6 * vel * y


def ka(vel=1.0, dur=0.25):
    """縁打ち「カッ」。撥で太鼓の木の縁を打つ乾いた音。"""
    t = np.arange(int(dur * SR)) / SR
    y = (np.sin(2 * np.pi * 1180 * t) + 0.7 * np.sin(2 * np.pi * 1870 * t)
         + 0.4 * np.sin(2 * np.pi * 2650 * t)) * np.exp(-t * 70)
    n = rng.standard_normal(len(t))
    y += (n - np.convolve(n, np.ones(4) / 4, mode="same")) * np.exp(-t * 400) * 0.3
    return 0.32 * vel * y


def shime(vel=1.0, dur=0.6):
    """締太鼓の「テン」。強く張った皮の、高く張りのある音。"""
    t, y = drumhead(420, dur, 9.0, drop=0.03)
    n = rng.standard_normal(len(t))
    y += np.convolve(n, np.ones(8) / 8, mode="same") * np.exp(-t * 160) * 0.6  # 撥の当たり
    y *= np.minimum(1, t * 900)
    return 0.3 * vel * y


def hyoshigi(vel=1.0, dur=0.3):
    """拍子木:歌舞伎で見得を切るときの「チョン」。"""
    t = np.arange(int(dur * SR)) / SR
    y = (np.sin(2 * np.pi * 2350 * t) + 0.6 * np.sin(2 * np.pi * 3720 * t)) * np.exp(-t * 55)
    y += rng.standard_normal(len(t)) * np.exp(-t * 300) * 0.4
    return 0.5 * vel * y


def groove(start, end, pattern, vel=1.0, beats=11):
    """start〜end を beats 拍に分け、16分音符ごとに pattern の文字で太鼓を打つ。
    O=大太鼓(強) o=大太鼓(弱) K=縁打ち「カッ」 X=締太鼓(強) x=締太鼓(弱) .=休み。
    pattern はくり返して使う。"""
    step = (end - start) / beats / 4
    n = int(round((end - start) / step))
    for i in range(n):
        ch = pattern[i % len(pattern)]
        tm = start + i * step
        if ch == "O":
            place(odaiko(1.0 * vel), tm, -0.05)
        elif ch == "o":
            place(odaiko(0.6 * vel), tm, -0.05)
        elif ch == "K":
            place(ka(0.9 * vel), tm, -0.15)
        elif ch == "X":
            place(shime(1.0 * vel), tm, 0.25)
        elif ch == "x":
            place(shime(0.55 * vel), tm, 0.25)


def voice(name, time, vel=1.0, pan=0.0):
    """sounds/kakegoe-<name>.wav の掛け声を置く。ファイルがなければ何もしない。"""
    path = SOUNDS / f"kakegoe-{name}.wav"
    if not path.exists():
        return
    with wave.open(str(path)) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32767
    place(0.55 * vel * x, time, pan)


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

# 区間7 洗馬→蒲原 夜之雪:雪が降りはじめる。高い琴の音を、雪のようにまばらに
note(c[6] + 0.3, 5, 0.45, dur=4.0)
for i, tm in enumerate(np.sort(rng.uniform(0.6, 4.6, 9))):
    note(c[6] + tm, int(rng.choice([12, 13, 15, 17, 18])), 0.22 + 0.02 * i, dur=2.5)
note(c[6] + 2.4, 8, 0.4, bend=-1.0, dur=4.0)

# 区間8 蒲原→日本橋 朝之景:夜が明け、行列が歩きだす。明るく上る琴と、歩みの刻み
run(c[7] + 1.0, c[7] + 2.6, [5, 7, 9, 10, 12, 14, 15], 0.6)
for d in (10, 14, 17):
    note(c[7] + 2.8, d, 0.75, dur=4.0)                    # 朝日
for tm, d in ((3.4, 15), (3.9, 14), (4.4, 12)):
    note(c[7] + tm, d, 0.5)

# 区間9 日本橋→大はし:空が急に暗くなり、夕立。細かく降る雨のような琴
note(c[8] + 1.2, 6, 0.6, bend=-1.0, dur=4.0)              # 空が暗くなる
rain = c[8] + np.sort(rng.uniform(2.0, 5.0, 22))
for i, tm in enumerate(rain):
    note(tm, int(rng.choice([13, 14, 15, 16, 17])), 0.18 + 0.012 * i, dur=1.2)

# 区間10 大はし→庄野 白雨:雨が強まり、人々が坂を駆ける。速く下る琴
run(c[9] + 0.6, c[9] + 2.0, [17, 15, 14, 12, 10, 9, 7], 0.6)
run(c[9] + 2.6, c[9] + 4.4, [7, 9, 10, 12, 10, 12, 14, 12, 14, 15], 0.6)

# 区間11 庄野→山下白雨:雨雲が晴れ、黒い富士がそびえ、稲妻が走る
run(c[10] + 0.8, c[10] + 2.3, [5, 7, 9, 10, 12, 14, 15, 17], 0.65)
for d in (5, 9, 12, 15):
    note(c[10] + 2.5, d, 0.85, dur=4.0)                   # 富士がそびえる
note(c[10] + 3.7, 18, 0.7, bend=1.0)                      # 稲妻

# 区間12 山下白雨→大波:川がふくらみ、大波へ。だんだん速く強く(区間1の始まりへ流れ込む)
times = c[11] + 0.3 + np.cumsum(np.geomspace(0.5, 0.12, 14))
for i, tm in enumerate(times):
    if tm < T - 0.05:
        note(tm, [2, 5, 7, 5, 7, 9, 7, 9, 10, 9, 10, 12, 10, 12][i], 0.35 + 0.04 * i)
for tm in np.linspace(T - 1.2, T - 0.1, 6):
    place(taiko(0.25 + 0.1 * (tm - T + 1.2)), tm)
trem = np.arange(c[11] + 1.6, T - 0.06, 0.11)              # 速い刻み(だんだん強く)
for i, tm in enumerate(trem):
    sham(tm, [5, 5, 7, 5, 8, 7][i % 6] + (5 if i > len(trem) * 0.6 else 0),
         0.3 + 0.6 * i / len(trem), dur=0.7)

# ---- 太鼓のリズムと三味線の刻み(全体をダイナミックに) ----
# 区間1 大波:冒頭から力強く。砕けるところで大太鼓の連打
groove(c[0], c[1], "O.KoO.K.O.oKK.xK", 1.0)
for tm in (1.9, 2.05, 2.2):
    place(odaiko(1.0), c[0] + tm)
sham_run(c[0] + 2.4, c[1], [10, 8, 10, 7, 10, 8, 12, 10, 8, 7, 8, 10, 12, 13, 12, 10, 8, 7, 5, 7], 0.6)
# 区間2 赤富士→鳳凰:刻みを重ね、鳳凰が現れるところで大きく
groove(c[1], c[2], "O.xKK.x.o.oKK.xK", 0.9)
sham_run(c[1] + 0.2, c[1] + 1.55, [5, 7, 5, 8, 7, 5, 7, 8], 0.55)
for tm in (2.6, 2.75):
    place(odaiko(1.0), c[1] + tm)
sham_run(c[1] + 3.0, c[2], [15, 13, 15, 12, 13, 10, 12, 10, 8, 10], 0.6)
# 区間3 鳳凰→写楽:締太鼓がだんだん速くなり、見得で大太鼓と拍子木
for i, tm in enumerate(c[2] + 0.2 + np.cumsum(np.geomspace(0.3, 0.07, 24))):
    if tm < c[2] + 2.95:
        place(shime(0.4 + 0.025 * i), tm, 0.25)
place(odaiko(1.0), c[2] + 3.0); place(odaiko(1.0), c[2] + 3.25)
place(hyoshigi(1.0), c[2] + 3.55, 0.3); place(hyoshigi(0.9), c[2] + 3.8, 0.3)  # 拍子木「チョン、チョン」
# 区間4 写楽→北斎:静まるが、大太鼓の鼓動は残す
groove(c[3], c[4], "O.xKK.x.o.xKK.xK", 0.85)
sham_run(c[3] + 0.3, c[3] + 1.6, [12, 10, 8, 7, 5], 0.5)
# 区間5 北斎→江尻:風。締太鼓の速い刻みと、三味線の速い駆け回り
groove(c[4], c[5], "O.KxK.xKo.oKKxKx", 0.85)
for start in (0.3, 1.6, 2.9):
    k = int(rng.integers(8, 12))
    sham_run(c[4] + start, c[4] + start + 0.95, [k, k + 2, k + 1, k + 3, k + 2, k + 4, k + 3, k + 1], 0.55)
# 区間6 江尻→洗馬:日暮れ。ゆったりした大太鼓と、三味線の静かな節
groove(c[5], c[6], "O.xKK.xKo.xKK.xK", 0.8)
for tm, d, sl in ((0.9, 7, 0.0), (1.8, 8, 1.0), (3.2, 10, 0.0), (3.7, 8, -1.0)):
    sham(c[5] + tm, d, 0.45, slide=sl, dur=1.6)
# 区間7 洗馬→蒲原:雪の夜。太鼓はほとんど止め、三味線を静かに
place(odaiko(0.5), c[6] + 0.2)
for tm, d, sl in ((1.2, 5, 0.0), (2.6, 8, -1.0), (4.0, 7, 0.0)):
    sham(c[6] + tm, d, 0.35, slide=sl, dur=1.8)
# 区間8 蒲原→日本橋:夜明けの旅立ち。拍子木が鳴り、行列の歩みの刻みが始まる
place(hyoshigi(0.9), c[7] + 0.9, 0.3); place(hyoshigi(0.8), c[7] + 1.15, 0.3)
groove(c[7] + 1.6, c[8], "O...K...o...K.x.", 0.7)
sham_run(c[7] + 2.8, c[8], [10, 12, 10, 8, 10, 12, 13, 12, 10, 8], 0.5)
# 区間9 日本橋→大はし:夕立。締太鼓の細かい刻みが雨のように強まる
groove(c[8], c[8] + 1.8, "O...K...o...K.x.", 0.7)
for i, tm in enumerate(np.arange(c[8] + 1.8, c[9], 0.09)):
    place(shime(0.25 + 0.3 * (tm - c[8] - 1.8) / (c[9] - c[8] - 1.8)), tm, 0.2 * ((i % 2) * 2 - 1))
place(odaiko(0.9), c[8] + 1.8)
sham_run(c[8] + 2.0, c[9], [8, 7, 5, 7, 8, 10, 8, 7, 8, 10, 12, 10], 0.5)
# 区間10 大はし→庄野:雨の坂を駆ける。速い太鼓と三味線の駆け回り
groove(c[9], c[10], "O.KxK.xKo.oKKxKx", 0.9)
for start in (0.4, 1.7, 3.0):
    k = int(rng.integers(8, 12))
    sham_run(c[9] + start, c[9] + start + 0.95, [k, k + 2, k + 1, k + 3, k + 2, k + 4, k + 3, k + 1], 0.6)
# 区間11 庄野→山下白雨:富士が現れるところで大太鼓、稲妻で一撃
groove(c[10], c[10] + 2.3, "O.xKK.x.o.oKK.xK", 0.85)
sham_run(c[10] + 0.6, c[10] + 2.3, [5, 7, 8, 10, 12, 13, 15, 17], 0.6)
for tm in (2.5, 2.65):
    place(odaiko(1.0), c[10] + tm)
for d in (5, 10, 12):
    sham(c[10] + 3.7, d, 1.0, dur=1.6)                    # 稲妻
groove(c[10] + 3.0, c[11], "O.xKK.x.o.xKK.xK", 0.8)
# 区間12 山下白雨→大波:だんだん速く強く、大波へ流れ込む
for i, tm in enumerate(c[11] + 0.1 + np.cumsum(np.geomspace(0.45, 0.06, 30))):
    if tm < T - 0.05:
        place(shime(0.35 + 0.02 * i), tm, 0.25)
for tm in (c[11] + 1.0, c[11] + 2.0, c[11] + 2.6, c[11] + 3.1, c[11] + 3.5, T - 0.25):
    place(odaiko(0.8), tm)

# ---- 掛け声 ----
voice("ha1", c[0] + 1.8, 1.0, -0.1)          # 大波が砕ける
voice("iyaa", c[1] + 2.35, 0.9, 0.1)         # 鳳凰が現れる
voice("nipponichi", c[2] + 4.05, 0.9, 0.25)  # 写楽の見得のあとに、大向こうから「日本一!」
voice("sore", c[4] + 0.2, 0.9, -0.1)         # 江尻の風が起こる
voice("iyaa", c[7] + 2.8, 0.8, -0.1)         # 日本橋の夜明け、行列が歩きだす
voice("sore", c[9] + 0.4, 0.9, 0.1)          # 雨の坂を駆けだす
voice("ha1", c[10] + 2.5, 0.9, -0.1)         # 黒い富士が現れる
voice("ha2", c[11] + 2.0, 0.9, 0.1)          # 大波へ向けて盛り上がる途中
voice("yoo", T - 1.45, 1.0, 0.0)             # 一周の終わりに「よーっ!」、そのまま最初の大波へ

# ---- 静かだった場面も盛り上げる ----
sham_run(c[3] + 1.7, c[4], [7, 8, 10, 8, 7, 5, 7, 8, 10, 12, 10, 8, 10, 12, 13, 12], 0.55)
sham_run(c[5] + 0.3, c[6] - 0.1, [5, 7, 8, 7, 5, 7, 8, 10, 8, 7, 8, 10, 12, 10, 8, 10, 12, 13, 12, 10], 0.5)
groove(c[11], T, "O.xKO.xKO.xKOxKx", 0.9, beats=9)

# ---- 山場を大きく:「カカカッ」の連打のあとに大太鼓の連打 ----
def climax(at, ka_n=4, don_n=3, gap=0.15):
    for i in range(ka_n):                               # 山場の直前の「カカカッ」
        place(ka(0.8 + 0.1 * i), at - (ka_n - i) * 0.07, -0.15)
    for i in range(don_n):                              # 大太鼓の連打
        place(odaiko(1.0), at + i * gap, -0.05 + 0.1 * (i % 2))


climax(c[0] + 1.8, 4, 4)          # 大波が砕ける
climax(c[1] + 2.6, 5, 3)          # 鳳凰が現れる
climax(c[2] + 3.0, 6, 2, 0.25)    # 写楽の見得
climax(c[4] + 0.2, 3, 2)          # 江尻の風が起こる
climax(c[8] + 1.8, 3, 2)          # 夕立が降りだす
climax(c[10] + 2.5, 5, 3)         # 黒い富士が現れる
# 最後の盛り上がり:締太鼓の刻みに「カッ」を重ね、最後の1秒は大太鼓の連打で最初の大波へ
for i, tm in enumerate(np.arange(T - 2.0, T - 0.05, 0.14)):
    if i % 2:
        place(ka(0.5 + 0.03 * i), tm, -0.15)
for i, tm in enumerate(T - 1.0 + np.cumsum(np.geomspace(0.2, 0.07, 9)) - 0.2):
    if tm < T - 0.03:
        place(odaiko(0.6 + 0.05 * i), tm, -0.05 + 0.1 * (i % 2))

# ---- 抑揚:山場以外を少し抑え、山場を大きく ----
# 1周を「輪」として扱い、終わりの盛り上がりがそのまま始まりの大波へ続くようにする
t_all = np.arange(L) / SR
peaks = [(c[0] + 1.9, 1.6), (c[1] + 2.7, 1.1), (c[2] + 3.2, 0.9), (c[4] + 0.4, 0.8),
         (c[7] + 2.8, 0.9), (c[9] + 1.5, 1.4), (c[10] + 2.7, 1.2), (T - 0.2, 2.2)]
lift = np.zeros(L)
for at, width in peaks:
    dt = (t_all - at + T / 2) % T - T / 2              # 1周の輪の上での距離
    lift = np.maximum(lift, np.exp(-(dt / width) ** 2))
buf *= 0.78 + 0.22 * lift

# 低い持続音:レとラ。1周でちょうど整数回振動する高さにして、つなぎ目で位相がずれないようにする
t = np.arange(L) / SR
drone = np.zeros(L)
for f, a in ((73.42, 0.03), (110.0, 0.018), (146.83, 0.01)):
    f_loop = round(f * T) / T
    drone += a * np.sin(2 * np.pi * f_loop * t)
breath = 0.65 + 0.35 * np.sin(2 * np.pi * 3 * t / T - np.pi / 2)  # 1周で3回ゆっくり息をする
buf += drone * breath

# 残響:1周を「輪」とみなしてかける(終わりの響きが始まりに自然につながる)
ir_t = np.arange(int(3.0 * SR)) / SR
ir = rng.standard_normal(len(ir_t)) * np.exp(-ir_t / 0.75)
ir = np.convolve(ir, np.ones(8) / 8, mode="same")     # 響きを少し柔らかく
ir /= np.sqrt(np.sum(ir ** 2))
IR = np.fft.rfft(np.pad(ir, (0, L - len(ir))))
wet = np.stack([np.fft.irfft(np.fft.rfft(ch) * IR, n=L) for ch in buf])
mix = 0.9 * buf + 0.25 * wet

# 音圧を上げる:いったんそろえてから、やわらかく頭を丸める(割れないように)
mix /= np.max(np.abs(mix))
mix = np.tanh(2.3 * mix) / np.tanh(2.3)
mix *= 0.9
pcm = (mix.T * 32767).astype(np.int16)
OUT.parent.mkdir(parents=True, exist_ok=True)
with wave.open(str(OUT), "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f"作りました: {OUT.relative_to(ROOT)}  {L / SR:.3f} 秒")
