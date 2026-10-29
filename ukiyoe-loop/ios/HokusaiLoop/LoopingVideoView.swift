import AVFoundation
import SwiftUI
import UIKit

/// アプリに同梱した動画を、つなぎ目なしでくり返し再生する画面。
/// 動画全体が見えるように収め、余白は黒にする。
/// 音楽(動画の1周と同じ長さ)があれば、動画と一緒にくり返し流す。
struct LoopingVideoView: UIViewRepresentable {
    let video: String
    let music: String

    func makeUIView(context: Context) -> PlayerUIView {
        PlayerUIView(
            videoURL: Bundle.main.url(forResource: video, withExtension: "mp4"),
            musicURL: Bundle.main.url(forResource: music, withExtension: "wav")
        )
    }

    func updateUIView(_ uiView: PlayerUIView, context: Context) {}
}

final class PlayerUIView: UIView {
    override class var layerClass: AnyClass { AVPlayerLayer.self }
    private var playerLayer: AVPlayerLayer { layer as! AVPlayerLayer }

    private let player = AVQueuePlayer()
    private var looper: AVPlayerLooper?
    private var music: AVAudioPlayer?
    private var loopObservation: NSKeyValueObservation?
    private var activeObserver: NSObjectProtocol?

    init(videoURL: URL?, musicURL: URL?) {
        super.init(frame: .zero)
        backgroundColor = .black
        playerLayer.videoGravity = .resizeAspect
        playerLayer.player = player
        player.isMuted = true  // 動画そのものには音がない。音楽は別に流す

        guard let videoURL else {
            // 動画がまだ入っていないときは黒い画面のまま。
            return
        }

        // 音楽は WAV(圧縮なし)で持ち、AVAudioPlayer でくり返す。
        // 圧縮した音声と違って先頭に無音が入らないので、つなぎ目で途切れない。
        if let musicURL, let audio = try? AVAudioPlayer(contentsOf: musicURL) {
            audio.numberOfLoops = -1
            audio.volume = 0.8
            audio.prepareToPlay()
            music = audio
        }

        // AVPlayerLooper は次の回を先に読み込んでおくので、くり返しの継ぎ目で止まらない。
        looper = AVPlayerLooper(player: player, templateItem: AVPlayerItem(url: videoURL))
        startTogether()

        // 動画が1周するたびに、音楽とのずれを確かめる(長く流していても絵と音がずれないように)。
        loopObservation = looper?.observe(\.loopCount, options: [.new]) { [weak self] _, _ in
            DispatchQueue.main.async { self?.resyncMusic() }
        }

        // 別のアプリから戻ってきたら、絵と音楽をそろえて最初から流し直す。
        activeObserver = NotificationCenter.default.addObserver(
            forName: UIApplication.didBecomeActiveNotification, object: nil, queue: .main
        ) { [weak self] _ in
            self?.startTogether()
        }
    }

    /// 絵と音楽を、同時に最初から流す。
    private func startTogether() {
        player.seek(to: .zero, toleranceBefore: .zero, toleranceAfter: .zero)
        music?.currentTime = 0
        player.play()
        music?.play()
    }

    /// 音楽が絵から 0.15 秒以上ずれていたら、絵の位置に合わせ直す。
    private func resyncMusic() {
        guard let music else { return }
        let video = player.currentTime().seconds
        guard video.isFinite else { return }
        var diff = music.currentTime - video
        // 片方だけ先に1周して巻き戻った直後は、1周の長さぶん離れて見えるので補正する
        let length = music.duration
        if diff > length / 2 { diff -= length } else if diff < -length / 2 { diff += length }
        if abs(diff) > 0.15 {
            music.currentTime = max(0, video)
        }
    }

    required init?(coder: NSCoder) {
        fatalError("init(coder:) is not used")
    }

    deinit {
        if let activeObserver {
            NotificationCenter.default.removeObserver(activeObserver)
        }
    }
}
