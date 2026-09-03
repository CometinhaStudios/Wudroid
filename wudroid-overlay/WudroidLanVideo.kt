package info.cemu.cemu

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.os.Handler
import android.os.HandlerThread
import android.view.PixelCopy
import android.view.SurfaceView
import java.io.ByteArrayOutputStream
import java.lang.ref.WeakReference
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress
import java.nio.ByteBuffer
import java.util.concurrent.atomic.AtomicBoolean
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

data class WudroidVideoTarget(
    val address: String,
    val port: Int,
)

object WudroidLanVideoHost {
    private const val MAGIC = 0x5756314A // WV1J
    private const val HEADER_SIZE = 12
    private const val MAX_PACKET_PAYLOAD = 1180

    // First proof-of-concept: intentionally light to protect emulation FPS.
    private const val MAX_WIDTH = 480
    private const val MAX_HEIGHT = 270
    private const val JPEG_QUALITY = 52
    private const val FRAME_INTERVAL_MS = 100L // ~10 FPS

    private val active = AtomicBoolean(false)

    private val captureThread =
        HandlerThread("Wudroid-LAN-Video-Capture").apply {
            start()
        }

    private val handler = Handler(captureThread.looper)

    @Volatile
    private var surfaceRef: WeakReference<SurfaceView>? = null

    @Volatile
    private var captureBitmap: Bitmap? = null

    @Volatile
    private var nextFrameId = 1

    private val senderSocket by lazy {
        DatagramSocket().apply {
            broadcast = false
            sendBufferSize = 512 * 1024
        }
    }

    fun attachSurfaceView(surfaceView: SurfaceView) {
        surfaceRef = WeakReference(surfaceView)

        if (active.compareAndSet(false, true)) {
            handler.post(::captureNext)
        }
    }

    fun detachSurfaceView(surfaceView: SurfaceView) {
        val current = surfaceRef?.get()

        if (current === surfaceView) {
            surfaceRef = null
            active.set(false)

            handler.post {
                captureBitmap?.let { bitmap ->
                    if (!bitmap.isRecycled) {
                        bitmap.recycle()
                    }
                }
                captureBitmap = null
            }
        }
    }

    private fun chooseSize(
        sourceWidth: Int,
        sourceHeight: Int,
    ): Pair<Int, Int> {
        if (sourceWidth <= 0 || sourceHeight <= 0) {
            return MAX_WIDTH to MAX_HEIGHT
        }

        val scale = minOf(
            MAX_WIDTH.toFloat() / sourceWidth,
            MAX_HEIGHT.toFloat() / sourceHeight,
            1f,
        )

        var width =
            (sourceWidth * scale).toInt().coerceAtLeast(2)
        var height =
            (sourceHeight * scale).toInt().coerceAtLeast(2)

        if (width % 2 != 0) width -= 1
        if (height % 2 != 0) height -= 1

        return width.coerceAtLeast(2) to
            height.coerceAtLeast(2)
    }

    private fun bitmapFor(
        width: Int,
        height: Int,
    ): Bitmap {
        val old = captureBitmap

        if (
            old != null &&
            !old.isRecycled &&
            old.width == width &&
            old.height == height
        ) {
            return old
        }

        old?.let {
            if (!it.isRecycled) {
                it.recycle()
            }
        }

        return Bitmap.createBitmap(
            width,
            height,
            Bitmap.Config.ARGB_8888,
        ).also {
            captureBitmap = it
        }
    }

    private fun captureNext() {
        if (!active.get()) {
            return
        }

        val target =
            WudroidLanMultiplayer.videoTarget()
        val surfaceView =
            surfaceRef?.get()

        if (
            target == null ||
            surfaceView == null ||
            !surfaceView.holder.surface.isValid ||
            surfaceView.width <= 1 ||
            surfaceView.height <= 1
        ) {
            handler.postDelayed(::captureNext, 180L)
            return
        }

        val (width, height) =
            chooseSize(
                surfaceView.width,
                surfaceView.height,
            )

        val bitmap =
            bitmapFor(width, height)

        try {
            PixelCopy.request(
                surfaceView,
                bitmap,
                { result ->
                    if (
                        result == PixelCopy.SUCCESS &&
                        active.get()
                    ) {
                        sendBitmap(bitmap, target)
                    }

                    if (active.get()) {
                        handler.postDelayed(
                            ::captureNext,
                            FRAME_INTERVAL_MS,
                        )
                    }
                },
                handler,
            )
        } catch (_: Throwable) {
            handler.postDelayed(::captureNext, 220L)
        }
    }

