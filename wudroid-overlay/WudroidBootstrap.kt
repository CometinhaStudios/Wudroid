package info.cemu.cemu

import android.content.Context
import info.cemu.cemu.common.settings.AppSettingsStore
import kotlinx.coroutines.runBlocking

object WudroidBootstrap {
    private const val PREFS = "wudroid_bootstrap"
    private const val TOUCH_DEFAULT_007 = "touch_overlay_default_007"

    @JvmStatic
    fun applyFirstRunDefaults(context: Context) {
        val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        if (prefs.getBoolean(TOUCH_DEFAULT_007, false)) return

        try {
            runBlocking {
                AppSettingsStore.dataStore.updateData { settings ->
                    settings.copy(
                        inputOverlaySettings = settings.inputOverlaySettings.copy(
                            isOverlayEnabled = true,
                            alpha = maxOf(settings.inputOverlaySettings.alpha, 128),
                        )
                    )
                }
            }
            prefs.edit().putBoolean(TOUCH_DEFAULT_007, true).apply()
        } catch (_: Throwable) {
            // Do not mark migration complete if DataStore is not ready.
        }
    }
}
