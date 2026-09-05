package info.cemu.cemu

import android.content.Context
import android.net.ConnectivityManager
import java.io.BufferedInputStream
import java.io.BufferedOutputStream
import java.io.ByteArrayOutputStream
import java.net.Inet4Address
import java.net.InetAddress
import java.net.NetworkInterface
import java.net.ServerSocket
import java.net.Socket
import java.nio.charset.StandardCharsets
import java.util.ArrayDeque
import java.util.concurrent.atomic.AtomicBoolean

/**
 * WUDROID_TV_CAST_STREAM1
 *
 * Tiny live-HLS server fed directly by the existing Wudroid H.264 encoder.
 * The Google Cast Default Media Receiver fetches this URL from the phone,
 * therefore no Wudroid APK or receiver app is required on the TV.
 */
object WudroidCastHlsServer {
    private const val MAX_SEGMENTS = 8
    private const val TARGET_DURATION_SECONDS = 1
    private const val PMT_PID = 0x0100
    private const val VIDEO_PID = 0x0101

    private data class Segment(
        val sequence: Long,
        val durationSeconds: Double,
        val bytes: ByteArray,
    )

    private val running = AtomicBoolean(false)
    private val lock = Any()

    @Volatile
    private var serverSocket: ServerSocket? = null

    @Volatile
    private var serverThread: Thread? = null

    @Volatile
    private var port: Int = 0

    private val segments = ArrayDeque<Segment>()
    private var currentSegment: ByteArrayOutputStream? = null
    private var currentStartPtsUs: Long = -1L
    private var currentLastPtsUs: Long = -1L
    private var nextSequence = 1L
    private var codecConfig: ByteArray? = null

    private var patContinuity = 0
    private var pmtContinuity = 0
    private var videoContinuity = 0

    fun start(context: Context): Boolean {
        if (running.get()) return true

        synchronized(lock) {
            if (running.get()) return true
            return try {
                val socket = ServerSocket(0)
                socket.reuseAddress = true
                serverSocket = socket
                port = socket.localPort
                segments.clear()
                currentSegment = null
                currentStartPtsUs = -1L
                currentLastPtsUs = -1L
                nextSequence = 1L
                codecConfig = null
                running.set(true)

                serverThread = Thread({ acceptLoop() }, "Wudroid-HLS-HTTP").apply {
                    isDaemon = true
                    start()
                }
                true
            } catch (_: Throwable) {
                running.set(false)
                false
            }
        }
    }

    fun stop() {
        synchronized(lock) {
            running.set(false)
            runCatching { serverSocket?.close() }
            serverSocket = null
            serverThread = null
            port = 0
            segments.clear()
            currentSegment = null
            currentStartPtsUs = -1L
            currentLastPtsUs = -1L
            codecConfig = null
        }
    }

    fun isRunning(): Boolean = running.get()

    fun isReady(): Boolean = synchronized(lock) { segments.isNotEmpty() }

    fun playlistUrl(context: Context): String? {
        if (!running.get() || port <= 0) return null
        val address = localIpv4(context) ?: return null
        return "http://$address:$port/wudroid/live.m3u8"
    }

    /** Called by WudroidLanVideoHost for every MediaCodec output access unit. */
    fun onAccessUnit(bytes: ByteArray, flags: Int, ptsUs: Long) {
        if (!running.get() || bytes.isEmpty()) return

        val isConfig = (flags and android.media.MediaCodec.BUFFER_FLAG_CODEC_CONFIG) != 0
        val isKey = (flags and android.media.MediaCodec.BUFFER_FLAG_KEY_FRAME) != 0
        val annexB = toAnnexB(bytes)
        if (annexB.isEmpty()) return

        synchronized(lock) {
            if (!running.get()) return

            if (isConfig) {
                codecConfig = annexB
                return
            }

            if (isKey) {
                // Every HLS segment begins on an IDR frame. Finalize the previous
                // one when the next keyframe arrives (encoder requests one ~1/s).
                finalizeCurrentSegmentLocked(ptsUs)
                currentSegment = ByteArrayOutputStream(256 * 1024).also { out ->
                    out.write(buildPatPacket())
                    out.write(buildPmtPacket())
                }
                currentStartPtsUs = ptsUs
                currentLastPtsUs = ptsUs

                val config = codecConfig
                if (config != null && config.isNotEmpty()) {
                    writeVideoPesLocked(config, ptsUs, false)
                }
                writeVideoPesLocked(annexB, ptsUs, true)
                return
            }

            if (currentSegment == null) {
                // Wait for the first IDR so the receiver can start cleanly.
                return
            }

            currentLastPtsUs = ptsUs
            writeVideoPesLocked(annexB, ptsUs, false)
        }
    }

