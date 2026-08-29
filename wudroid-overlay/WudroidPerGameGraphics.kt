package info.cemu.cemu

import android.content.Context
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import info.cemu.cemu.nativeinterface.NativeGameTitles
import info.cemu.cemu.nativeinterface.NativeSettings

object WudroidGameGraphicsProfiles {
    private const val PREFS = "wudroid_per_game_graphics"
    const val USE_GLOBAL = -1
    const val ENGINE_VULKAN = 0
    const val ENGINE_VULKAN_X = 1

    private fun prefs(context: Context) =
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)

    private fun key(base: String, titleId: Long) = "${base}_$titleId"

    fun captureGlobalsIfMissing(context: Context, globalEngine: Int? = null) {
        val p = prefs(context)
        val e = p.edit()
        var changed = false
        if (!p.contains("global_vsync")) {
            e.putInt("global_vsync", runCatching { NativeSettings.getVsyncMode() }.getOrDefault(1))
            changed = true
        }
        if (!p.contains("global_upscale")) {
            e.putInt("global_upscale", runCatching { NativeSettings.getUpscalingFilter() }.getOrDefault(0))
            changed = true
        }
        if (!p.contains("global_downscale")) {
            e.putInt("global_downscale", runCatching { NativeSettings.getDownscalingFilter() }.getOrDefault(0))
            changed = true
        }
        if (!p.contains("global_engine") && globalEngine != null) {
            e.putInt("global_engine", globalEngine)
            changed = true
        }
        if (changed) e.apply()
    }

    fun setGlobalVsync(context: Context, value: Int) =
        prefs(context).edit().putInt("global_vsync", value).apply()
    fun setGlobalUpscaling(context: Context, value: Int) =
        prefs(context).edit().putInt("global_upscale", value).apply()
    fun setGlobalDownscaling(context: Context, value: Int) =
        prefs(context).edit().putInt("global_downscale", value).apply()
    fun setGlobalGraphicsEngine(context: Context, value: Int) =
        prefs(context).edit().putInt("global_engine", value).apply()

    fun getGlobalVsync(context: Context): Int {
        captureGlobalsIfMissing(context)
        return prefs(context).getInt("global_vsync", 1)
    }
    fun getGlobalUpscaling(context: Context): Int {
        captureGlobalsIfMissing(context)
        return prefs(context).getInt("global_upscale", 0)
    }
    fun getGlobalDownscaling(context: Context): Int {
        captureGlobalsIfMissing(context)
        return prefs(context).getInt("global_downscale", 0)
    }
    fun getGlobalGraphicsEngine(context: Context, fallback: Int): Int {
        captureGlobalsIfMissing(context, fallback)
        return prefs(context).getInt("global_engine", fallback)
    }

    fun getEngine(context: Context, titleId: Long): Int =
        prefs(context).getInt(key("engine", titleId), USE_GLOBAL)
    fun setEngine(context: Context, titleId: Long, value: Int) =
        prefs(context).edit().putInt(key("engine", titleId), value).apply()

    fun getResolution(context: Context, titleId: Long): Float =
        prefs(context).getFloat(key("resolution", titleId), -1f)
    fun setResolution(context: Context, titleId: Long, value: Float) =
        prefs(context).edit().putFloat(key("resolution", titleId), value).apply()

    fun getVsync(context: Context, titleId: Long): Int =
        prefs(context).getInt(key("vsync", titleId), USE_GLOBAL)
    fun setVsync(context: Context, titleId: Long, value: Int) =
        prefs(context).edit().putInt(key("vsync", titleId), value).apply()

    fun getUpscaling(context: Context, titleId: Long): Int =
        prefs(context).getInt(key("upscale", titleId), USE_GLOBAL)
    fun setUpscaling(context: Context, titleId: Long, value: Int) =
        prefs(context).edit().putInt(key("upscale", titleId), value).apply()

    fun getDownscaling(context: Context, titleId: Long): Int =
        prefs(context).getInt(key("downscale", titleId), USE_GLOBAL)
    fun setDownscaling(context: Context, titleId: Long, value: Int) =
        prefs(context).edit().putInt(key("downscale", titleId), value).apply()

    fun getAa(context: Context, titleId: Long): String =
        prefs(context).getString(
            key("aa", titleId),
            WudroidAntiAliasingManager.MODE_USE_GLOBAL
        ) ?: WudroidAntiAliasingManager.MODE_USE_GLOBAL

    fun setAa(context: Context, titleId: Long, value: String) =
        prefs(context).edit().putString(key("aa", titleId), value).apply()

    fun applyBeforeLaunch(
        context: Context,
        game: NativeGameTitles.Game,
        globalEngineFallback: Int,
    ): Int {
        captureGlobalsIfMissing(context, globalEngineFallback)
        val titleId = game.titleId

        val vsync = getVsync(context, titleId).let {
            if (it == USE_GLOBAL) getGlobalVsync(context) else it
        }
        val up = getUpscaling(context, titleId).let {
            if (it == USE_GLOBAL) getGlobalUpscaling(context) else it
        }
        val down = getDownscaling(context, titleId).let {
            if (it == USE_GLOBAL) getGlobalDownscaling(context) else it
        }

        runCatching {
            NativeSettings.setVsyncMode(vsync)
            NativeSettings.setUpscalingFilter(up)
            NativeSettings.setDownscalingFilter(down)
            NativeSettings.saveSettings()
        }

        val scale = getResolution(context, titleId).takeIf { it > 0f }
            ?: WudroidResolutionManager.getScale(context)
        WudroidResolutionManager.applyForGame(context, game, scale)
        WudroidAntiAliasingManager.applyForGame(context, game, getAa(context, titleId))
        WudroidFrameGeneration.prepareForLaunch(context, game)

        val engine = getEngine(context, titleId)
        return if (engine == USE_GLOBAL) {
            getGlobalGraphicsEngine(context, globalEngineFallback)
        } else engine
    }
}

