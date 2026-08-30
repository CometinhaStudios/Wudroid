package info.cemu.cemu

import android.content.Context
import info.cemu.cemu.nativeinterface.NativeGameTitles
import info.cemu.cemu.nativeinterface.NativeSettings

/**
 * Wudroid 0.1.1 direct-Vulkan frame generation.
 *
 * This replaces the old MediaProjection/Lossless.dll path. Settings are pushed
 * straight into Cemu's native Vulkan renderer before a game starts. The native
 * present hook keeps the previous/current frames and inserts temporal
 * intermediate frames directly into the swapchain.
 */
object WudroidFrameGenerationManager {
    private const val PREFS = "wudroid_frame_generation"

    const val PRESET_ECO = 0
    const val PRESET_FLOW = 1
    const val PRESET_BALANCED = 2
    const val PRESET_BOOST = 3
    const val PRESET_CLEAR = 4
    const val PRESET_MAX = 5

    data class Config(
        val enabled: Boolean = false,
        val useGlobal: Boolean = false,
        val multiplier: Int = 2,
        val preset: Int = PRESET_BALANCED,
        val flowScale: Float = 0.50f,
    )

    data class NativeState(
        val bridgeCompiled: Boolean,
        val presentHookActive: Boolean,
        val opticalFlowAdvertised: Boolean,
        val generatedFrames: Long,
        val engine: String,
    )

    private fun prefs(context: Context) =
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)

    private fun gamePrefix(titleId: Long) =
        "game_${java.lang.Long.toUnsignedString(titleId, 16)}_"

    fun globalConfig(context: Context): Config {
        val p = prefs(context)
        val preset = p.getInt("global_preset", PRESET_BALANCED).coerceIn(0, 5)
        return Config(
            enabled = p.getBoolean("global_enabled", false),
            useGlobal = false,
            multiplier = p.getInt("global_multiplier", 2).coerceIn(2, 4),
            preset = preset,
            flowScale = p.getFloat("global_flow_scale", defaultScaleForPreset(preset))
                .coerceIn(0.20f, 1.00f),
        )
    }

    fun gameConfig(context: Context, titleId: Long): Config {
        val p = prefs(context)
        val prefix = gamePrefix(titleId)
        val useGlobal = p.getBoolean("${prefix}use_global", false)
        if (useGlobal) return globalConfig(context).copy(useGlobal = true)

        val preset = p.getInt("${prefix}preset", PRESET_BALANCED).coerceIn(0, 5)
        return Config(
            enabled = p.getBoolean("${prefix}enabled", false),
            useGlobal = false,
            multiplier = p.getInt("${prefix}multiplier", 2).coerceIn(2, 4),
            preset = preset,
            flowScale = p.getFloat("${prefix}flow_scale", defaultScaleForPreset(preset))
                .coerceIn(0.20f, 1.00f),
        )
    }

    fun saveGameConfig(context: Context, titleId: Long, config: Config) {
        val prefix = gamePrefix(titleId)
        prefs(context).edit()
            .putBoolean("${prefix}use_global", config.useGlobal)
            .putBoolean("${prefix}enabled", config.enabled)
            .putInt("${prefix}multiplier", config.multiplier.coerceIn(2, 4))
            .putInt("${prefix}preset", config.preset.coerceIn(0, 5))
            .putFloat("${prefix}flow_scale", config.flowScale.coerceIn(0.20f, 1.00f))
            .apply()
        pushNative(config)
    }

    fun useGlobalForGame(context: Context, titleId: Long) {
        val prefix = gamePrefix(titleId)
        prefs(context).edit().putBoolean("${prefix}use_global", true).apply()
        pushNative(globalConfig(context))
    }

    fun nativeState(): NativeState {
        val bridge = runCatching { WudroidFrameGenerationNative.isBridgeCompiled() }
            .getOrDefault(false)
        return NativeState(
            bridgeCompiled = bridge,
            presentHookActive = runCatching {
                WudroidFrameGenerationNative.isPresentHookActive()
            }.getOrDefault(false),
            opticalFlowAdvertised = runCatching {
                WudroidFrameGenerationNative.isOpticalFlowAdvertised()
            }.getOrDefault(false),
            generatedFrames = runCatching {
                WudroidFrameGenerationNative.generatedFrameCount()
            }.getOrDefault(0L),
            engine = runCatching { WudroidFrameGenerationNative.engineStatus() }
                .getOrElse { "Renderer Vulkan ainda não carregado" },
        )
    }

    fun backendStatusText(config: Config): String {
        if (!config.enabled) return "Desativado"
        val state = nativeState()
        if (!state.bridgeCompiled) return "Bridge nativa não carregada"
        if (!state.presentHookActive) return "Aguardando o renderer Vulkan do jogo"
        return if (state.opticalFlowAdvertised) {
            "Ativo no Present Vulkan • VK_NV_optical_flow detectado"
        } else {
            "Ativo no Present Vulkan • interpolação temporal"
        }
    }

    fun prepareBeforeLaunch(context: Context, game: NativeGameTitles.Game): Config {
        val config = gameConfig(context, game.titleId)
        if (config.enabled) {
            // FIFO is important: the extra presents are paced by Android's display
            // rather than being dumped into an immediate/mailbox queue.
            runCatching {
                NativeSettings.setVsyncMode(NativeSettings.VSyncMode.DOUBLE_BUFFERING)
                NativeSettings.saveSettings()
            }
        }
        pushNative(config)
        return config
    }

    fun presetName(preset: Int): String = when (preset) {
        PRESET_ECO -> "Eco"
        PRESET_FLOW -> "Flow"
        PRESET_BALANCED -> "Bal"
        PRESET_BOOST -> "Boost"
        PRESET_CLEAR -> "Clear"
        PRESET_MAX -> "Max"
        else -> "Bal"
    }

    fun defaultScaleForPreset(preset: Int): Float = when (preset) {
        PRESET_ECO -> 0.30f
        PRESET_FLOW -> 0.40f
        PRESET_BALANCED -> 0.50f
        PRESET_BOOST -> 0.60f
        PRESET_CLEAR -> 0.70f
        PRESET_MAX -> 0.85f
        else -> 0.50f
    }

    private fun pushNative(config: Config) {
        runCatching {
            WudroidFrameGenerationNative.setConfig(
                config.enabled,
                config.multiplier.coerceIn(2, 4),
                config.flowScale.coerceIn(0.20f, 1.00f),
                config.preset.coerceIn(0, 5),
            )
        }
    }
}
