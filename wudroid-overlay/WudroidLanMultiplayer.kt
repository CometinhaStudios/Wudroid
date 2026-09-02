package info.cemu.cemu

import android.content.Context
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.Inet4Address
import java.net.InetAddress
import java.net.InetSocketAddress
import java.net.NetworkInterface
import java.net.SocketTimeoutException
import java.util.UUID
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.atomic.AtomicBoolean

data class WudroidProfile(
    val nickname: String,
    val roomName: String,
    val localId: String,
)

object WudroidProfileStore {
    private const val PREFS = "wudroid_profile_012"
    private const val KEY_NICK = "nickname"
    private const val KEY_ROOM = "room_name"
    private const val KEY_ID = "local_id"

    fun load(context: Context): WudroidProfile {
        val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        var id = prefs.getString(KEY_ID, null).orEmpty()
        if (id.isBlank()) {
            id = UUID.randomUUID().toString().replace("-", "").take(10)
            prefs.edit().putString(KEY_ID, id).apply()
        }
        val nick = prefs.getString(KEY_NICK, null)
            ?.trim()
            ?.takeIf { it.isNotBlank() }
            ?: "Jogador"
        val room = prefs.getString(KEY_ROOM, null)
            ?.trim()
            ?.takeIf { it.isNotBlank() }
            ?: "$nick • Wudroid"
        return WudroidProfile(nick, room, id)
    }

    fun save(context: Context, nickname: String, roomName: String): WudroidProfile {
        val old = load(context)
        val nick = nickname.trim().ifBlank { "Jogador" }.take(24)
        val room = roomName.trim().ifBlank { "$nick • Wudroid" }.take(36)
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit()
            .putString(KEY_NICK, nick)
            .putString(KEY_ROOM, room)
            .putString(KEY_ID, old.localId)
            .apply()
        return WudroidProfile(nick, room, old.localId)
    }
}

data class WudroidLanHost(
    val address: String,
    val hostId: String,
    val hostName: String,
    val roomName: String,
    val players: Int,
)

object WudroidLanMultiplayer {
    private const val PORT = 39891
    private const val DISCOVER = "WUDROID_DISCOVER_V1"
    private const val HOST = "WUDROID_HOST_V1"
    private const val JOIN = "WUDROID_JOIN_V1"
    private const val JOINED = "WUDROID_JOINED_V1"

    private val running = AtomicBoolean(false)
    @Volatile private var hostSocket: DatagramSocket? = null
    @Volatile private var hostThread: Thread? = null
    private val participants = ConcurrentHashMap<String, String>()

    @Synchronized
    fun startHost(context: Context): Boolean {
        if (running.get() && hostThread?.isAlive == true) return true
        stopHost()
        return try {
            val socket = DatagramSocket(null).apply {
                reuseAddress = true
                broadcast = true
                soTimeout = 700
                bind(InetSocketAddress(PORT))
            }
            val appContext = context.applicationContext
            hostSocket = socket
            participants.clear()
            running.set(true)
            hostThread = Thread({
                val buffer = ByteArray(1400)
                while (running.get()) {
                    try {
                        val packet = DatagramPacket(buffer, buffer.size)
                        socket.receive(packet)
                        val text = String(packet.data, 0, packet.length, Charsets.UTF_8)
                        val profile = WudroidProfileStore.load(appContext)
                        when {
                            text == DISCOVER -> {
                                val payload = listOf(
                                    HOST,
                                    clean(profile.localId),
                                    clean(profile.nickname),
                                    clean(profile.roomName),
                                    (1 + participants.size).toString(),
                                ).joinToString("|")
                                val bytes = payload.toByteArray(Charsets.UTF_8)
                                socket.send(DatagramPacket(bytes, bytes.size, packet.address, packet.port))
                            }
                            text.startsWith("$JOIN|") -> {
                                val parts = text.split("|", limit = 3)
                                if (parts.size >= 3) {
                                    participants[parts[1]] = clean(parts[2])
                                    val payload = "$JOINED|${clean(profile.localId)}|${1 + participants.size}"
                                    val bytes = payload.toByteArray(Charsets.UTF_8)
                                    socket.send(DatagramPacket(bytes, bytes.size, packet.address, packet.port))
                                }
                            }
                        }
                    } catch (_: SocketTimeoutException) {
                    } catch (_: Throwable) {
                        if (!running.get()) break
                    }
                }
                runCatching { socket.close() }
            }, "Wudroid-LAN-Host").apply {
                isDaemon = true
                start()
            }
            true
        } catch (_: Throwable) {
            running.set(false)
            hostSocket = null
            hostThread = null
            false
        }
    }