    private fun sendBitmap(
        bitmap: Bitmap,
        target: WudroidVideoTarget,
    ) {
        val output =
            ByteArrayOutputStream(64 * 1024)

        val encoded =
            runCatching {
                bitmap.compress(
                    Bitmap.CompressFormat.JPEG,
                    JPEG_QUALITY,
                    output,
                )
            }.getOrDefault(false)

        if (!encoded) {
            return
        }

        val bytes = output.toByteArray()

        if (
            bytes.isEmpty() ||
            bytes.size > 900_000
        ) {
            return
        }

        val chunkCount =
            (bytes.size + MAX_PACKET_PAYLOAD - 1) /
                MAX_PACKET_PAYLOAD

        if (chunkCount !in 1..512) {
            return
        }

        val address =
            runCatching {
                InetAddress.getByName(target.address)
            }.getOrNull() ?: return

        val frameId = nextFrameId++

        if (nextFrameId == Int.MAX_VALUE) {
            nextFrameId = 1
        }

        for (chunkIndex in 0 until chunkCount) {
            val start =
                chunkIndex * MAX_PACKET_PAYLOAD

            val end =
                minOf(
                    bytes.size,
                    start + MAX_PACKET_PAYLOAD,
                )

            val payloadSize = end - start

            val packetBytes =
                ByteArray(
                    HEADER_SIZE + payloadSize
                )

            val header =
                ByteBuffer.wrap(packetBytes)

            header.putInt(MAGIC)
            header.putInt(frameId)
            header.putShort(chunkIndex.toShort())
            header.putShort(chunkCount.toShort())

            System.arraycopy(
                bytes,
                start,
                packetBytes,
                HEADER_SIZE,
                payloadSize,
            )

            runCatching {
                senderSocket.send(
                    DatagramPacket(
                        packetBytes,
                        packetBytes.size,
                        address,
                        target.port,
                    )
                )
            }
        }
    }
}

object WudroidLanVideoClient {
    private const val MAGIC = 0x5756314A
    private const val HEADER_SIZE = 12
    private const val MAX_FRAME_BYTES = 900_000
    private const val MAX_CHUNKS = 512

    private data class Assembly(
        val chunks: Array<ByteArray?>,
        var received: Int = 0,
        var bytes: Int = 0,
    )

    private val _frameFlow =
        MutableStateFlow<Bitmap?>(null)

    val frameFlow: StateFlow<Bitmap?> =
        _frameFlow.asStateFlow()

    private val receiverRunning =
        AtomicBoolean(false)

    @Volatile
    private var receiverThread: Thread? = null

    fun start(socket: DatagramSocket) {
        stop(clearFrame = true)

        receiverRunning.set(true)

        receiverThread =
            Thread({
                val assemblies =
                    LinkedHashMap<Int, Assembly>()

                val packetBuffer =
                    ByteArray(1400)

                while (
                    receiverRunning.get() &&
                    !socket.isClosed
                ) {
                    try {
                        val packet =
                            DatagramPacket(
                                packetBuffer,
                                packetBuffer.size,
                            )

                        socket.receive(packet)

                        if (packet.length <= HEADER_SIZE) {
                            continue
                        }

                        val header =
                            ByteBuffer.wrap(
                                packet.data,
                                packet.offset,
                                packet.length,
                            )

                        val magic = header.int

                        if (magic != MAGIC) {
                            continue
                        }

                        val frameId = header.int

                        val chunkIndex =
                            header.short.toInt() and 0xFFFF

                        val chunkCount =
                            header.short.toInt() and 0xFFFF

                        if (
                            chunkCount !in 1..MAX_CHUNKS ||
                            chunkIndex !in 0 until chunkCount
                        ) {
                            continue
                        }

                        val payloadSize =
                            packet.length - HEADER_SIZE

                        if (payloadSize <= 0) {
                            continue
                        }

                        val assembly =
                            assemblies.getOrPut(frameId) {
                                Assembly(
                                    arrayOfNulls(chunkCount)
                                )
                            }

                        if (
                            assembly.chunks.size != chunkCount
                        ) {
                            assemblies.remove(frameId)
                            continue
                        }

                        if (
                            assembly.chunks[chunkIndex] == null
                        ) {
                            val data =
                                ByteArray(payloadSize)

                            System.arraycopy(
                                packet.data,
                                packet.offset + HEADER_SIZE,
                                data,
                                0,
                                payloadSize,
                            )

                            assembly.chunks[chunkIndex] = data
                            assembly.received += 1
                            assembly.bytes += payloadSize
                        }

                        if (
                            assembly.bytes > MAX_FRAME_BYTES
                        ) {
                            assemblies.remove(frameId)
                            continue
                        }

                        if (
                            assembly.received == chunkCount
                        ) {
                            val frameData =
                                ByteArray(assembly.bytes)

                            var position = 0

                            for (chunk in assembly.chunks) {
                                if (chunk == null) {
                                    position = -1
                                    break
                                }

                                System.arraycopy(
                                    chunk,
                                    0,
                                    frameData,
                                    position,
                                    chunk.size,
                                )

                                position += chunk.size
                            }

                            assemblies.remove(frameId)

                            if (
                                position == frameData.size
                            ) {
                                val bitmap =
                                    BitmapFactory
                                        .decodeByteArray(
                                            frameData,
                                            0,
                                            frameData.size,
                                        )

                                if (bitmap != null) {
                                    _frameFlow.value =
                                        bitmap
                                }
                            }
                        }

                        while (assemblies.size > 3) {
                            val firstKey =
                                assemblies.keys
                                    .firstOrNull()
                                    ?: break

                            assemblies.remove(firstKey)
                        }
                    } catch (_: Throwable) {
                        if (
                            !receiverRunning.get() ||
                            socket.isClosed
                        ) {
                            break
                        }
                    }
                }
            }, "Wudroid-LAN-Video-Client").apply {
                isDaemon = true
                start()
            }
    }

    fun stop(clearFrame: Boolean = true) {
        receiverRunning.set(false)
        receiverThread = null

        if (clearFrame) {
            _frameFlow.value = null
        }
    }
}
