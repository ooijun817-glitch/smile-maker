import AVFoundation
import SwiftUI

/// 北斎の浮世絵が動く動画を、全画面・音なしでくり返し流すだけのアプリ。
/// 文字やボタンは出さない。開いているあいだは画面を自動で消さない。
@main
struct HokusaiLoopApp: App {
    @Environment(\.scenePhase) private var scenePhase

    init() {
        // 動画に音はないが、念のため他のアプリの音(音楽など)を止めない設定にしておく。
        try? AVAudioSession.sharedInstance().setCategory(.ambient, options: [.mixWithOthers])
    }

    var body: some Scene {
        WindowGroup {
            LoopingVideoView(resource: "hokusai-loop", withExtension: "mp4")
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
