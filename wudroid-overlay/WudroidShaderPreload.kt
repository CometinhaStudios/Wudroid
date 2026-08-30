package info.cemu.cemu

import android.content.Context
import android.system.Os
import info.cemu.cemu.nativeinterface.NativeGameTitles

object WudroidShaderPreload {
    private const val PREFS = "wudroid_shader_preload"

    fun isEnabled(context: Context): Boolean =
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getBoolean("enabled", true)

    fun prepareBeforeLaunch(context: Context, game: NativeGameTitles.Game) {
        val enabled = isEnabled(context)
        runCatching {
            Os.setenv("WUDROID_SHADER_PRELOAD", if (enabled) "1" else "0", true)
            Os.setenv(
                "WUDROID_SHADER_PRELOAD_TITLE",
                java.lang.Long.toUnsignedString(game.titleId, 16).padStart(16, '0'),
                true,
            )
        }
    }
}