    private fun finalizeCurrentSegmentLocked(nextKeyPtsUs: Long) {
        val out = currentSegment ?: return
        val start = currentStartPtsUs
        if (start < 0L || out.size() <= 376) {
            currentSegment = null
            return
        }

        val endPts = if (nextKeyPtsUs > start) nextKeyPtsUs else currentLastPtsUs
        val duration = ((endPts - start).coerceAtLeast(100_000L) / 1_000_000.0)
            .coerceIn(0.10, 3.0)

        segments.addLast(
            Segment(
                sequence = nextSequence++,
                durationSeconds = duration,
                bytes = out.toByteArray(),
            )
        )
        while (segments.size > MAX_SEGMENTS) {
            segments.removeFirst()
        }
        currentSegment = null
    }

    private fun acceptLoop() {
        while (running.get()) {
            val client = try {
                serverSocket?.accept()
            } catch (_: Throwable) {
                null
            } ?: break

            Thread({ handleClient(client) }, "Wudroid-HLS-Client").apply {
                isDaemon = true
                start()
            }
        }
    }

    private fun handleClient(socket: Socket) {
        socket.use { client ->
            runCatching {
                client.soTimeout = 2500
                val input = BufferedInputStream(client.getInputStream())
                val requestLine = readAsciiLine(input) ?: return
                val parts = requestLine.split(' ')
                val method = parts.getOrNull(0) ?: "GET"
                val path = parts.getOrNull(1)?.substringBefore('?') ?: "/"

                // Consume request headers.
                while (true) {
                    val line = readAsciiLine(input) ?: break
                    if (line.isEmpty()) break
                }

                when {
                    path == "/wudroid/live.m3u8" -> {
                        val body = playlistText().toByteArray(StandardCharsets.UTF_8)
                        sendResponse(
                            client,
                            200,
                            "OK",
                            "application/vnd.apple.mpegurl",
                            body,
                            method != "HEAD",
                        )
                    }
                    path.startsWith("/wudroid/seg") && path.endsWith(".ts") -> {
                        val seq = path.removePrefix("/wudroid/seg").removeSuffix(".ts").toLongOrNull()
                        val body = synchronized(lock) {
                            segments.firstOrNull { it.sequence == seq }?.bytes
                        }
                        if (body == null) {
                            sendResponse(client, 404, "Not Found", "text/plain", "gone".toByteArray(), method != "HEAD")
                        } else {
                            sendResponse(client, 200, "OK", "video/mp2t", body, method != "HEAD")
                        }
                    }
                    else -> {
                        sendResponse(client, 404, "Not Found", "text/plain", "Wudroid Cast".toByteArray(), method != "HEAD")
                    }
                }
            }
        }
    }

    private fun playlistText(): String = synchronized(lock) {
        val snapshot = segments.toList()
        val firstSeq = snapshot.firstOrNull()?.sequence ?: nextSequence
        buildString {
            append("#EXTM3U\n")
            append("#EXT-X-VERSION:3\n")
            append("#EXT-X-TARGETDURATION:$TARGET_DURATION_SECONDS\n")
            append("#EXT-X-MEDIA-SEQUENCE:$firstSeq\n")
            append("#EXT-X-INDEPENDENT-SEGMENTS\n")
            for (segment in snapshot) {
                append("#EXTINF:")
                append(String.format(java.util.Locale.US, "%.3f", segment.durationSeconds))
                append(",\n")
                append("seg${segment.sequence}.ts\n")
            }
        }
    }