private val ProfileBlue = Color(0xFF00B8F5)
private val ProfileMuted = Color(0xFF9DA8B4)

@Composable
fun WudroidPerGameGraphicsDialog(
    game: NativeGameTitles.Game,
    onDismiss: () -> Unit,
) {
    val context = androidx.compose.ui.platform.LocalContext.current
    val id = game.titleId
    var engine by remember { mutableIntStateOf(WudroidGameGraphicsProfiles.getEngine(context, id)) }
    var resolution by remember { mutableFloatStateOf(WudroidGameGraphicsProfiles.getResolution(context, id)) }
    var vsync by remember { mutableIntStateOf(WudroidGameGraphicsProfiles.getVsync(context, id)) }
    var upscale by remember { mutableIntStateOf(WudroidGameGraphicsProfiles.getUpscaling(context, id)) }
    var downscale by remember { mutableIntStateOf(WudroidGameGraphicsProfiles.getDownscaling(context, id)) }
    var aa by remember { mutableStateOf(WudroidGameGraphicsProfiles.getAa(context, id)) }
    var frameGenMode by remember {
        mutableIntStateOf(WudroidFrameGeneration.getMode(context, id))
    }
    val aaPresets = remember(game.titleId) { WudroidAntiAliasingManager.availablePresets(game) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Gráficos • ${game.name ?: "Jogo"}") },
        text = {
            LazyColumn(modifier = Modifier.heightIn(max = 520.dp)) {
                item {
                    ProfileSection("Motor gráfico")
                    ProfileChoices(
                        listOf(
                            WudroidGameGraphicsProfiles.USE_GLOBAL to "Usar global",
                            WudroidGameGraphicsProfiles.ENGINE_VULKAN to "Vulkan padrão",
                            WudroidGameGraphicsProfiles.ENGINE_VULKAN_X to "Vulkan X",
                        ),
                        engine
                    ) {
                        engine = it
                        WudroidGameGraphicsProfiles.setEngine(context, id, it)
                    }

                    ProfileSection("Resolução")
                    ProfileChoice("Usar global", resolution < 0f) {
                        resolution = -1f
                        WudroidGameGraphicsProfiles.setResolution(context, id, -1f)
                    }
                    WudroidResolutionManager.options.forEach { option ->
                        ProfileChoice(
                            option.label,
                            kotlin.math.abs(resolution - option.scale) < .001f
                        ) {
                            resolution = option.scale
                            WudroidGameGraphicsProfiles.setResolution(context, id, option.scale)
                        }
                    }

                    ProfileSection("VSync")
                    ProfileChoices(
                        listOf(
                            -1 to "Usar global",
                            0 to "Desligado",
                            1 to "Duplo",
                            2 to "Triplo",
                        ),
                        vsync
                    ) {
                        vsync = it
                        WudroidGameGraphicsProfiles.setVsync(context, id, it)
                    }

                    ProfileSection("Filtro de ampliação")
                    ProfileChoices(filterChoices(), upscale) {
                        upscale = it
                        WudroidGameGraphicsProfiles.setUpscaling(context, id, it)
                    }

                    ProfileSection("Filtro de redução")
                    ProfileChoices(filterChoices(), downscale) {
                        downscale = it
                        WudroidGameGraphicsProfiles.setDownscaling(context, id, it)
                    }

                    ProfileSection("Frame Generation")
                    ProfileChoice(
                        "Desativado",
                        frameGenMode == WudroidFrameGeneration.MODE_OFF
                    ) {
                        frameGenMode = WudroidFrameGeneration.MODE_OFF
                        WudroidFrameGeneration.setMode(context, id, frameGenMode)
                    }
                    ProfileChoice(
                        "LSFG 2X [Foundation]",
                        frameGenMode == WudroidFrameGeneration.MODE_LSFG_2X
                    ) {
                        frameGenMode = WudroidFrameGeneration.MODE_LSFG_2X
                        WudroidFrameGeneration.setMode(context, id, frameGenMode)
                    }
                    Text(
                        if (WudroidFrameGeneration.hasDll(context))
                            "Lossless.dll pronta. O hook Vulkan entra no próximo teste nativo."
                        else
                            "Importe sua Lossless.dll em Configurações avançadas antes de usar LSFG.",
                        color = ProfileMuted,
                        fontSize = 11.sp,
                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 4.dp)
                    )

                    ProfileSection("Anti-aliasing")
                    ProfileChoice(
                        "Usar global",
                        aa == WudroidAntiAliasingManager.MODE_USE_GLOBAL
                    ) {
                        aa = WudroidAntiAliasingManager.MODE_USE_GLOBAL
                        WudroidGameGraphicsProfiles.setAa(context, id, aa)
                    }
                    ProfileChoice(
                        "Padrão do jogo",
                        aa == WudroidAntiAliasingManager.MODE_DEFAULT
                    ) {
                        aa = WudroidAntiAliasingManager.MODE_DEFAULT
                        WudroidGameGraphicsProfiles.setAa(context, id, aa)
                    }

                    if (aaPresets.isEmpty()) {
                        Text(
                            "Este jogo não expõe métodos de anti-aliasing nos Graphic Packs instalados.",
                            color = ProfileMuted,
                            fontSize = 12.sp,
                            modifier = Modifier.padding(vertical = 8.dp),
                        )
                    } else {
                        aaPresets.forEach { preset ->
                            val value = WudroidAntiAliasingManager.exactValue(preset)
                            ProfileChoice(preset, aa == value) {
                                aa = value
                                WudroidGameGraphicsProfiles.setAa(context, id, value)
                            }
                        }
                    }

                    Spacer(Modifier.height(12.dp))
                    Text(
                        "Salvo somente para este jogo e aplicado antes dele abrir.",
                        color = ProfileMuted,
                        fontSize = 12.sp,
                    )
                }
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) { Text("Pronto") }
        },
    )
}

@Composable
private fun ProfileSection(title: String) {
    Spacer(Modifier.height(10.dp))
    Text(title, color = ProfileBlue, fontWeight = FontWeight.Bold, fontSize = 13.sp)
}

@Composable
private fun ProfileChoices(
    options: List<Pair<Int, String>>,
    selected: Int,
    onSelected: (Int) -> Unit,
) {
    Column {
        options.forEach { (value, label) ->
            ProfileChoice(label, selected == value) { onSelected(value) }
        }
    }
}

@Composable
private fun ProfileChoice(
    label: String,
    selected: Boolean,
    onClick: () -> Unit,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .padding(vertical = 2.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        RadioButton(selected = selected, onClick = null)
        Text(label)
    }
}

private fun filterChoices() = listOf(
    -1 to "Usar global",
    3 to "Nearest Neighbor",
    0 to "Bilinear",
    1 to "Bicubic",
    2 to "Bicubic Hermite",
)
