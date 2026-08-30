package info.cemu.cemu.framegen

import android.content.Context
import android.system.Os

object WudroidNativeFrameGen {
    private const val PREFS = "wudroid_native_framegen"
    private const val KEY_ENABLED = "enabled"
    private const val KEY_QUALITY = "quality"
    private const val KEY_STRENGTH = "strength"

    data class Config(
        val enabled: Boolean = false,
        val quality: Int = 1, // 0 performance, 1 balanced, 2 quality
        val strength: Float = 0.92f,
    )

    fun load(context: Context): Config {
        val p = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        return Config(
            enabled = p.getBoolean(KEY_ENABLED, false),
            quality = p.getInt(KEY_QUALITY, 1).coerceIn(0, 2),
            strength = p.getFloat(KEY_STRENGTH, 0.92f).coerceIn(0.0f, 1.0f),
        )
    }

    fun saveAndApply(context: Context, config: Config) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit()
            .putBoolean(KEY_ENABLED, config.enabled)
            .putInt(KEY_QUALITY, config.quality.coerceIn(0, 2))
            .putFloat(KEY_STRENGTH, config.strength.coerceIn(0.0f, 1.0f))
            .apply()
        apply(config)
    }

    fun applySaved(context: Context) = apply(load(context))

    private fun apply(config: Config) {
        runCatching {
            Os.setenv("WUDROID_FRAMEGEN_ENABLED", if (config.enabled) "1" else "0", true)
            Os.setenv("WUDROID_FRAMEGEN_QUALITY", config.quality.toString(), true)
            Os.setenv("WUDROID_FRAMEGEN_STRENGTH", config.strength.toString(), true)
        }
    }
}

object WudroidNativeFrameGenBridge {
    external fun nativeStatusCode(): Int
    external fun nativeFps(): IntArray
    external fun nativeHasNvOpticalFlow(): Boolean
    external fun nativeLastError(): String

    fun statusCode(): Int = runCatching { nativeStatusCode() }.getOrDefault(0)
    fun fps(): IntArray = runCatching { nativeFps() }.getOrDefault(intArrayOf(0, 0, 0))
    fun hasNvOpticalFlow(): Boolean = runCatching { nativeHasNvOpticalFlow() }.getOrDefault(false)
    fun lastError(): String = runCatching { nativeLastError() }.getOrDefault("")
}