    private fun sendResponse(
        socket: Socket,
        code: Int,
        reason: String,
        contentType: String,
        body: ByteArray,
        includeBody: Boolean,
    ) {
        val out = BufferedOutputStream(socket.getOutputStream())
        val headers = buildString {
            append("HTTP/1.1 $code $reason\r\n")
            append("Content-Type: $contentType\r\n")
            append("Content-Length: ${body.size}\r\n")
            append("Cache-Control: no-store, no-cache, must-revalidate\r\n")
            append("Access-Control-Allow-Origin: *\r\n")
            append("Connection: close\r\n\r\n")
        }.toByteArray(StandardCharsets.US_ASCII)
        out.write(headers)
        if (includeBody) out.write(body)
        out.flush()
    }

    private fun readAsciiLine(input: BufferedInputStream): String? {
        val out = ByteArrayOutputStream(128)
        var previous = -1
        while (out.size() < 8192) {
            val current = input.read()
            if (current < 0) {
                if (out.size() == 0) return null
                break
            }
            if (previous == '\r'.code && current == '\n'.code) {
                val bytes = out.toByteArray()
                return String(bytes, 0, (bytes.size - 1).coerceAtLeast(0), StandardCharsets.US_ASCII)
            }
            out.write(current)
            previous = current
        }
        return out.toString(StandardCharsets.US_ASCII.name())
    }

    private fun localIpv4(context: Context): String? {
        // Prefer the currently active Android network (normally the Wi-Fi that
        // contains the Google TV), then fall back to interface enumeration.
        runCatching {
            val cm = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
            val active = cm.activeNetwork
            val props = active?.let { cm.getLinkProperties(it) }
            val addr = props?.linkAddresses
                ?.map { it.address }
                ?.firstOrNull { it is Inet4Address && !it.isLoopbackAddress }
            if (addr != null) return addr.hostAddress
        }

        return runCatching {
            val interfaces = NetworkInterface.getNetworkInterfaces()
            while (interfaces.hasMoreElements()) {
                val iface = interfaces.nextElement()
                if (!iface.isUp || iface.isLoopback) continue
                val addresses = iface.inetAddresses
                while (addresses.hasMoreElements()) {
                    val address = addresses.nextElement()
                    if (address is Inet4Address && !address.isLoopbackAddress) {
                        val host = address.hostAddress
                        if (!host.isNullOrBlank()) return host
                    }
                }
            }
            null
        }.getOrNull()
    }

    // ---------------------------------------------------------------------
    // MPEG-TS muxing (H.264 only). Small, self-contained, no extra codec lib.
    // ---------------------------------------------------------------------

    private fun writeVideoPesLocked(accessUnit: ByteArray, ptsUs: Long, keyFrame: Boolean) {
        val out = currentSegment ?: return
        val pts90 = ((ptsUs * 90L) / 1000L) and 0x1FFFFFFFFL

        val pes = ByteArrayOutputStream(accessUnit.size + 32)
        pes.write(byteArrayOf(0x00, 0x00, 0x01, 0xE0.toByte()))
        // Video PES can legally use packet_length=0 for unbounded payload.
        pes.write(byteArrayOf(0x00, 0x00))
        pes.write(0x80)
        pes.write(0x80)
        pes.write(0x05)
        pes.write(encodePts(pts90))
        pes.write(accessUnit)

        val bytes = pes.toByteArray()
        var offset = 0
        var first = true
        while (offset < bytes.size) {
            val withPcr = first
            val maxPayload = if (withPcr) 176 else 184
            val count = minOf(maxPayload, bytes.size - offset)
            val packet = buildTsPacket(
                pid = VIDEO_PID,
                payloadUnitStart = first,
                payload = bytes,
                offset = offset,
                count = count,
                pcr90 = if (withPcr) pts90 else null,
                randomAccess = first && keyFrame,
            )
            out.write(packet)
            offset += count
            first = false
        }
    }

