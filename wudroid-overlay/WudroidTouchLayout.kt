package info.cemu.cemu

import android.content.Context
import info.cemu.cemu.common.settings.AppSettingsStore
import info.cemu.cemu.common.settings.InputOverlaySettings
import info.cemu.cemu.common.settings.OverlayInputConfig
import kotlinx.coroutines.runBlocking

private const val TOUCH_LAYOUT_PREFS = "wudroid_touch_layout"
private const val TOUCH_LAYOUT_V1_APPLIED = "layout_v1_applied"

fun applyWudroidTouchLayoutV1(context: Context) {
    val prefs = context.getSharedPreferences(TOUCH_LAYOUT_PREFS, Context.MODE_PRIVATE)
    if (prefs.getBoolean(TOUCH_LAYOUT_V1_APPLIED, false)) return
    resetWudroidTouchLayout()
    prefs.edit().putBoolean(TOUCH_LAYOUT_V1_APPLIED, true).apply()
}

fun resetWudroidTouchLayout(): InputOverlaySettings =
    try {
        runBlocking {
            var result = InputOverlaySettings()
            AppSettingsStore.dataStore.updateData { appSettings ->
                val current = appSettings.inputOverlaySettings
                result = current.copy(
                    isOverlayEnabled = true,
                    controllerIndex = 0,
                    alpha = 112,
                    inputOverlayRectMap = emptyMap(),
                    inputVisibilityMap = current.inputVisibilityMap +
                        mapOf(
                            OverlayInputConfig.BUTTON_BLOW_MIC to false,
                            OverlayInputConfig.BUTTON_HOME to false
                        )
                )
                appSettings.copy(inputOverlaySettings = result)
            }
            result
        }
    } catch (_: Throwable) {
        InputOverlaySettings(
            isOverlayEnabled = true,
            controllerIndex = 0,
            alpha = 112
        )
    }
