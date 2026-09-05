package info.cemu.cemu

import android.app.Activity
import android.app.Dialog
import android.graphics.Color
import android.graphics.drawable.ColorDrawable
import android.os.Handler
import android.os.Looper
import android.view.Gravity
import android.view.ViewGroup
import android.view.Window
import android.widget.FrameLayout
import androidx.mediarouter.app.MediaRouteButton
import com.google.android.gms.cast.MediaInfo
import com.google.android.gms.cast.MediaLoadRequestData
import com.google.android.gms.cast.MediaMetadata
import com.google.android.gms.cast.framework.CastButtonFactory
import com.google.android.gms.cast.framework.CastContext
import com.google.android.gms.cast.framework.CastSession
import com.google.android.gms.cast.framework.SessionManagerListener
import java.lang.ref.WeakReference
import java.util.concurrent.atomic.AtomicBoolean

/**
 * WUDROID_TV_CAST_STREAM1
 *
 * Sender-only Google Cast bridge. The TV uses Google's Default Media Receiver;
 * Wudroid itself remains installed only on the phone.
 */
data class WudroidCastState(
    val connected: Boolean = false,
    val deviceName: String? = null,
    val loading: Boolean = false,
    val error: String? = null,
)

object WudroidCastController {
    private val mainHandler = Handler(Looper.getMainLooper())
    private val initialized = AtomicBoolean(false)

    @Volatile
    private var activityRef: WeakReference<Activity>? = null

    @Volatile
    private var castContext: CastContext? = null

    @Volatile
    private var castSession: CastSession? = null

    @Volatile
    private var stateListener: ((WudroidCastState) -> Unit)? = null

    @Volatile
    private var state = WudroidCastState()

    @Volatile
    private var pendingMode: String = "GAME"

    private val sessionListener = object : SessionManagerListener<CastSession> {
        override fun onSessionStarting(session: CastSession) {
            updateState(state.copy(loading = true, error = null))
        }

        override fun onSessionStarted(session: CastSession, sessionId: String) {
            castSession = session
            val name = runCatching { session.castDevice?.friendlyName }.getOrNull()
            updateState(WudroidCastState(connected = true, deviceName = name, loading = true))
            loadLiveStreamWhenReady(session)
        }

        override fun onSessionStartFailed(session: CastSession, error: Int) {
            castSession = null
            WudroidCastHlsServer.stop()
            updateState(WudroidCastState(error = "Falha ao conectar à TV ($error)"))
        }

        override fun onSessionEnding(session: CastSession) = Unit

        override fun onSessionEnded(session: CastSession, error: Int) {
            castSession = null
            WudroidCastHlsServer.stop()
            updateState(WudroidCastState())
        }

        override fun onSessionResuming(session: CastSession, sessionId: String) {
            updateState(state.copy(loading = true, error = null))
        }

        override fun onSessionResumed(session: CastSession, wasSuspended: Boolean) {
            castSession = session
            val name = runCatching { session.castDevice?.friendlyName }.getOrNull()
            updateState(WudroidCastState(connected = true, deviceName = name, loading = true))
            val activity = activityRef?.get()
            if (activity != null) {
                WudroidCastHlsServer.start(activity)
            }
            loadLiveStreamWhenReady(session)
        }

        override fun onSessionResumeFailed(session: CastSession, error: Int) {
            castSession = null
            WudroidCastHlsServer.stop()
            updateState(WudroidCastState(error = "Não foi possível retomar a transmissão"))
        }

        override fun onSessionSuspended(session: CastSession, reason: Int) {
            updateState(state.copy(loading = true))
        }
    }

    fun setStateListener(listener: ((WudroidCastState) -> Unit)?) {
        stateListener = listener
        listener?.invoke(state)
    }

    fun currentState(): WudroidCastState = state

    fun initialize(activity: Activity): Boolean {
        activityRef = WeakReference(activity)
        if (initialized.get()) return castContext != null

        return try {
            val context = CastContext.getSharedInstance(activity.applicationContext)
            castContext = context
            context.sessionManager.addSessionManagerListener(sessionListener, CastSession::class.java)
            castSession = context.sessionManager.currentCastSession
            initialized.set(true)
            true
        } catch (t: Throwable) {
            updateState(WudroidCastState(error = "Google Cast indisponível: ${t.message ?: "erro"}"))
            false
        }
    }

