package info.cemu.cemu

import android.content.Context
import android.content.pm.PackageManager
import android.net.wifi.WifiManager
import android.os.Build
import android.os.Handler
import android.os.Looper

data class WudroidHotspotState(
    val active: Boolean = false,
    val starting: Boolean = false,
    val ssid: String = "",
    val password: String = "",
    val error: String? = null,
)

object WudroidLocalHotspot {
    private val lock = Any()

    @Volatile
    private var reservation: WifiManager.LocalOnlyHotspotReservation? = null

    @Volatile
    private var currentState = WudroidHotspotState()

    fun state(): WudroidHotspotState = currentState

    fun requiredRuntimePermission(): String =
        if (Build.VERSION.SDK_INT >= 33)
            "android.permission.NEARBY_WIFI_DEVICES"
        else
            "android.permission.ACCESS_FINE_LOCATION"

    fun hasRuntimePermission(context: Context): Boolean =
        context.checkSelfPermission(requiredRuntimePermission()) == PackageManager.PERMISSION_GRANTED

    @Suppress("DEPRECATION")
    fun start(context: Context): Boolean {
        synchronized(lock) {
            if (reservation != null || currentState.starting) return true
            currentState = WudroidHotspotState(starting = true)
        }

        val appContext = context.applicationContext
        val wifiManager =
            appContext.getSystemService(Context.WIFI_SERVICE) as? WifiManager
                ?: run {
                    currentState = WudroidHotspotState(error = "Wi-Fi indisponível neste aparelho")
                    return false
                }

        return try {
            wifiManager.startLocalOnlyHotspot(
                object : WifiManager.LocalOnlyHotspotCallback() {
                    override fun onStarted(
                        newReservation: WifiManager.LocalOnlyHotspotReservation
                    ) {
                        synchronized(lock) {
                            reservation = newReservation

                            var ssid = ""
                            var password = ""

                            if (Build.VERSION.SDK_INT >= 30) {
                                val config = newReservation.softApConfiguration
                                ssid = config.ssid.orEmpty()
                                password = config.passphrase.orEmpty()
                            } else {
                                val config = newReservation.wifiConfiguration
                                ssid = config?.SSID?.trim('"').orEmpty()
                                password = config?.preSharedKey?.trim('"').orEmpty()
                            }

                            currentState = WudroidHotspotState(
                                active = true,
                                ssid = ssid,
                                password = password,
                            )
                        }
                    }

                    override fun onStopped() {
                        synchronized(lock) {
                            reservation = null
                            currentState = WudroidHotspotState(
                                error = "O Wi-Fi do Host foi desligado"
                            )
                        }
                    }

                    override fun onFailed(reason: Int) {
                        synchronized(lock) {
                            reservation = null
                            currentState = WudroidHotspotState(
                                error = when (reason) {
                                    WifiManager.LocalOnlyHotspotCallback.ERROR_NO_CHANNEL ->
                                        "Sem canal Wi-Fi disponível"
                                    WifiManager.LocalOnlyHotspotCallback.ERROR_INCOMPATIBLE_MODE ->
                                        "O Wi-Fi atual não permite criar o hotspot agora"
                                    WifiManager.LocalOnlyHotspotCallback.ERROR_TETHERING_DISALLOWED ->
                                        "Hotspot bloqueado pelas configurações do aparelho"
                                    else ->
                                        "Não foi possível criar o Wi-Fi do Host"
                                }
                            )
                        }
                    }
                },
                Handler(Looper.getMainLooper()),
            )
            true
        } catch (_: SecurityException) {
            currentState = WudroidHotspotState(
                error = "Permissão de Wi-Fi necessária"
            )
            false
        } catch (_: Throwable) {
            currentState = WudroidHotspotState(
                error = "Não foi possível criar o Wi-Fi do Host"
            )
            false
        }
    }

    fun stop() {
        val old = synchronized(lock) {
            val value = reservation
            reservation = null
            currentState = WudroidHotspotState()
            value
        }
        runCatching { old?.close() }
    }
}
