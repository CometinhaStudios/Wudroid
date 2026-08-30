package info.cemu.cemu

import android.content.Context
import info.cemu.cemu.nativeinterface.NativeGameTitles

object WudroidFrameGenerationManager {
    private const val PREFS = "wudroid_frame_generation"
    const val TARGET_FIXED_MULTIPLIER = 0
    const val QUEUE_LOWEST_LATENCY = 0
    const val QUEUE_BALANCED = 1
    const val QUEUE_SMOOTHEST = 2

    data class Config(
        val enabled: Boolean = false,
        val useGlobal: Boolean = false,
        val targetFps: Int = TARGET_FIXED_MULTIPLIER,
        val multiplier: Int = 2,
        val queueTarget: Int = QUEUE_BALANCED,
        val matchMotionToGame: Boolean = true,
        val halfPrecisionShaders: Boolean = true,
    )

    private fun prefs(context: Context) = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
    private fun gamePrefix(titleId: Long) = "game_${java.lang.Long.toUnsignedString(titleId, 16)}_"

    fun globalConfig(context: Context): Config = Config(enabled = false)

    fun gameConfig(context: Context, titleId: Long): Config {
        val p = prefs(context)
        val prefix = gamePrefix(titleId)
        return Config(
            enabled = false,
            useGlobal = p.getBoolean("${prefix}use_global", false),
            targetFps = p.getInt("${prefix}target_fps", TARGET_FIXED_MULTIPLIER),
            multiplier = p.getInt("${prefix}multiplier", 2).coerceIn(2, 4),
            queueTarget = p.getInt("${prefix}queue", QUEUE_BALANCED).coerceIn(0, 2),
            matchMotionToGame = p.getBoolean("${prefix}match_motion", true),
            halfPrecisionShaders = p.getBoolean("${prefix}fp16", true),
        )
    }

    fun saveGameConfig(context: Context, titleId: Long, config: Config) {
        val prefix = gamePrefix(titleId)
        prefs(context).edit()
            .putBoolean("${prefix}enabled", false)
            .putBoolean("${prefix}use_global", config.useGlobal)
            .putInt("${prefix}target_fps", config.targetFps)
            .putInt("${prefix}multiplier", config.multiplier.coerceIn(2, 4))
            .putInt("${prefix}queue", config.queueTarget.coerceIn(0, 2))
            .putBoolean("${prefix}match_motion", config.matchMotionToGame)
            .putBoolean("${prefix}fp16", config.halfPrecisionShaders)
            .apply()
    }

    fun useGlobalForGame(context: Context, titleId: Long) {
        prefs(context).edit().putBoolean("${gamePrefix(titleId)}use_global", true).apply()
    }

    fun hasLosslessDll(context: Context): Boolean = false

    fun prepareBeforeLaunch(context: Context, game: NativeGameTitles.Game): Config =
        gameConfig(context, game.titleId).copy(enabled = false)
}
