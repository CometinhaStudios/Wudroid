package info.cemu.cemu

import android.content.Context
import android.util.Log
import info.cemu.cemu.nativeinterface.NativeGameTitles
import info.cemu.cemu.nativeinterface.NativeGraphicPacks
import kotlin.math.abs
import kotlin.math.ln

object WudroidResolutionManager {
    private const val TAG = "WudroidResolution"
    private const val PREFS = "wudroid_resolution"
    private const val KEY_SCALE = "global_scale"

    data class ResolutionOption(
        val scale: Float,
        val label: String,
    )

    val options = listOf(
        ResolutionOption(0.25f, "0.25X (180p/120p)"),
        ResolutionOption(0.50f, "0.5X (360p/240p)"),
        ResolutionOption(0.75f, "0.75X (540p/360p)"),
        ResolutionOption(1.00f, "1X (720p/480p)"),
        ResolutionOption(1.25f, "1.25X (900p/600p)"),
        ResolutionOption(1.50f, "1.5X (1080p/720p)"),
        ResolutionOption(2.00f, "2X (1440p/960p)"),
        ResolutionOption(3.00f, "3X (2160p/1440p)"),
        ResolutionOption(4.00f, "4X (2880p/1920p)"),
    )

    fun getScale(context: Context): Float =
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .getFloat(KEY_SCALE, 1.0f)

    fun setScale(context: Context, scale: Float) {
        val valid = options.minByOrNull { abs(it.scale - scale) }?.scale ?: 1.0f
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit()
            .putFloat(KEY_SCALE, valid)
            .apply()
    }

    fun labelFor(scale: Float): String =
        options.minByOrNull { abs(it.scale - scale) }?.label ?: "1X (720p/480p)"

    fun applyForGame(context: Context, game: NativeGameTitles.Game): Boolean {
        val scale = getScale(context)
        return runCatching {
            NativeGraphicPacks.refreshGraphicPacks()

            val infos = NativeGraphicPacks.getGraphicPackBasicInfos()
                .filter { info -> info.titleIds.any { it == game.titleId } }

            var changed = false

            infos.forEach { info ->
                val pack = NativeGraphicPacks.getGraphicPack(info.id) ?: return@forEach
                val resolutionGroups = pack.presets.filter {
                    it.category?.contains("Resolution", ignoreCase = true) == true
                }
                if (resolutionGroups.isEmpty()) return@forEach

                if (!pack.isActive()) {
                    pack.setActive(true)
                }

                resolutionGroups.forEach { group ->
                    val preset = choosePreset(
                        context = context,
                        packId = info.id,
                        category = group.category ?: "Resolution",
                        presets = group.presets.toList(),
                        currentPreset = group.activePreset,
                        scale = scale,
                    ) ?: return@forEach

                    if (group.activePreset != preset) {
                        group.activePreset = preset
                    }
                    changed = true
                    Log.i(
                        TAG,
                        "Applied ${labelFor(scale)} to ${pack.name} / ${group.category}: $preset"
                    )
                }
            }

            if (!changed) {
                Log.w(
                    TAG,
                    "No compatible resolution Graphic Pack found for title " +
                        java.lang.Long.toUnsignedString(game.titleId, 16)
                )
            }

            changed
        }.getOrElse {
            Log.e(TAG, "Failed to apply Wudroid resolution profile", it)
            false
        }
    }

    private fun choosePreset(
        context: Context,
        packId: Long,
        category: String,
        presets: List<String>,
        currentPreset: String,
        scale: Float,
    ): String? {
        if (presets.isEmpty()) return null

        val token = when (scale) {
            0.25f -> "0.25X"
            0.50f -> "0.5X"
            0.75f -> "0.75X"
            1.00f -> "1X"
            1.25f -> "1.25X"
            1.50f -> "1.5X"
            2.00f -> "2X"
            3.00f -> "3X"
            4.00f -> "4X"
            else -> null
        }
        if (token != null) {
            presets.firstOrNull { it.trim().startsWith(token, ignoreCase = true) }?.let {
                return it
            }
        }

        val parsed = presets.mapNotNull { preset ->
            parseDimensions(preset)?.let { dims -> preset to dims }
        }
        if (parsed.isEmpty()) return null

        val prefs = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        val safeCategory = category.replace(Regex("[^A-Za-z0-9_]"), "_")
        val basePresetKey = "base_${packId}_$safeCategory"

        var basePreset = prefs.getString(basePresetKey, null)
        if (basePreset == null || presets.none { it == basePreset }) {
            basePreset =
                presets.firstOrNull { it.contains("default", ignoreCase = true) }
                    ?: currentPreset.takeIf { current -> presets.any { it == current } }
                    ?: parsed.first().first

            prefs.edit().putString(basePresetKey, basePreset).apply()
        }

        if (abs(scale - 1.0f) < 0.001f) {
            return basePreset
        }

        val baseDims = parseDimensions(basePreset) ?: parsed.first().second
        val targetW = baseDims.first * scale
        val targetH = baseDims.second * scale

        return parsed.minByOrNull { (_, dims) ->
            abs(ln((dims.first / targetW).toDouble())) + abs(ln((dims.second / targetH).toDouble()))
        }?.first
    }

    private fun parseDimensions(text: String): Pair<Float, Float>? {
        val match = Regex("""(\d{2,5})\s*[xX]\s*(\d{2,5})""").find(text) ?: return null
        val w = match.groupValues[1].toFloatOrNull() ?: return null
        val h = match.groupValues[2].toFloatOrNull() ?: return null
        if (w <= 0f || h <= 0f) return null
        return w to h
    }
}
