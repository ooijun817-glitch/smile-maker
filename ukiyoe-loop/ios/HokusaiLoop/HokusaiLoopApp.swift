import AVFoundation
import SwiftUI

/// 浮世絵が動く動画を、全画面でくり返し流すだけのアプリ。和風の音楽も一緒に流す。
/// 文字やボタンは出さない。開いているあいだは画面を自動で消さない。
@main
struct HokusaiLoopApp: App {
    @Environment(\.scenePhase) private var scenePhase

    init() {
        // ambient:iPhone の消音スイッチ(マナーモード)に従い、消音中は音楽を鳴らさない。
        // 夜の枕元で使うので、こちらにしている。他のアプリの音も止めない。
        try? AVAudioSession.sharedInstance().setCategory(.ambient, options: [.mixWithOthers])
        try? AVAudioSession.sharedInstance().setActive(true)
    }

    var body: some Scene {
        WindowGroup {
            LoopingVideoView(video: "hokusai-loop", music: "hokusai-music")
                .ignoresSafeArea()
                .background(Color.black)
                .statusBarHidden(true)
                .persistentSystemOverlays(.hidden)
                .onAppear { UIApplication.shared.isIdleTimerDisabled = true }
        }
        .onChange(of: scenePhase) { _, phase in
            // 前に出ているあいだだけ、画面の自動消灯を止める。
            UIApplication.shared.isIdleTimerDisabled = (phase == .active)
        }
    }
}
