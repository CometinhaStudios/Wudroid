package info.cemu.cemu

import android.content.Context
import android.content.pm.PackageManager
import android.net.wifi.WifiManager
import android.os.Build
import android.os.Handler
import android.os.Looper
import java.util.concurrent.Executor

data class WudroidHotspotState(
    val active: Boolean = false,
    val starting: Boolean = false,
    val ssid: String = "",
    val password: String = "",
    val isPrivate: Boolean = false,
    val exactConfiguration: Boolean = false,
    val error: String? = null,
)

object WudroidLocalHotspot {
    private val lock = Any()

    @Volatile
    private var reservation: WifiManager.LocalOnlyHotspotReservation? = null

    @Volatile
    private var currentState = WudroidHotspotState()

    @Volatile
    private var generation: Long = 0L

    fun state(): WudroidHotspotState = currentState

    fun requiredRuntimePermission(): String =
        if (Build.VERSION.SDK_INT >= 33)
            "android.permission.NEARBY_WIFI_DEVICES"
        else
            "android.permission.ACCESS_FINE_LOCATION"

    fun hasRuntimePermission(context: Context): Boolean =
        context.checkSelfPermission(requiredRuntimePermission()) == PackageManager.PERMISSION_GRANTED

    private fun cleanSsid(value: String): String = value.trim()

    private fun errorText(reason: Int): String =
        when (reason) {
            WifiManager.LocalOnlyHotspotCallback.ERROR_NO_CHANNEL ->
                "Sem canal Wi-Fi disponível"
            WifiManager.LocalOnlyHotspotCallback.ERROR_INCOMPATIBLE_MODE ->
                "O Wi-Fi atual não permite criar o hotspot agora"
            WifiManager.LocalOnlyHotspotCallback.ERROR_TETHERING_DISALLOWED ->
                "Hotspot bloqueado pelas configurações do aparelho"
            else ->
                "Não foi possível criar o Wi-Fi do Host"
        }