    /**
     * Opens Google's official device picker directly after Game/Motion Game is chosen.
     * Wudroid starts its local HLS source before the receiver connects, so the first
     * video segments are already being prepared while the user picks the TV.
     */
    fun openDevicePicker(activity: Activity, mode: String) {
        pendingMode = mode
        activityRef = WeakReference(activity)

        if (!initialize(activity)) return

        if (!WudroidCastHlsServer.start(activity)) {
            updateState(WudroidCastState(error = "Não foi possível iniciar o vídeo para a TV"))
            return
        }

        // If there is already a Cast session, reuse it and reload the Wudroid live stream.
        castContext?.sessionManager?.currentCastSession?.let { existing ->
            castSession = existing
            val name = runCatching { existing.castDevice?.friendlyName }.getOrNull()
            updateState(WudroidCastState(connected = true, deviceName = name, loading = true))
            loadLiveStreamWhenReady(existing)
            return
        }

        mainHandler.post {
            try {
                // MediaRouteButton is the official CAF picker. Attach it to a tiny,
                // transparent dialog so performClick() can immediately show Google's
                // real Cast device list without adding another visible button to Wudroid.
                val shell = Dialog(activity)
                shell.requestWindowFeature(Window.FEATURE_NO_TITLE)
                val root = FrameLayout(activity)
                val routeButton = MediaRouteButton(activity)
                root.addView(
                    routeButton,
                    FrameLayout.LayoutParams(2, 2, Gravity.CENTER),
                )
                shell.setContentView(root)
                shell.window?.apply {
                    setBackgroundDrawable(ColorDrawable(Color.TRANSPARENT))
                    setDimAmount(0f)
                    setLayout(2, 2)
                }
                shell.show()

                CastButtonFactory.setUpMediaRouteButton(activity.applicationContext, routeButton)
                routeButton.postDelayed({
                    val opened = runCatching { routeButton.performClick() }.getOrDefault(false)
                    if (!opened) {
                        updateState(WudroidCastState(error = "Nenhuma TV Cast disponível"))
                    }
                    routeButton.postDelayed({ runCatching { shell.dismiss() } }, 350L)
                }, 180L)
            } catch (t: Throwable) {
                updateState(WudroidCastState(error = "Não foi possível abrir a lista de TVs"))
            }
        }
    }

    fun stopCasting() {
        mainHandler.post {
            runCatching { castSession?.remoteMediaClient?.stop() }
            runCatching { castContext?.sessionManager?.endCurrentSession(true) }
            castSession = null
            WudroidCastHlsServer.stop()
            updateState(WudroidCastState())
        }
    }

    private fun loadLiveStreamWhenReady(session: CastSession) {
        val activity = activityRef?.get() ?: return
        if (!WudroidCastHlsServer.isRunning()) {
            WudroidCastHlsServer.start(activity)
        }

        Thread({
            val deadline = System.currentTimeMillis() + 9_000L
            while (
                System.currentTimeMillis() < deadline &&
                !WudroidCastHlsServer.isReady()
            ) {
                try {
                    Thread.sleep(80L)
                } catch (_: InterruptedException) {
                    return@Thread
                }
            }

            val url = WudroidCastHlsServer.playlistUrl(activity)
            if (url == null || !WudroidCastHlsServer.isReady()) {
                updateState(state.copy(loading = false, error = "O vídeo do jogo ainda não ficou pronto"))
                return@Thread
            }

            mainHandler.post {
                if (castSession !== session && castSession != null) return@post

                try {
                    val metadata = MediaMetadata(MediaMetadata.MEDIA_TYPE_GENERIC).apply {
                        putString(MediaMetadata.KEY_TITLE, "Wudroid")
                        putString(
                            MediaMetadata.KEY_SUBTITLE,
                            if (pendingMode == "MOTION") "Motion Game" else "Game",
                        )
                    }
                    val mediaInfo = MediaInfo.Builder(url)
                        .setStreamType(MediaInfo.STREAM_TYPE_LIVE)
                        .setContentType("application/x-mpegURL")
                        .setMetadata(metadata)
                        .build()
                    val request = MediaLoadRequestData.Builder()
                        .setMediaInfo(mediaInfo)
                        .setAutoplay(true)
                        .build()

                    val client = session.remoteMediaClient
                    if (client == null) {
                        updateState(state.copy(loading = false, error = "A TV não abriu o player Cast"))
                        return@post
                    }
                    client.load(request)
                    val name = runCatching { session.castDevice?.friendlyName }.getOrNull()
                    updateState(WudroidCastState(connected = true, deviceName = name, loading = false))
                } catch (t: Throwable) {
                    updateState(state.copy(loading = false, error = "Falha ao iniciar vídeo na TV"))
                }
            }
        }, "Wudroid-Cast-Load").apply {
            isDaemon = true
            start()
        }
    }

    private fun updateState(newState: WudroidCastState) {
        state = newState
        mainHandler.post {
            stateListener?.invoke(newState)
        }
    }
}
