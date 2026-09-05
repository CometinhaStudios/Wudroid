package info.cemu.cemu

import android.content.pm.ActivityInfo
import android.graphics.Color as AndroidColor
import android.os.Bundle
import android.view.SurfaceHolder
import android.view.SurfaceView
import android.view.WindowManager
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetSocketAddress
import java.util.concurrent.atomic.AtomicBoolean

/**
 * WUDROID_TV_DIRECT_LINK1_RECEIVER
 * Launch target for Android TV / Google TV. The same Wudroid APK can be
 * installed on the TV; this activity advertises itself and decodes the exact
 * H.264/UDP stream already used by Player 2 multiplayer.
 */
class WudroidTvReceiverActivity : ComponentActivity() {
    private val running = AtomicBoolean(false)
    private var discoverySocket: DatagramSocket? = null
    private var videoSocket: DatagramSocket? = null
    private var discoveryThread: Thread? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        requestedOrientation = ActivityInfo.SCREEN_ORIENTATION_SENSOR_LANDSCAPE
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        window.statusBarColor = AndroidColor.BLACK
        window.navigationBarColor = AndroidColor.BLACK

        startReceiverTransport()

        setContent {
            MaterialTheme {
                val status by WudroidLanVideoClient.statusFlow.collectAsState()
                Box(Modifier.fillMaxSize().background(Color.Black)) {
                    AndroidView(
                        modifier = Modifier.fillMaxSize(),
                        factory = { context ->
                            SurfaceView(context).apply {
                                keepScreenOn = true
                                holder.setFixedSize(640, 360)
                                holder.addCallback(object : SurfaceHolder.Callback {
                                    override fun surfaceCreated(holder: SurfaceHolder) {
                                        if (holder.surface.isValid) {
                                            WudroidLanVideoClient.attachSurface(holder.surface)
                                        }
                                    }

                                    override fun surfaceChanged(
                                        holder: SurfaceHolder,
                                        format: Int,
                                        width: Int,
                                        height: Int,
                                    ) {
                                        if (holder.surface.isValid) {
                                            WudroidLanVideoClient.attachSurface(holder.surface)
                                        }
                                    }

                                    override fun surfaceDestroyed(holder: SurfaceHolder) {
                                        WudroidLanVideoClient.detachSurface()
                                    }
                                })
                            }
                        },
                    )

                    Column(
                        modifier = Modifier
                            .align(Alignment.TopStart)
                            .padding(18.dp)
                            .background(Color(0xB8000000))
                            .padding(horizontal = 14.dp, vertical = 10.dp),
                    ) {
                        Text(
                            "Wudroid TV",
                            color = Color(0xFF00B8F5),
                            fontSize = 20.sp,
                            fontWeight = FontWeight.Bold,
                        )
                        Text(status, color = Color.White, fontSize = 12.sp)
                    }
                }

                DisposableEffect(Unit) {
                    onDispose { WudroidLanVideoClient.detachSurface() }
                }
            }
        }
    }

    private fun startReceiverTransport() {
        if (!running.compareAndSet(false, true)) return

        val video = DatagramSocket(null).apply {
            reuseAddress = true
            bind(InetSocketAddress(WudroidTvDirectHost.VIDEO_PORT))
            receiveBufferSize = 128 * 1024
        }
        videoSocket = video
        WudroidLanVideoClient.start(video)

        val discovery = DatagramSocket(null).apply {
            reuseAddress = true
            broadcast = true
            soTimeout = 400
            bind(InetSocketAddress(WudroidTvDirectHost.DISCOVERY_PORT))
        }
        discoverySocket = discovery

        discoveryThread = Thread({
            val buffer = ByteArray(800)
            while (running.get() && !discovery.isClosed) {
                try {
                    val packet = DatagramPacket(buffer, buffer.size)
                    discovery.receive(packet)
                    val text = String(packet.data, packet.offset, packet.length, Charsets.UTF_8)
                    val parts = text.split("|", limit = 3)
                    if (parts.size < 2 || parts[0] != WudroidTvDirectHost.discoveryRequestPrefix()) {
                        continue
                    }
                    val nonce = parts[1].take(32)
                    val reply = listOf(
                        WudroidTvDirectHost.discoveryReplyPrefix(),
                        nonce,
                        WudroidTvDirectHost.receiverName().replace("|", " "),
                        WudroidTvDirectHost.VIDEO_PORT.toString(),
                    ).joinToString("|").toByteArray(Charsets.UTF_8)
                    discovery.send(DatagramPacket(reply, reply.size, packet.address, packet.port))
                } catch (_: Throwable) {
                }
            }
        }, "Wudroid-TV-Discovery").apply {
            isDaemon = true
            start()
        }
    }

    override fun onDestroy() {
        running.set(false)
        WudroidLanVideoClient.stop(clearStatus = true)
        runCatching { discoverySocket?.close() }
        runCatching { videoSocket?.close() }
        discoverySocket = null
        videoSocket = null
        discoveryThread = null
        super.onDestroy()
    }
}
