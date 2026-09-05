package info.cemu.cemu

import android.os.Build
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.Inet4Address
import java.net.InetAddress
import java.net.NetworkInterface
import java.util.UUID
import java.util.concurrent.atomic.AtomicReference

/**
 * WUDROID_TV_DIRECT_LINK1
 *
 * Direct-TV transport built on the same low-latency H.264/UDP path used by
 * Wudroid LAN multiplayer. The phone is still the emulator/encoder; a Wudroid
 * receiver running on the TV advertises itself and receives only the video.
 */
data class WudroidTvReceiverDevice(
    val name: String,
    val address: String,
    val videoPort: Int,
)

object WudroidTvDirectHost {
    const val DISCOVERY_PORT = 58340
    const val VIDEO_PORT = 58341

    private const val DISCOVER = "WUDROID_TV_DISCOVER_V1"
    private const val HERE = "WUDROID_TV_HERE_V1"

    private val currentTarget = AtomicReference<WudroidVideoTarget?>(null)
    private val currentName = AtomicReference<String?>(null)

    fun connect(device: WudroidTvReceiverDevice) {
        currentTarget.set(WudroidVideoTarget(device.address, device.videoPort))
        currentName.set(device.name)
    }

    fun disconnect() {
        currentTarget.set(null)
        currentName.set(null)
    }

    fun isConnected(): Boolean = currentTarget.get() != null
    fun connectedName(): String? = currentName.get()
    fun videoTarget(): WudroidVideoTarget? = currentTarget.get()

    fun scanReceivers(timeoutMs: Int = 1200): List<WudroidTvReceiverDevice> {
        val nonce = UUID.randomUUID().toString().replace("-", "").take(12)
        val request = "$DISCOVER|$nonce".toByteArray(Charsets.UTF_8)
        val found = LinkedHashMap<String, WudroidTvReceiverDevice>()
        val deadline = System.currentTimeMillis() + timeoutMs.coerceIn(500, 4000)

        DatagramSocket().use { socket ->
            socket.broadcast = true
            socket.soTimeout = 120

            val destinations = LinkedHashSet<InetAddress>()
            runCatching { destinations += InetAddress.getByName("255.255.255.255") }

            runCatching {
                val interfaces = NetworkInterface.getNetworkInterfaces()
                while (interfaces.hasMoreElements()) {
                    val iface = interfaces.nextElement()
                    if (!iface.isUp || iface.isLoopback) continue
                    iface.interfaceAddresses.forEach { ia ->
                        val broadcast = ia.broadcast
                        if (broadcast is Inet4Address) destinations += broadcast
                    }
                }
            }

            destinations.forEach { address ->
                runCatching {
                    socket.send(DatagramPacket(request, request.size, address, DISCOVERY_PORT))
                }
            }

            val buffer = ByteArray(1000)
            while (System.currentTimeMillis() < deadline) {
                try {
                    val packet = DatagramPacket(buffer, buffer.size)
                    socket.receive(packet)
                    val text = String(packet.data, packet.offset, packet.length, Charsets.UTF_8)
                    val parts = text.split("|", limit = 5)
                    if (parts.size < 4 || parts[0] != HERE || parts[1] != nonce) continue

                    val name = parts[2].trim().ifBlank { "Wudroid TV" }.take(48)
                    val port = parts[3].toIntOrNull()?.takeIf { it in 1..65535 } ?: continue
                    val address = packet.address.hostAddress ?: continue
                    found["$address:$port"] = WudroidTvReceiverDevice(name, address, port)
                } catch (_: Throwable) {
                }
            }
        }

        return found.values.toList()
    }

    internal fun discoveryRequestPrefix(): String = DISCOVER
    internal fun discoveryReplyPrefix(): String = HERE
    internal fun receiverName(): String =
        listOfNotNull(Build.MANUFACTURER, Build.MODEL)
            .joinToString(" ")
            .trim()
            .ifBlank { "Wudroid TV" }
}
