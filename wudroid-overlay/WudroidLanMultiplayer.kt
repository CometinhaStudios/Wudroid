package info.cemu.cemu

import android.content.Context
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.Inet4Address
import java.net.InetAddress
import java.net.InetSocketAddress
import java.net.NetworkInterface
import java.net.SocketTimeoutException
import java.security.MessageDigest
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
            ?.trim()?.takeIf { it.isNotBlank() } ?: "Jogador"
        val room = prefs.getString(KEY_ROOM, null)
            ?.trim()?.takeIf { it.isNotBlank() } ?: "$nick • Wudroid"
        return WudroidProfile(nick, room, id)
    }

    fun save(context: Context, nickname: String, roomName: String = ""): WudroidProfile {
        val old = load(context)
        val nick = nickname.trim().ifBlank { "Jogador" }.take(24)
        val room = roomName.trim().ifBlank { old.roomName.ifBlank { "$nick • Wudroid" } }.take(36)
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit()
            .putString(KEY_NICK, nick)
            .putString(KEY_ROOM, room)
            .putString(KEY_ID, old.localId)
            .apply()
        return WudroidProfile(nick, room, old.localId)
    }
}

data class WudroidRoomConfig(
    val roomName: String,
    val isPrivate: Boolean,
    val passwordHash: String = "",
)

data class WudroidLanParticipant(
    val localId: String,
    val nickname: String,
    val playerNumber: Int,
)

data class WudroidLanHost(
    val address: String,
    val hostId: String,
    val hostName: String,
    val roomName: String,
    val players: Int,
    val isPrivate: Boolean = false,
)

enum class WudroidJoinStatus {
    SUCCESS, WRONG_PASSWORD, FULL, FAILED
}

data class WudroidJoinResult(
    val status: WudroidJoinStatus,
    val playerNumber: Int = 0,
)

object WudroidLanMultiplayer {
    private const val PORT = 39891
    private const val DISCOVER_V1 = "WUDROID_DISCOVER_V1"
    private const val DISCOVER_V2 = "WUDROID_DISCOVER_V2"
    private const val HOST_V2 = "WUDROID_HOST_V2"
    private const val JOIN_V2 = "WUDROID_JOIN_V2"
    private const val JOINED_V2 = "WUDROID_JOINED_V2"
    private const val REJECT_V2 = "WUDROID_REJECT_V2"

    private val running = AtomicBoolean(false)
    @Volatile private var hostSocket: DatagramSocket? = null
    @Volatile private var hostThread: Thread? = null
    @Volatile private var currentRoom: WudroidRoomConfig? = null
    private val participants = ConcurrentHashMap<String, WudroidLanParticipant>()

    @Synchronized
    fun startHost(
        context: Context,
        roomName: String,
        isPrivate: Boolean,
        password: String,
    ): Boolean {
        stopHost()
        val profile = WudroidProfileStore.load(context.applicationContext)
        val cleanRoom = clean(roomName).ifBlank { "Partida de ${profile.nickname}" }.take(40)
        val passwordHash = if (isPrivate) hashPassword(password) else ""
        currentRoom = WudroidRoomConfig(cleanRoom, isPrivate, passwordHash)

        return try {
            val socket = DatagramSocket(null).apply {
                reuseAddress = true
                broadcast = true
                soTimeout = 500
                bind(InetSocketAddress(PORT))
            }
            val appContext = context.applicationContext
            hostSocket = socket
            participants.clear()
            running.set(true)

            hostThread = Thread({
                val buffer = ByteArray(1600)
                while (running.get()) {
                    try {
                        val packet = DatagramPacket(buffer, buffer.size)
                        socket.receive(packet)
                        val text = String(packet.data, 0, packet.length, Charsets.UTF_8)
                        val currentProfile = WudroidProfileStore.load(appContext)
                        val room = currentRoom ?: continue

                        when {
                            text == DISCOVER_V2 || text == DISCOVER_V1 -> {
                                val payload = listOf(
                                    HOST_V2,
                                    clean(currentProfile.localId),
                                    clean(currentProfile.nickname),
                                    clean(room.roomName),
                                    (1 + participants.size).toString(),
                                    if (room.isPrivate) "1" else "0",
                                ).joinToString("|")
                                reply(socket, packet, payload)
                            }

                            text.startsWith("$JOIN_V2|") -> {
                                val parts = text.split("|", limit = 5)
                                if (parts.size >= 5) {
                                    val clientId = clean(parts[1])
                                    val clientName = clean(parts[2]).ifBlank { "Jogador 2" }.take(24)
                                    val suppliedHash = parts[3]
                                    val existing = participants[clientId]

                                    if (room.isPrivate && suppliedHash != room.passwordHash) {
                                        reply(socket, packet, "$REJECT_V2|WRONG_PASSWORD")
                                    } else if (existing == null && participants.isNotEmpty()) {
                                        reply(socket, packet, "$REJECT_V2|FULL")
                                    } else {
                                        val participant = existing ?: WudroidLanParticipant(
                                            localId = clientId,
                                            nickname = clientName,
                                            playerNumber = 2,
                                        )
                                        participants[clientId] = participant
                                        reply(socket, packet, "$JOINED_V2|${clean(currentProfile.localId)}|${participant.playerNumber}")
                                    }
                                }
                            }
                        }
                    } catch (_: SocketTimeoutException) {
                    } catch (_: Throwable) {
                        if (!running.get()) break
                    }
                }
                runCatching { socket.close() }
            }, "Wudroid-LAN-Host-V2").apply {
                isDaemon = true
                start()
            }
            true
        } catch (_: Throwable) {
            running.set(false)
            currentRoom = null
            hostSocket = null
            hostThread = null
            false
        }
    }