    @Suppress("DEPRECATION")
    fun start(
        context: Context,
        requestedSsid: String,
        isPrivate: Boolean,
        roomPassword: String,
        onReady: (Boolean) -> Unit = {},
    ): Boolean {
        val ssid = cleanSsid(requestedSsid)
        if (ssid.isBlank()) {
            currentState = WudroidHotspotState(error = "Nome da partida vazio")
            onReady(false)
            return false
        }

        if (Build.VERSION.SDK_INT >= 36) {
            val ssidBytes = ssid.toByteArray(Charsets.UTF_8).size
            if (ssidBytes !in 1..32) {
                currentState = WudroidHotspotState(
                    error = "No Wi-Fi do Host, o nome precisa ter até 32 bytes"
                )
                onReady(false)
                return false
            }

            if (isPrivate) {
                val passBytes = roomPassword.toByteArray(Charsets.UTF_8).size
                if (passBytes !in 8..63) {
                    currentState = WudroidHotspotState(
                        error = "A senha privada do Wi-Fi precisa ter de 8 a 63 bytes"
                    )
                    onReady(false)
                    return false
                }
            }
        }

        val myGeneration: Long
        synchronized(lock) {
            // A new session request replaces any previous hotspot reservation.
            generation += 1L
            myGeneration = generation

            runCatching { reservation?.close() }
            reservation = null

            currentState = WudroidHotspotState(
                starting = true,
                ssid = ssid,
                password = if (isPrivate) roomPassword else "",
                isPrivate = isPrivate,
                exactConfiguration = Build.VERSION.SDK_INT >= 36,
            )
        }

        val appContext = context.applicationContext
        val wifiManager =
            appContext.getSystemService(Context.WIFI_SERVICE) as? WifiManager
                ?: run {
                    currentState = WudroidHotspotState(error = "Wi-Fi indisponível neste aparelho")
                    onReady(false)
                    return false
                }

        val callback = object : WifiManager.LocalOnlyHotspotCallback() {
            override fun onStarted(
                newReservation: WifiManager.LocalOnlyHotspotReservation
            ) {
                // If the user cancelled while Android was creating the AP,
                // close the late reservation immediately.
                if (myGeneration != generation) {
                    runCatching { newReservation.close() }
                    return
                }

                synchronized(lock) {
                    reservation = newReservation

                    var actualSsid = ssid
                    var actualPassword = if (isPrivate) roomPassword else ""
                    var exact = Build.VERSION.SDK_INT >= 36

                    if (Build.VERSION.SDK_INT >= 30) {
                        val config = newReservation.softApConfiguration
                        actualSsid = config.ssid.orEmpty().ifBlank { ssid }
                        actualPassword = config.passphrase.orEmpty()
                    } else {
                        val config = newReservation.wifiConfiguration
                        actualSsid = config?.SSID?.trim('"').orEmpty().ifBlank { ssid }
                        actualPassword = config?.preSharedKey?.trim('"').orEmpty()
                        exact = false
                    }

                    currentState = WudroidHotspotState(
                        active = true,
                        ssid = actualSsid,
                        password = actualPassword,
                        isPrivate = actualPassword.isNotBlank(),
                        exactConfiguration = exact,
                    )
                }

                onReady(true)
            }

            override fun onStopped() {
                if (myGeneration != generation) return
                synchronized(lock) {
                    reservation = null
                    currentState = WudroidHotspotState(
                        error = "O Wi-Fi do Host foi desligado"
                    )
                }
            }

            override fun onFailed(reason: Int) {
                if (myGeneration != generation) return
                synchronized(lock) {
                    reservation = null
                    currentState = WudroidHotspotState(error = errorText(reason))
                }
                onReady(false)
            }
        }

        return try {
            if (Build.VERSION.SDK_INT >= 36) {
                // Android 16: public API allows app-defined local hotspot configuration.
                // Reflection keeps this source compatible with SDK/OEM variations around
                // SoftApConfiguration.Builder while still using the public API at runtime.
                val builderClass =
                    Class.forName("android.net.wifi.SoftApConfiguration\$Builder")
                val softApClass =
                    Class.forName("android.net.wifi.SoftApConfiguration")

                val builder = builderClass.getConstructor().newInstance()

                // setSsid(String)
                builderClass
                    .getMethod("setSsid", String::class.java)
                    .invoke(builder, ssid)

                val securityOpen =
                    softApClass.getField("SECURITY_TYPE_OPEN").getInt(null)
                val securityWpa2 =
                    softApClass.getField("SECURITY_TYPE_WPA2_PSK").getInt(null)

                builderClass
                    .getMethod(
                        "setPassphrase",
                        String::class.java,
                        Int::class.javaPrimitiveType,
                    )
                    .invoke(
                        builder,
                        if (isPrivate) roomPassword else null,
                        if (isPrivate) securityWpa2 else securityOpen,
                    )

                val config = builderClass.getMethod("build").invoke(builder)

                val startMethod = WifiManager::class.java.getMethod(
                    "startLocalOnlyHotspotWithConfiguration",
                    softApClass,
                    Executor::class.java,
                    WifiManager.LocalOnlyHotspotCallback::class.java,
                )

                startMethod.invoke(
                    wifiManager,
                    config,
                    appContext.mainExecutor,
                    callback,
                )
            } else {
                // Android 15 and older: framework chooses SSID/security credentials.
                // We still keep the reservation for the full Host session.
                synchronized(lock) {
                    currentState = currentState.copy(exactConfiguration = false)
                }
                wifiManager.startLocalOnlyHotspot(
                    callback,
                    Handler(Looper.getMainLooper()),
                )
            }
            true
        } catch (security: SecurityException) {
            if (myGeneration == generation) {
                currentState = WudroidHotspotState(
                    error = "Permissão de Wi-Fi necessária"
                )
            }
            onReady(false)
            false
        } catch (error: Throwable) {
            if (myGeneration == generation) {
                currentState = WudroidHotspotState(
                    error =
                        if (Build.VERSION.SDK_INT >= 36)
                            "O Android não aceitou a configuração do Wi-Fi do Host"
                        else
                            "Não foi possível criar o Wi-Fi do Host"
                )
            }
            onReady(false)
            false
        }
    }

    fun stop() {
        val old = synchronized(lock) {
            generation += 1L
            val value = reservation
            reservation = null
            currentState = WudroidHotspotState()
            value
        }
        runCatching { old?.close() }
    }
}
