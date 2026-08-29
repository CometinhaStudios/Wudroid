package info.cemu.cemu

import android.content.Context
import android.util.Log
import info.cemu.cemu.nativeinterface.NativeGameTitles
import info.cemu.cemu.nativeinterface.NativeGraphicPacks

object WudroidAntiAliasingManager {
    private const val TAG = "WudroidAA"
    private const val PREFS = "wudroid_aa"
    private const val GLOBAL_MODE = "global_mode"

    const val MODE_DEFAULT = "DEFAULT"
    const val MODE_OFF = "OFF"
    const val MODE_FXAA = "FXAA"
    const val MODE_NVIDIA_FXAA = "NVIDIA_FXAA"
    const val MODE_USE_GLOBAL = "USE_GLOBAL"
    private const val EXACT_PREFIX = "PRESET:"

    data class Method(val value: String, val label: String)

    val globalMethods = listOf(
        Method(MODE_DEFAULT, "Padrão do jogo"),
        Method(MODE_OFF, "Desativado"),
        Method(MODE_FXAA, "FXAA"),
        Method(MODE_NVIDIA_FXAA, "NVIDIA FXAA"),
    )

    fun getGlobalMode(context: Context): String =
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .getString(GLOBAL_MODE, MODE_DEFAULT) ?: MODE_DEFAULT

    fun setGlobalMode(context: Context, value: String) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit().putString(GLOBAL_MODE, value).apply()
    }

    fun exactValue(preset: String): String = EXACT_PREFIX + preset
    fun exactPreset(value: String): String? =
        value.takeIf { it.startsWith(EXACT_PREFIX) }?.removePrefix(EXACT_PREFIX)

    fun availablePresets(game: NativeGameTitles.Game): List<String> = runCatching {
        NativeGraphicPacks.refreshGraphicPacks()
        val result = mutableListOf<String>()
        val infos = NativeGraphicPacks.getGraphicPackBasicInfos()
            .filter { it.titleIds.any { id -> id == game.titleId } }
        for (info in infos) {
            val pack = NativeGraphicPacks.getGraphicPack(info.id) ?: continue
            for (group in pack.presets) {
                if (isAaGroup(pack.name, group.category)) {
                    result += group.presets
                }
            }
        }
        result.distinct()
    }.getOrDefault(emptyList())

    fun applyForGame(
        context: Context,
        game: NativeGameTitles.Game,
        overrideMode: String? = null,
    ): Boolean {
        val mode = when (overrideMode) {
            null, MODE_USE_GLOBAL -> getGlobalMode(context)
            else -> overrideMode
        }
        if (mode == MODE_DEFAULT) return false

        return runCatching {
            NativeGraphicPacks.refreshGraphicPacks()
            val infos = NativeGraphicPacks.getGraphicPackBasicInfos()
                .filter { it.titleIds.any { id -> id == game.titleId } }
            var changed = false

            for (info in infos) {
                val pack = NativeGraphicPacks.getGraphicPack(info.id) ?: continue
                val groups = pack.presets.filter { isAaGroup(pack.name, it.category) }
                for (group in groups) {
                    val target = choosePreset(mode, group.presets.toList()) ?: continue
                    if (!pack.isActive()) pack.setActive(true)
                    if (group.activePreset != target) group.activePreset = target
                    changed = true
                    Log.i(TAG, "Applied ${pack.name}/${group.category}: $target")
                }
            }
            changed
        }.getOrElse {
            Log.e(TAG, "Failed to apply anti-aliasing", it)
            false
        }
    }

    private fun isAaGroup(packName: String, category: String?): Boolean {
        val text = (category ?: packName).lowercase()
        return text.contains("anti-alias") || text.contains("antialias") ||
            text == "aa" || text.startsWith("aa ")
    }

    private fun choosePreset(mode: String, presets: List<String>): String? {
        exactPreset(mode)?.let { exact ->
            return presets.firstOrNull { it == exact }
        }
        return when (mode) {
            MODE_OFF -> presets.firstOrNull {
                val n = it.lowercase()
                n.contains("none") || n.contains("disabled") || n.contains("off")
            }
            MODE_NVIDIA_FXAA -> presets.firstOrNull {
                val n = it.lowercase()
                n.contains("nvidia") && n.contains("fxaa")
            }
            MODE_FXAA -> presets.firstOrNull {
                it.lowercase().contains("normal fxaa")
            } ?: presets.firstOrNull {
                val n = it.lowercase()
                n.contains("fxaa") && !n.contains("nvidia")
            }
            else -> null
        }
    }
}