    fun startHost(context: Context): Boolean {
        val profile = WudroidProfileStore.load(context.applicationContext)
        return startHost(context, profile.roomName, false, "")
    }

    @Synchronized
    fun stopHost() {
        running.set(false)
        runCatching { hostSocket?.close() }
        hostSocket = null
        hostThread = null
        currentRoom = null
        participants.clear()
    }

    fun isHosting(): Boolean = running.get()
    fun hostRoom(): WudroidRoomConfig? = currentRoom
    fun participantCount(): Int = participants.size
    fun participants(): List<WudroidLanParticipant> = participants.values.sortedBy { it.playerNumber }

    fun scanHosts(timeoutMs: Int = 1000): List<WudroidLanHost> {
        val found = LinkedHashMap<String, WudroidLanHost>()
        val deadline = System.currentTimeMillis() + timeoutMs.coerceAtLeast(350)

        DatagramSocket().use { socket ->
            socket.broadcast = true
            socket.soTimeout = 110
            val bytes = DISCOVER_V2.toByteArray(Charsets.UTF_8)

            broadcastAddresses().forEach { address ->
                runCatching { socket.send(DatagramPacket(bytes, bytes.size, address, PORT)) }
            }
            probeAddresses().forEach { address ->
                runCatching { socket.send(DatagramPacket(bytes, bytes.size, address, PORT)) }
            }

            val buffer = ByteArray(1600)
            while (System.currentTimeMillis() < deadline) {
                try {
                    val packet = DatagramPacket(buffer, buffer.size)
                    socket.receive(packet)
                    val text = String(packet.data, 0, packet.length, Charsets.UTF_8)
                    val parts = text.split("|")
                    if (parts.size >= 6 && parts[0] == HOST_V2) {
                        val item = WudroidLanHost(
                            address = packet.address.hostAddress ?: continue,
                            hostId = parts[1],
                            hostName = parts[2],
                            roomName = parts[3],
                            players = parts[4].toIntOrNull()?.coerceAtLeast(1) ?: 1,
                            isPrivate = parts[5] == "1",
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

    fun joinHost(
        context: Context,
        host: WudroidLanHost,
        password: String = "",
        timeoutMs: Int = 1500,
    ): WudroidJoinResult {
        val profile = WudroidProfileStore.load(context.applicationContext)
        return try {
            DatagramSocket().use { socket ->
                socket.soTimeout = timeoutMs
                val suppliedHash = if (host.isPrivate) hashPassword(password) else ""
                val payload = listOf(
                    JOIN_V2,
                    clean(profile.localId),
                    clean(profile.nickname),
                    suppliedHash,
                    "2",
                ).joinToString("|")
                val bytes = payload.toByteArray(Charsets.UTF_8)
                socket.send(DatagramPacket(bytes, bytes.size, InetAddress.getByName(host.address), PORT))

                val buffer = ByteArray(700)
                val reply = DatagramPacket(buffer, buffer.size)
                socket.receive(reply)
                val text = String(reply.data, 0, reply.length, Charsets.UTF_8)
                val parts = text.split("|")

                when {
                    parts.size >= 3 && parts[0] == JOINED_V2 && parts[1] == host.hostId ->
                        WudroidJoinResult(WudroidJoinStatus.SUCCESS, parts[2].toIntOrNull() ?: 2)
                    parts.size >= 2 && parts[0] == REJECT_V2 && parts[1] == "WRONG_PASSWORD" ->
                        WudroidJoinResult(WudroidJoinStatus.WRONG_PASSWORD)
                    parts.size >= 2 && parts[0] == REJECT_V2 && parts[1] == "FULL" ->
                        WudroidJoinResult(WudroidJoinStatus.FULL)
                    else -> WudroidJoinResult(WudroidJoinStatus.FAILED)
                }
            }
        } catch (_: Throwable) {
            WudroidJoinResult(WudroidJoinStatus.FAILED)
        }
    }

    private fun reply(socket: DatagramSocket, packet: DatagramPacket, text: String) {
        val bytes = text.toByteArray(Charsets.UTF_8)
        socket.send(DatagramPacket(bytes, bytes.size, packet.address, packet.port))
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
                    if (iface.address is Inet4Address && iface.broadcast != null) result += iface.broadcast
                }
            }
        }
        return result
    }

    private fun probeAddresses(): Set<InetAddress> {
        val result = linkedSetOf<InetAddress>()
        runCatching {
            val interfaces = NetworkInterface.getNetworkInterfaces()
            while (interfaces.hasMoreElements()) {
                val network = interfaces.nextElement()
                if (!network.isUp || network.isLoopback) continue
                val addresses = network.inetAddresses
                while (addresses.hasMoreElements()) {
                    val address = addresses.nextElement()
                    if (address !is Inet4Address || address.isLoopbackAddress) continue
                    val octets = address.hostAddress?.split(".") ?: continue
                    if (octets.size != 4) continue
                    val prefix = "${octets[0]}.${octets[1]}.${octets[2]}."
                    runCatching { result += InetAddress.getByName(prefix + "1") }
                    for (last in 2..254) {
                        if (last.toString() == octets[3]) continue
                        runCatching { result += InetAddress.getByName(prefix + last) }
                    }
                }
            }
        }
        return result
    }

    private fun hashPassword(value: String): String {
        val digest = MessageDigest.getInstance("SHA-256").digest(value.toByteArray(Charsets.UTF_8))
        return digest.joinToString("") { "%02x".format(it) }
    }

    private fun clean(value: String): String =
        value.replace("|", " ").replace("\n", " ").replace("\r", " ").trim()
}