    private fun buildPatPacket(): ByteArray {
        val section = ByteArrayOutputStream(32)
        section.write(0x00) // table id
        section.write(0xB0)
        section.write(0x0D) // section length 13
        section.write(0x00)
        section.write(0x01) // transport stream id
        section.write(0xC1) // version 0, current_next=1
        section.write(0x00)
        section.write(0x00)
        section.write(0x00)
        section.write(0x01) // program 1
        section.write(0xE0 or ((PMT_PID shr 8) and 0x1F))
        section.write(PMT_PID and 0xFF)
        val raw = section.toByteArray()
        val crc = mpegCrc32(raw)
        val full = ByteArrayOutputStream(raw.size + 4)
        full.write(raw)
        writeInt32(full, crc)
        return buildPsiPacket(0x0000, full.toByteArray(), true)
    }

    private fun buildPmtPacket(): ByteArray {
        val section = ByteArrayOutputStream(40)
        section.write(0x02)
        section.write(0xB0)
        section.write(0x12) // one H.264 stream => section length 18
        section.write(0x00)
        section.write(0x01) // program number
        section.write(0xC1)
        section.write(0x00)
        section.write(0x00)
        section.write(0xE0 or ((VIDEO_PID shr 8) and 0x1F))
        section.write(VIDEO_PID and 0xFF) // PCR PID
        section.write(0xF0)
        section.write(0x00) // program info length
        section.write(0x1B) // H.264/AVC
        section.write(0xE0 or ((VIDEO_PID shr 8) and 0x1F))
        section.write(VIDEO_PID and 0xFF)
        section.write(0xF0)
        section.write(0x00) // ES info length
        val raw = section.toByteArray()
        val crc = mpegCrc32(raw)
        val full = ByteArrayOutputStream(raw.size + 4)
        full.write(raw)
        writeInt32(full, crc)
        return buildPsiPacket(PMT_PID, full.toByteArray(), false)
    }

    private fun buildPsiPacket(pid: Int, section: ByteArray, pat: Boolean): ByteArray {
        val packet = ByteArray(188) { 0xFF.toByte() }
        packet[0] = 0x47
        packet[1] = (0x40 or ((pid shr 8) and 0x1F)).toByte()
        packet[2] = (pid and 0xFF).toByte()
        val cc = if (pat) {
            val v = patContinuity and 0x0F
            patContinuity = (patContinuity + 1) and 0x0F
            v
        } else {
            val v = pmtContinuity and 0x0F
            pmtContinuity = (pmtContinuity + 1) and 0x0F
            v
        }
        packet[3] = (0x10 or cc).toByte()
        packet[4] = 0x00 // pointer field
        System.arraycopy(section, 0, packet, 5, minOf(section.size, 183))
        return packet
    }

    private fun buildTsPacket(
        pid: Int,
        payloadUnitStart: Boolean,
        payload: ByteArray,
        offset: Int,
        count: Int,
        pcr90: Long?,
        randomAccess: Boolean,
    ): ByteArray {
        val packet = ByteArray(188) { 0xFF.toByte() }
        packet[0] = 0x47
        packet[1] = (((if (payloadUnitStart) 0x40 else 0x00)) or ((pid shr 8) and 0x1F)).toByte()
        packet[2] = (pid and 0xFF).toByte()

        val cc = videoContinuity and 0x0F
        videoContinuity = (videoContinuity + 1) and 0x0F

        val needPcr = pcr90 != null
        val needsStuffing = count < 184
        if (needPcr || needsStuffing) {
            packet[3] = (0x30 or cc).toByte()
            val adaptationLength = (183 - count).coerceAtLeast(if (needPcr) 7 else 0)
            packet[4] = adaptationLength.toByte()
            var pos = 5
            if (adaptationLength > 0) {
                var flags = 0
                if (randomAccess) flags = flags or 0x40
                if (needPcr) flags = flags or 0x10
                packet[pos++] = flags.toByte()
                if (needPcr) {
                    writePcr(packet, pos, pcr90!!)
                    pos += 6
                }
                val adaptationEnd = 5 + adaptationLength
                while (pos < adaptationEnd) packet[pos++] = 0xFF.toByte()
            }
            val payloadStart = 5 + adaptationLength
            System.arraycopy(payload, offset, packet, payloadStart, count)
        } else {
            packet[3] = (0x10 or cc).toByte()
            System.arraycopy(payload, offset, packet, 4, count)
        }
        return packet
    }

