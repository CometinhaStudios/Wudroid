package info.cemu.cemu

import android.graphics.Bitmap
import android.media.Image
import android.media.MediaCodec
import android.media.MediaCodecInfo
import android.media.MediaCodecList
import android.media.MediaFormat
import android.os.Build
import android.os.Handler
import android.os.HandlerThread
import android.view.PixelCopy
import android.view.Surface
import android.view.SurfaceView
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
    private const val MIME = "video/avc"
    private const val MAGIC = 0x57564839
    private const val HEADER_SIZE = 28
    private const val MAX_PACKET_PAYLOAD = 1150
    private const val MAX_ACCESS_UNIT_BYTES = 2_500_000

    private const val VIDEO_WIDTH = 1280
    private const val VIDEO_HEIGHT = 720
    private const val VIDEO_FPS = 30
    private const val VIDEO_BITRATE = 4_000_000
    private const val I_FRAME_INTERVAL_SECONDS = 1
    private const val FRAME_INTERVAL_MS = 34L

    private val active = AtomicBoolean(false)

    private val captureThread =
        HandlerThread("Wudroid-H264-Capture").apply {
            start()
        }

    private val handler = Handler(captureThread.looper)

    @Volatile
    private var surfaceRef: WeakReference<SurfaceView>? = null

    @Volatile
    private var captureBitmap: Bitmap? = null

    private var argbPixels =
        IntArray(VIDEO_WIDTH * VIDEO_HEIGHT)

    private var encoder: MediaCodec? = null
    private var encoderBufferInfo = MediaCodec.BufferInfo()
    private var cachedCodecConfig: ByteArray? = null
    private var nextUnitId = 1

    private val senderSocket by lazy {
        DatagramSocket().apply {
            broadcast = false
            sendBufferSize = 2 * 1024 * 1024
        }
    }

    fun attachSurfaceView(surfaceView: SurfaceView) {
        surfaceRef = WeakReference(surfaceView)

        if (active.compareAndSet(false, true)) {
            handler.post(::captureNext)
        }
    }

    fun detachSurfaceView(surfaceView: SurfaceView) {
        if (surfaceRef?.get() === surfaceView) {
            surfaceRef = null
            active.set(false)

            handler.post {
                releaseEncoder()

                captureBitmap?.let {
                    if (!it.isRecycled) {
                        it.recycle()
                    }
                }

                captureBitmap = null
            }
        }
    }

    private fun captureBitmap(): Bitmap {
        val old = captureBitmap

        if (
            old != null &&
            !old.isRecycled &&
            old.width == VIDEO_WIDTH &&
            old.height == VIDEO_HEIGHT
        ) {
            return old
        }

        old?.let {
            if (!it.isRecycled) {
                it.recycle()
            }
        }

        return Bitmap.createBitmap(
            VIDEO_WIDTH,
            VIDEO_HEIGHT,
            Bitmap.Config.ARGB_8888,
        ).also {
            captureBitmap = it
        }
    }

    private fun captureNext() {
        if (!active.get()) return

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
            handler.postDelayed(::captureNext, 160L)
            return
        }

        if (!ensureEncoder()) {
            handler.postDelayed(::captureNext, 300L)
            return
        }

        val bitmap = captureBitmap()

        try {
            PixelCopy.request(
                surfaceView,
                bitmap,
                { result ->
                    if (
                        result == PixelCopy.SUCCESS &&
                        active.get()
                    ) {
                        encodeBitmap(bitmap, target)
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

    private fun preferredEncoder(): MediaCodec {
        if (Build.VERSION.SDK_INT >= 29) {
            val info =
                runCatching {
                    MediaCodecList(
                        MediaCodecList.REGULAR_CODECS
                    ).codecInfos.firstOrNull { codecInfo ->
                        codecInfo.isEncoder &&
                            codecInfo.isHardwareAccelerated &&
                            codecInfo.supportedTypes.any {
                                it.equals(MIME, ignoreCase = true)
                            } &&
                            runCatching {
                                codecInfo
                                    .getCapabilitiesForType(MIME)
                                    .colorFormats
                                    .contains(
                                        MediaCodecInfo
                                            .CodecCapabilities
                                            .COLOR_FormatYUV420Flexible
                                    )
                            }.getOrDefault(false)
                    }
                }.getOrNull()

            if (info != null) {
                return MediaCodec.createByCodecName(
                    info.name
                )
            }
        }

        return MediaCodec.createEncoderByType(MIME)
    }

    private fun ensureEncoder(): Boolean {
        if (encoder != null) return true

        return try {
            val format =
                MediaFormat.createVideoFormat(
                    MIME,
                    VIDEO_WIDTH,
                    VIDEO_HEIGHT,
                ).apply {
                    setInteger(
                        MediaFormat.KEY_COLOR_FORMAT,
                        MediaCodecInfo.CodecCapabilities
                            .COLOR_FormatYUV420Flexible,
                    )
                    setInteger(
                        MediaFormat.KEY_BIT_RATE,
                        VIDEO_BITRATE,
                    )
                    setInteger(
                        MediaFormat.KEY_FRAME_RATE,
                        VIDEO_FPS,
                    )
                    setInteger(
                        MediaFormat.KEY_I_FRAME_INTERVAL,
                        I_FRAME_INTERVAL_SECONDS,
                    )
                }

            val codec = preferredEncoder()

            codec.configure(
                format,
                null,
                null,
                MediaCodec.CONFIGURE_FLAG_ENCODE,
            )

            codec.start()

            encoder = codec
            encoderBufferInfo = MediaCodec.BufferInfo()
            cachedCodecConfig = null
            true
        } catch (_: Throwable) {
            releaseEncoder()
            false
        }
    }

    private fun releaseEncoder() {
        val codec = encoder
        encoder = null
        cachedCodecConfig = null

        if (codec != null) {
            runCatching { codec.stop() }
            runCatching { codec.release() }
        }
    }

    private fun encodeBitmap(
        bitmap: Bitmap,
        target: WudroidVideoTarget,
    ) {
        val codec = encoder ?: return

        try {
            drainEncoder(codec, target)

            val inputIndex =
                codec.dequeueInputBuffer(2_000L)

            if (inputIndex < 0) return

            val image =
                runCatching {
                    codec.getInputImage(inputIndex)
                }.getOrNull()

            val wrote =
                if (image != null) {
                    writeBitmapToImage(bitmap, image)
                    true
                } else {
                    val buffer =
                        codec.getInputBuffer(inputIndex)

                    buffer != null &&
                        writeBitmapAsI420(bitmap, buffer)
                }

            val pts = presentationTimeUs()

            if (!wrote) {
                codec.queueInputBuffer(
                    inputIndex,
                    0,
                    0,
                    pts,
                    0,
                )
                return
            }

            codec.queueInputBuffer(
                inputIndex,
                0,
                VIDEO_WIDTH * VIDEO_HEIGHT * 3 / 2,
                pts,
                0,
            )

            drainEncoder(codec, target)
        } catch (_: Throwable) {
            releaseEncoder()
        }
    }

    private fun presentationTimeUs(): Long =
        System.nanoTime() / 1_000L

    private fun drainEncoder(
        codec: MediaCodec,
        target: WudroidVideoTarget,
    ) {
        while (true) {
            val index =
                codec.dequeueOutputBuffer(
                    encoderBufferInfo,
                    0L,
                )

            when {
                index >= 0 -> {
                    val info = encoderBufferInfo

                    if (info.size > 0) {
                        val output =
                            codec.getOutputBuffer(index)

                        if (output != null) {
                            val bytes =
                                ByteArray(info.size)

                            output.position(info.offset)
                            output.limit(
                                info.offset + info.size
                            )
                            output.get(bytes)

                            val isConfig =
                                (
                                    info.flags and
                                        MediaCodec
                                            .BUFFER_FLAG_CODEC_CONFIG
                                ) != 0

                            val isKey =
                                (
                                    info.flags and
                                        MediaCodec
                                            .BUFFER_FLAG_KEY_FRAME
                                ) != 0

                            if (isConfig) {
                                cachedCodecConfig = bytes

                                sendAccessUnit(
                                    bytes,
                                    MediaCodec
                                        .BUFFER_FLAG_CODEC_CONFIG,
                                    info.presentationTimeUs,
                                    target,
                                )
                            } else {
                                if (isKey) {
                                    cachedCodecConfig?.let {
                                        sendAccessUnit(
                                            it,
                                            MediaCodec
                                                .BUFFER_FLAG_CODEC_CONFIG,
                                            info.presentationTimeUs,
                                            target,
                                        )
                                    }
                                }

                                sendAccessUnit(
                                    bytes,
                                    if (isKey)
                                        MediaCodec
                                            .BUFFER_FLAG_KEY_FRAME
                                    else
                                        0,
                                    info.presentationTimeUs,
                                    target,
                                )
                            }
                        }
                    }

                    codec.releaseOutputBuffer(
                        index,
                        false,
                    )
                }

                index ==
                    MediaCodec.INFO_OUTPUT_FORMAT_CHANGED -> {
                    cacheCodecConfigFromFormat(
                        codec.outputFormat
                    )
                }

                index ==
                    MediaCodec.INFO_TRY_AGAIN_LATER -> {
                    return
                }

                else -> return
            }
        }
    }

    private fun cacheCodecConfigFromFormat(
        format: MediaFormat,
    ) {
        val csd0 =
            copyByteBuffer(
                format.getByteBuffer("csd-0")
            )

        val csd1 =
            copyByteBuffer(
                format.getByteBuffer("csd-1")
            )

        val total =
            (csd0?.size ?: 0) +
                (csd1?.size ?: 0)

        if (total <= 0) return

        val combined = ByteArray(total)
        var position = 0

        csd0?.let {
            System.arraycopy(
                it,
                0,
                combined,
                position,
                it.size,
            )
            position += it.size
        }

        csd1?.let {
            System.arraycopy(
                it,
                0,
                combined,
                position,
                it.size,
            )
        }

        cachedCodecConfig = combined
    }

    private fun copyByteBuffer(
        source: ByteBuffer?,
    ): ByteArray? {
        if (source == null) return null

        val copy = source.duplicate()
        val bytes = ByteArray(copy.remaining())
        copy.get(bytes)
        return bytes
    }

    private fun sendAccessUnit(
        bytes: ByteArray,
        flags: Int,
        ptsUs: Long,
        target: WudroidVideoTarget,
    ) {
        if (
            bytes.isEmpty() ||
            bytes.size > MAX_ACCESS_UNIT_BYTES
        ) {
            return
        }

        val chunkCount =
            (bytes.size + MAX_PACKET_PAYLOAD - 1) /
                MAX_PACKET_PAYLOAD

        if (chunkCount !in 1..1024) return

        val address =
            runCatching {
                InetAddress.getByName(target.address)
            }.getOrNull() ?: return

        val unitId = nextUnitId++

        if (nextUnitId == Int.MAX_VALUE) {
            nextUnitId = 1
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
            header.putInt(unitId)
            header.putShort(chunkIndex.toShort())
            header.putShort(chunkCount.toShort())
            header.putInt(flags)
            header.putLong(ptsUs)
            header.putShort(VIDEO_WIDTH.toShort())
            header.putShort(VIDEO_HEIGHT.toShort())

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

    private fun ensureArgbPixels() {
        val needed =
            VIDEO_WIDTH * VIDEO_HEIGHT

        if (argbPixels.size != needed) {
            argbPixels = IntArray(needed)
        }
    }

    private fun writeBitmapToImage(
        bitmap: Bitmap,
        image: Image,
    ) {
        ensureArgbPixels()

        bitmap.getPixels(
            argbPixels,
            0,
            VIDEO_WIDTH,
            0,
            0,
            VIDEO_WIDTH,
            VIDEO_HEIGHT,
        )

        val planes = image.planes
        if (planes.size < 3) return

        val yPlane = planes[0]
        val uPlane = planes[1]
        val vPlane = planes[2]

        val yBuffer = yPlane.buffer
        val uBuffer = uPlane.buffer
        val vBuffer = vPlane.buffer

        val yBase = yBuffer.position()
        val uBase = uBuffer.position()
        val vBase = vBuffer.position()

        for (y in 0 until VIDEO_HEIGHT) {
            val yRow =
                yBase + y * yPlane.rowStride

            val sourceRow =
                y * VIDEO_WIDTH

            for (x in 0 until VIDEO_WIDTH) {
                val color =
                    argbPixels[sourceRow + x]

                val r = (color shr 16) and 0xFF
                val g = (color shr 8) and 0xFF
                val b = color and 0xFF

                val yy =
                    clampByte(
                        (
                            (
                                66 * r +
                                    129 * g +
                                    25 * b +
                                    128
                            ) shr 8
                        ) + 16
                    )

                val index =
                    yRow +
                        x * yPlane.pixelStride

                if (index < yBuffer.limit()) {
                    yBuffer.put(
                        index,
                        yy.toByte(),
                    )
                }
            }
        }

        for (y in 0 until VIDEO_HEIGHT step 2) {
            val uvY = y / 2

            val uRow =
                uBase +
                    uvY * uPlane.rowStride

            val vRow =
                vBase +
                    uvY * vPlane.rowStride

            for (x in 0 until VIDEO_WIDTH step 2) {
                var r = 0
                var g = 0
                var b = 0
                var count = 0

                for (dy in 0..1) {
                    val sy = y + dy
                    if (sy >= VIDEO_HEIGHT) continue

                    val sourceRow =
                        sy * VIDEO_WIDTH

                    for (dx in 0..1) {
                        val sx = x + dx
                        if (sx >= VIDEO_WIDTH) continue

                        val color =
                            argbPixels[
                                sourceRow + sx
                            ]

                        r += (color shr 16) and 0xFF
                        g += (color shr 8) and 0xFF
                        b += color and 0xFF
                        count += 1
                    }
                }

                if (count <= 0) continue

                r /= count
                g /= count
                b /= count

                val uu =
                    clampByte(
                        (
                            (
                                -38 * r -
                                    74 * g +
                                    112 * b +
                                    128
                            ) shr 8
                        ) + 128
                    )

                val vv =
                    clampByte(
                        (
                            (
                                112 * r -
                                    94 * g -
                                    18 * b +
                                    128
                            ) shr 8
                        ) + 128
                    )

                val uvX = x / 2

                val uIndex =
                    uRow +
                        uvX * uPlane.pixelStride

                val vIndex =
                    vRow +
                        uvX * vPlane.pixelStride

                if (uIndex < uBuffer.limit()) {
                    uBuffer.put(
                        uIndex,
                        uu.toByte(),
                    )
                }

                if (vIndex < vBuffer.limit()) {
                    vBuffer.put(
                        vIndex,
                        vv.toByte(),
                    )
                }
            }
        }
    }

    private fun writeBitmapAsI420(
        bitmap: Bitmap,
        buffer: ByteBuffer,
    ): Boolean {
        ensureArgbPixels()

        val required =
            VIDEO_WIDTH *
                VIDEO_HEIGHT *
                3 / 2

        if (buffer.capacity() < required) {
            return false
        }

        bitmap.getPixels(
            argbPixels,
            0,
            VIDEO_WIDTH,
            0,
            0,
            VIDEO_WIDTH,
            VIDEO_HEIGHT,
        )

        buffer.clear()

        for (color in argbPixels) {
            val r = (color shr 16) and 0xFF
            val g = (color shr 8) and 0xFF
            val b = color and 0xFF

            val yy =
                clampByte(
                    (
                        (
                            66 * r +
                                129 * g +
                                25 * b +
                                128
                        ) shr 8
                    ) + 16
                )

            buffer.put(yy.toByte())
        }

        for (y in 0 until VIDEO_HEIGHT step 2) {
            for (x in 0 until VIDEO_WIDTH step 2) {
                val color =
                    argbPixels[
                        y * VIDEO_WIDTH + x
                    ]

                val r = (color shr 16) and 0xFF
                val g = (color shr 8) and 0xFF
                val b = color and 0xFF

                val uu =
                    clampByte(
                        (
                            (
                                -38 * r -
                                    74 * g +
                                    112 * b +
                                    128
                            ) shr 8
                        ) + 128
                    )

                buffer.put(uu.toByte())
            }
        }

        for (y in 0 until VIDEO_HEIGHT step 2) {
            for (x in 0 until VIDEO_WIDTH step 2) {
                val color =
                    argbPixels[
                        y * VIDEO_WIDTH + x
                    ]

                val r = (color shr 16) and 0xFF
                val g = (color shr 8) and 0xFF
                val b = color and 0xFF

                val vv =
                    clampByte(
                        (
                            (
                                112 * r -
                                    94 * g -
                                    18 * b +
                                    128
                            ) shr 8
                        ) + 128
                    )

                buffer.put(vv.toByte())
            }
        }

        return true
    }

    private fun clampByte(value: Int): Int =
        value.coerceIn(0, 255)
}

object WudroidLanVideoClient {
    private const val MIME = "video/avc"
    private const val MAGIC = 0x57564839
    private const val HEADER_SIZE = 28
    private const val MAX_ACCESS_UNIT_BYTES = 2_500_000
    private const val MAX_CHUNKS = 1024

    private data class Assembly(
        val chunks: Array<ByteArray?>,
        val flags: Int,
        val ptsUs: Long,
        val width: Int,
        val height: Int,
        var received: Int = 0,
        var bytes: Int = 0,
    )

    private val receiverRunning =
        AtomicBoolean(false)

    @Volatile
    private var receiverThread: Thread? = null

    private val decoderLock = Any()

    private var outputSurface: Surface? = null
    private var decoder: MediaCodec? = null
    private var decoderWidth = 0
    private var decoderHeight = 0
    private var decoderConfigQueued = false

    private var cachedConfig: ByteArray? = null
    private var cachedWidth = 1280
    private var cachedHeight = 720

    private val decoderBufferInfo =
        MediaCodec.BufferInfo()

    private val _statusFlow =
        MutableStateFlow(
            "Aguardando H.264 do Host…"
        )

    val statusFlow: StateFlow<String> =
        _statusFlow.asStateFlow()

    fun start(socket: DatagramSocket) {
        stop(clearStatus = true)

        receiverRunning.set(true)

        receiverThread =
            Thread({
                receiveLoop(socket)
            }, "Wudroid-H264-Client").apply {
                isDaemon = true
                start()
            }
    }

    fun attachSurface(surface: Surface) {
        synchronized(decoderLock) {
            if (
                outputSurface === surface &&
                decoder != null
            ) {
                return
            }

            outputSurface = surface
            releaseDecoderLocked()

            ensureDecoderLocked(
                cachedWidth,
                cachedHeight,
            )

            _statusFlow.value =
                "Decoder H.264 pronto • aguardando vídeo"
        }
    }

    fun detachSurface() {
        synchronized(decoderLock) {
            outputSurface = null
            releaseDecoderLocked()
        }
    }

    fun stop(clearStatus: Boolean = true) {
        receiverRunning.set(false)
        receiverThread = null

        synchronized(decoderLock) {
            outputSurface = null
            releaseDecoderLocked()
            cachedConfig = null
            decoderConfigQueued = false
        }

        if (clearStatus) {
            _statusFlow.value =
                "Aguardando H.264 do Host…"
        }
    }

    private fun receiveLoop(socket: DatagramSocket) {
        val assemblies =
            LinkedHashMap<Int, Assembly>()

        val packetBuffer = ByteArray(1400)

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
                if (magic != MAGIC) continue

                val unitId = header.int

                val chunkIndex =
                    header.short.toInt() and
                        0xFFFF

                val chunkCount =
                    header.short.toInt() and
                        0xFFFF

                val flags = header.int
                val ptsUs = header.long

                val width =
                    header.short.toInt() and
                        0xFFFF

                val height =
                    header.short.toInt() and
                        0xFFFF

                if (
                    width !in 64..4096 ||
                    height !in 64..4096 ||
                    chunkCount !in 1..MAX_CHUNKS ||
                    chunkIndex !in 0 until chunkCount
                ) {
                    continue
                }

                val payloadSize =
                    packet.length - HEADER_SIZE

                if (payloadSize <= 0) continue

                val assembly =
                    assemblies.getOrPut(unitId) {
                        Assembly(
                            chunks =
                                arrayOfNulls(
                                    chunkCount
                                ),
                            flags = flags,
                            ptsUs = ptsUs,
                            width = width,
                            height = height,
                        )
                    }

                if (
                    assembly.chunks.size !=
                        chunkCount ||
                    assembly.flags != flags ||
                    assembly.width != width ||
                    assembly.height != height
                ) {
                    assemblies.remove(unitId)
                    continue
                }

                if (
                    assembly.chunks[
                        chunkIndex
                    ] == null
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

                    assembly.chunks[
                        chunkIndex
                    ] = data

                    assembly.received += 1
                    assembly.bytes += payloadSize
                }

                if (
                    assembly.bytes >
                        MAX_ACCESS_UNIT_BYTES
                ) {
                    assemblies.remove(unitId)
                    continue
                }

                if (
                    assembly.received ==
                        chunkCount
                ) {
                    val complete =
                        reassemble(assembly)

                    assemblies.remove(unitId)

                    if (complete != null) {
                        handleAccessUnit(
                            complete,
                            assembly.flags,
                            assembly.ptsUs,
                            assembly.width,
                            assembly.height,
                        )
                    }
                }

                while (assemblies.size > 4) {
                    val first =
                        assemblies.keys
                            .firstOrNull()
                            ?: break

                    assemblies.remove(first)
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
    }

    private fun reassemble(
        assembly: Assembly,
    ): ByteArray? {
        val bytes = ByteArray(assembly.bytes)
        var position = 0

        for (chunk in assembly.chunks) {
            if (chunk == null) return null

            System.arraycopy(
                chunk,
                0,
                bytes,
                position,
                chunk.size,
            )

            position += chunk.size
        }

        return bytes
    }

    private fun handleAccessUnit(
        bytes: ByteArray,
        flags: Int,
        ptsUs: Long,
        width: Int,
        height: Int,
    ) {
        val isConfig =
            (
                flags and
                    MediaCodec
                        .BUFFER_FLAG_CODEC_CONFIG
            ) != 0

        synchronized(decoderLock) {
            if (isConfig) {
                cachedConfig = bytes
                cachedWidth = width
                cachedHeight = height

                if (
                    outputSurface != null &&
                    ensureDecoderLocked(
                        width,
                        height,
                    )
                ) {
                    queueDecoderDataLocked(
                        bytes,
                        ptsUs,
                        true,
                    )
                    decoderConfigQueued = true
                }

                _statusFlow.value =
                    "H.264 configurado • ${width}×${height}"
                return
            }

            if (
                outputSurface == null ||
                !ensureDecoderLocked(
                    width,
                    height,
                )
            ) {
                return
            }

            if (!decoderConfigQueued) {
                val config = cachedConfig

                if (config == null) {
                    _statusFlow.value =
                        "Esperando SPS/PPS H.264…"
                    return
                }

                queueDecoderDataLocked(
                    config,
                    ptsUs,
                    true,
                )

                decoderConfigQueued = true
            }

            if (
                queueDecoderDataLocked(
                    bytes,
                    ptsUs,
                    false,
                )
            ) {
                _statusFlow.value =
                    "H.264 • ${width}×${height} • recebendo"
            }
        }
    }

    private fun ensureDecoderLocked(
        width: Int,
        height: Int,
    ): Boolean {
        val surface =
            outputSurface ?: return false

        if (
            decoder != null &&
            decoderWidth == width &&
            decoderHeight == height
        ) {
            return true
        }

        releaseDecoderLocked()

        return try {
            val format =
                MediaFormat.createVideoFormat(
                    MIME,
                    width,
                    height,
                )

            if (Build.VERSION.SDK_INT >= 30) {
                format.setInteger(
                    "low-latency",
                    1,
                )
            }

            val codec =
                MediaCodec
                    .createDecoderByType(MIME)

            codec.configure(
                format,
                surface,
                null,
                0,
            )

            codec.start()

            decoder = codec
            decoderWidth = width
            decoderHeight = height
            decoderConfigQueued = false

            true
        } catch (_: Throwable) {
            releaseDecoderLocked()

            _statusFlow.value =
                "Falha ao iniciar decoder H.264"

            false
        }
    }

    private fun releaseDecoderLocked() {
        val codec = decoder

        decoder = null
        decoderWidth = 0
        decoderHeight = 0
        decoderConfigQueued = false

        if (codec != null) {
            runCatching { codec.stop() }
            runCatching { codec.release() }
        }
    }

    private fun queueDecoderDataLocked(
        bytes: ByteArray,
        ptsUs: Long,
        isConfig: Boolean,
    ): Boolean {
        val codec = decoder ?: return false

        return try {
            drainDecoderLocked(codec)

            val index =
                codec.dequeueInputBuffer(2_000L)

            if (index < 0) return false

            val input =
                codec.getInputBuffer(index)

            if (input == null) {
                codec.queueInputBuffer(
                    index,
                    0,
                    0,
                    ptsUs,
                    0,
                )
                return false
            }

            if (
                input.capacity() <
                    bytes.size
            ) {
                codec.queueInputBuffer(
                    index,
                    0,
                    0,
                    ptsUs,
                    0,
                )
                return false
            }

            input.clear()
            input.put(bytes)

            codec.queueInputBuffer(
                index,
                0,
                bytes.size,
                ptsUs,
                if (isConfig)
                    MediaCodec
                        .BUFFER_FLAG_CODEC_CONFIG
                else
                    0,
            )

            drainDecoderLocked(codec)
            true
        } catch (_: Throwable) {
            releaseDecoderLocked()
            false
        }
    }

    private fun drainDecoderLocked(
        codec: MediaCodec,
    ) {
        while (true) {
            val index =
                codec.dequeueOutputBuffer(
                    decoderBufferInfo,
                    0L,
                )

            when {
                index >= 0 -> {
                    codec.releaseOutputBuffer(
                        index,
                        true,
                    )
                }

                index ==
                    MediaCodec.INFO_TRY_AGAIN_LATER -> {
                    return
                }

                index ==
                    MediaCodec.INFO_OUTPUT_FORMAT_CHANGED -> {
                }

                else -> return
            }
        }
    }
}