    @Synchronized
    fun stopHost() {
        running.set(false)
        runCatching { hostSocket?.close() }
        hostSocket = null
        hostThread = null
        participants.clear()
    }

    fun isHosting(): Boolean = running.get()
    fun participantCount(): Int = participants.size

    fun scanHosts(timeoutMs: Int = 900): List<WudroidLanHost> {
        val found = LinkedHashMap<String, WudroidLanHost>()
        val deadline = System.currentTimeMillis() + timeoutMs.coerceAtLeast(250)
        DatagramSocket().use { socket ->
            socket.broadcast = true
            socket.soTimeout = 180
            val bytes = DISCOVER.toByteArray(Charsets.UTF_8)
            broadcastAddresses().forEach { address ->
                runCatching { socket.send(DatagramPacket(bytes, bytes.size, address, PORT)) }
            }
            val buffer = ByteArray(1400)
            while (System.currentTimeMillis() < deadline) {
                try {
                    val packet = DatagramPacket(buffer, buffer.size)
                    socket.receive(packet)
                    val text = String(packet.data, 0, packet.length, Charsets.UTF_8)
                    val parts = text.split("|")
                    if (parts.size >= 5 && parts[0] == HOST) {
                        val item = WudroidLanHost(
                            address = packet.address.hostAddress ?: continue,
                            hostId = parts[1],
                            hostName = parts[2],
                            roomName = parts[3],
                            players = parts[4].toIntOrNull()?.coerceAtLeast(1) ?: 1,
                        )
                        found["${item.address}:${item.hostId}"] = item
                    }
                } catch (_: SocketTimeoutException) {
                } catch (_: Throwable) {
                }
            }
        }
        return found.values.toList()
    }

    fun joinHost(context: Context, host: WudroidLanHost, timeoutMs: Int = 1300): Boolean {
        val profile = WudroidProfileStore.load(context.applicationContext)
        return try {
            DatagramSocket().use { socket ->
                socket.soTimeout = timeoutMs
                val payload = "$JOIN|${clean(profile.localId)}|${clean(profile.nickname)}"
                val bytes = payload.toByteArray(Charsets.UTF_8)
                socket.send(DatagramPacket(bytes, bytes.size, InetAddress.getByName(host.address), PORT))
                val buffer = ByteArray(512)
                val reply = DatagramPacket(buffer, buffer.size)
                socket.receive(reply)
                val text = String(reply.data, 0, reply.length, Charsets.UTF_8)
                text.startsWith("$JOINED|${host.hostId}|")
            }
        } catch (_: Throwable) {
            false
        }
    }

    private fun broadcastAddresses(): Set<InetAddress> {
        val result = linkedSetOf<InetAddress>()
        runCatching { result += InetAddress.getByName("255.255.255.255") }
        runCatching {
            val interfaces = NetworkInterface.getNetworkInterfaces()
            while (interfaces.hasMoreElements()) {
                val network = interfaces.nextElement()
                if (!network.isUp || network.isLoopback) continue
                network.interfaceAddresses.forEach { iface ->
                    val address = iface.address
                    val broadcast = iface.broadcast
                    if (address is Inet4Address && broadcast != null) result += broadcast
                }
            }
        }
        return result
    }

    private fun clean(value: String): String =
        value.replace("|", " ").replace("\n", " ").replace("\r", " ").trim()
}
