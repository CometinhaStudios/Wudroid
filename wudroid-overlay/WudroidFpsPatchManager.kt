package info.cemu.cemu

import android.content.Context
import android.util.Log
import info.cemu.cemu.nativeinterface.NativeGameTitles
import info.cemu.cemu.nativeinterface.NativeGraphicPacks

/**
 * Wudroid 0.1.1 FPS patch controller.
 *
 * This does not "speed up" the whole emulator. It activates a game-specific
 * Cemu Graphic Pack that changes the game's own frame timing / FPS limit.
 * When the pack offers an FPS preset, Wudroid selects the 60 FPS preset.
 */
object WudroidFpsPatchManager {
    private const val TAG = "WudroidFPS"
    private const val PREFS = "wudroid_per_game_fps"

    const val MODE_ORIGINAL = 0
    const val MODE_60_FPS = 1

    data class Availability(
        val available: Boolean,
        val packNames: List<String>,
        val descriptions: List<String>,
    )

    private fun key(titleId: Long) = "fps_mode_$titleId"

    fun getMode(context: Context, titleId: Long): Int =
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .getInt(key(titleId), MODE_ORIGINAL)

    fun setMode(context: Context, titleId: Long, mode: Int) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit()
            .putInt(key(titleId), mode)
            .apply()
    }

    fun availability(game: NativeGameTitles.Game): Availability = runCatching {
        NativeGraphicPacks.refreshGraphicPacks()

        val names = mutableListOf<String>()
        val descriptions = mutableListOf<String>()

        for (info in NativeGraphicPacks.getGraphicPackBasicInfos()) {
            if (!info.titleIds.any { it == game.titleId }) continue

            val pack = NativeGraphicPacks.getGraphicPack(info.id) ?: continue
            if (!isFpsPatch(info.virtualPath, pack)) continue

            names += pack.name
            if (pack.description.isNotBlank()) descriptions += pack.description
        }

        Availability(
            available = names.isNotEmpty(),
            packNames = names.distinct(),
            descriptions = descriptions.distinct(),
        )
    }.getOrElse {
        Log.e(TAG, "Could not query FPS patches", it)
        Availability(false, emptyList(), emptyList())
    }

    fun applyForGame(
        context: Context,
        game: NativeGameTitles.Game,
    ): List<String> {
        val mode = getMode(context, game.titleId)

        return runCatching {
            NativeGraphicPacks.refreshGraphicPacks()
            val changed = mutableListOf<String>()

            for (info in NativeGraphicPacks.getGraphicPackBasicInfos()) {
                if (!info.titleIds.any { it == game.titleId }) continue

                val pack = NativeGraphicPacks.getGraphicPack(info.id) ?: continue
                if (!isFpsPatch(info.virtualPath, pack)) continue

                if (mode == MODE_ORIGINAL) {
                    if (pack.isActive()) {
                        pack.setActive(false)
                        changed += "${pack.name}: Original"
                        Log.i(TAG, "Disabled FPS patch ${pack.name}")
                    }
                    continue
                }

                if (!pack.isActive()) pack.setActive(true)

                // Dynamic FPS/FPS++ packs expose many values. Pick exactly 60.
                for (group in pack.presets) {
                    if (!isMainFpsGroup(group.category)) continue
                    val preset = choose60Preset(group.presets.toList()) ?: continue
                    if (group.activePreset != preset) {
                        group.activePreset = preset
                    }
                }

                changed += "${pack.name}: 60 FPS"
                Log.i(TAG, "Enabled FPS patch ${pack.name} for ${game.name}")
            }

            changed
        }.getOrElse {
            Log.e(TAG, "Failed to apply FPS patch", it)
            emptyList()
        }
    }

    private fun isFpsPatch(
        virtualPath: String,
        pack: NativeGraphicPacks.GraphicPack,
    ): Boolean {
        val path = virtualPath.lowercase()
        val name = pack.name.lowercase()
        val joined = "$path $name"

        // Never interpret an explicit 30 FPS limiter as an unlock patch.
        if (joined.contains("30fps") && !joined.contains("60fps")) return false

        if (
            joined.contains("60fps") ||
            joined.contains("60 fps") ||
            joined.contains("fps++") ||
            joined.contains("uncapped") ||
            joined.contains("static fps") ||
            joined.contains("staticfps")
        ) {
            return true
        }

        // Packs such as Skylanders simply use the name/path "FPS" and expose a
        // 60 FPS preset.
        val simpleFpsName =
            name == "fps" ||
            name == "fps v2" ||
            path.endsWith("/fps") ||
            path.endsWith("\\fps")

        return simpleFpsName && pack.presets.any { group ->
            choose60Preset(group.presets.toList()) != null
        }
    }

    private fun isMainFpsGroup(category: String?): Boolean {
        val text = category?.trim()?.lowercase() ?: return false

        if (
            text.contains("cutscene") ||
            text.contains("debug") ||
            text.contains("mode") ||
            text.contains("low fps") ||
            text.contains("minimum")
        ) {
            return false
        }

        return text == "fps" ||
            text == "fps limit" ||
            text == "framerate" ||
            text == "framerate limit" ||
            text == "frame rate" ||
            text == "frame rate limit" ||
            (text.contains("fps") && text.contains("limit"))
    }

    private fun choose60Preset(presets: List<String>): String? {
        return presets.firstOrNull { preset ->
            val n = preset
                .lowercase()
                .replace(" ", "")
                .replace("-", "")
            n.contains("60fps") && !n.contains("160fps")
        }
    }
}