    private fun writePcr(packet: ByteArray, offset: Int, pts90: Long) {
        val base = pts90 and 0x1FFFFFFFFL
        val ext = 0
        packet[offset] = ((base shr 25) and 0xFF).toByte()
        packet[offset + 1] = ((base shr 17) and 0xFF).toByte()
        packet[offset + 2] = ((base shr 9) and 0xFF).toByte()
        packet[offset + 3] = ((base shr 1) and 0xFF).toByte()
        packet[offset + 4] = ((((base and 1L) shl 7) or 0x7E or ((ext shr 8) and 1).toLong()) and 0xFF).toByte()
        packet[offset + 5] = (ext and 0xFF).toByte()
    }

    private fun encodePts(pts: Long): ByteArray {
        val p = pts and 0x1FFFFFFFFL
        return byteArrayOf(
            (0x20 or (((p shr 30) and 0x07).toInt() shl 1) or 0x01).toByte(),
            ((p shr 22) and 0xFF).toByte(),
            ((((p shr 15) and 0x7F).toInt() shl 1) or 0x01).toByte(),
            ((p shr 7) and 0xFF).toByte(),
            ((((p and 0x7F).toInt()) shl 1) or 0x01).toByte(),
        )
    }

    private fun toAnnexB(input: ByteArray): ByteArray {
        if (input.size >= 4 && input[0] == 0.toByte() && input[1] == 0.toByte() &&
            ((input[2] == 1.toByte()) || (input[2] == 0.toByte() && input[3] == 1.toByte()))) {
            return input
        }

        // Android AVC encoders may expose AVCC length-prefixed NAL units.
        val out = ByteArrayOutputStream(input.size + 32)
        var pos = 0
        var converted = false
        while (pos + 4 <= input.size) {
            val len = ((input[pos].toInt() and 0xFF) shl 24) or
                ((input[pos + 1].toInt() and 0xFF) shl 16) or
                ((input[pos + 2].toInt() and 0xFF) shl 8) or
                (input[pos + 3].toInt() and 0xFF)
            if (len <= 0 || pos + 4 + len > input.size) break
            out.write(byteArrayOf(0, 0, 0, 1))
            out.write(input, pos + 4, len)
            pos += 4 + len
            converted = true
        }
        if (converted && pos == input.size) return out.toByteArray()

        // Last-resort: a single NAL unit.
        return ByteArray(input.size + 4).also { result ->
            result[0] = 0
            result[1] = 0
            result[2] = 0
            result[3] = 1
            System.arraycopy(input, 0, result, 4, input.size)
        }
    }

    private fun mpegCrc32(data: ByteArray): Int {
        var crc = -1
        for (byte in data) {
            crc = crc xor ((byte.toInt() and 0xFF) shl 24)
            repeat(8) {
                crc = if ((crc and 0x80000000.toInt()) != 0) {
                    (crc shl 1) xor 0x04C11DB7
                } else {
                    crc shl 1
                }
            }
        }
        return crc
    }

    private fun writeInt32(out: ByteArrayOutputStream, value: Int) {
        out.write((value ushr 24) and 0xFF)
        out.write((value ushr 16) and 0xFF)
        out.write((value ushr 8) and 0xFF)
        out.write(value and 0xFF)
    }
}
