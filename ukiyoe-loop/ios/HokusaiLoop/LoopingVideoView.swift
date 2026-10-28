import AVFoundation
import SwiftUI
import UIKit

/// アプリに同梱した動画を、つなぎ目なしでくり返し再生する画面。
/// 動画全体が見えるように収め、余白は黒にする。
struct LoopingVideoView: UIViewRepresentable {
    let resource: String
    let withExtension: String

    func makeUIView(context: Context) -> PlayerUIView {
        PlayerUIView(url: Bundle.main.url(forResource: resource, withExtension: withExtension))
    }

    func updateUIView(_ uiView: PlayerUIView, context: Context) {}
}

final class PlayerUIView: UIView {
    override class var layerClass: AnyClass { AVPlayerLayer.self }
    private var playerLayer: AVPlayerLayer { layer as! AVPlayerLayer }

    private let player = AVQueuePlayer()
    private var looper: AVPlayerLooper?
    private var activeObserver: NSObjectProtocol?

    init(url: URL?) {
        super.init(frame: .zero)
        backgroundColor = .black
        playerLayer.videoGravity = .resizeAspect
        playerLayer.player = player
        player.isMuted = true

        guard let url else {
            // 動画がまだ入っていないときは黒い画面のまま。
            return
        }
        // AVPlayerLooper は次の回を先に読み込んでおくので、くり返しの継ぎ目で止まらない。
        looper = AVPlayerLooper(player: player, templateItem: AVPlayerItem(url: url))
        player.play()

        // 別のアプリから戻ってきたら再開する。
        activeObserver = NotificationCenter.default.addObserver(
            forName: UIApplication.didBecomeActiveNotification, object: nil, queue: .main
        ) { [weak self] _ in
            self?.player.play()
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
