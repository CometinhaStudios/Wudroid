package info.cemu.cemu.graphics

import android.content.Context
import android.content.Intent
import android.os.Build
import android.system.Os
import info.cemu.cemu.nativeinterface.NativeSettings
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * Wudroid Vulkan X v0.1
 *
 * First experimental graphics path for Wudroid. It deliberately keeps Cemu's
 * Latte translation intact and switches on a separate Android/Vulkan runtime
 * policy in the native renderer through WUDROID_VULKAN_X.
 */
object WudroidVulkanX {
    private const val EXTRA_GRAPHICS_ENGINE = "wudroid.graphics_engine"
    private const val ENGINE_WUDROID_VULKAN_X = 1
    private const val ENV_VULKAN_X = "WUDROID_VULKAN_X"

    private const val DIR_NAME = "wudroid-vulkanx"
    private const val LOG_NAME = "latest-session.txt"
    private const val MARKER_NAME = "session-active.marker"

    fun prepare(context: Context, intent: Intent, gamePath: String): Boolean {
        val active = intent.getIntExtra(EXTRA_GRAPHICS_ENGINE, 0) == ENGINE_WUDROID_VULKAN_X

        try {
            Os.setenv(ENV_VULKAN_X, if (active) "1" else "0", true)
        } catch (_: Throwable) {
            // Native renderer will simply stay on the standard path if setenv fails.
        }

        if (!active) return false

        val dir = sessionDir(context)
        dir.mkdirs()
        val marker = File(dir, MARKER_NAME)
        val log = File(dir, LOG_NAME)

        val now = timestamp()
        val gameLabel = runCatching {
            if (gamePath.startsWith("content://")) "content-uri" else File(gamePath).name
        }.getOrDefault("unknown")

        val asyncCompile = runCatching { NativeSettings.getAsyncShaderCompile() }.getOrNull()
        val accurateBarriers = runCatching { NativeSettings.getAccurateBarriers() }.getOrNull()
        val vsync = runCatching { NativeSettings.getVsyncMode() }.getOrNull()
        val customDriver = runCatching { NativeSettings.getCustomDriverPath() }.getOrNull()

        log.writeText(
            buildString {
                appendLine("Wudroid Vulkan X v0.1")
                appendLine("session_start=$now")
                appendLine("device=${Build.MANUFACTURER} ${Build.MODEL}")
                if (Build.VERSION.SDK_INT >= 31) appendLine("soc=${Build.SOC_MANUFACTURER} ${Build.SOC_MODEL}")
                appendLine("android=${Build.VERSION.RELEASE} api=${Build.VERSION.SDK_INT}")
                appendLine("abi=${Build.SUPPORTED_ABIS.joinToString()}")
                appendLine("game=$gameLabel")
                appendLine("async_shader_compile=$asyncCompile")
                appendLine("accurate_barriers=$accurateBarriers")
                appendLine("vsync_mode=$vsync")
                appendLine("custom_driver=${if (customDriver.isNullOrBlank()) "system" else "custom"}")
                appendLine("policy=pipeline_safe_scheduler_v0_1")
                appendLine("stage=prepare")
            }
        )
        marker.writeText(now)
        return true
    }

    fun markStage(context: Context, stage: String) {
        val log = File(sessionDir(context), LOG_NAME)
        if (!log.exists()) return
        runCatching { log.appendText("${timestamp()} stage=$stage\n") }
    }

    fun cleanExit(context: Context) {
        markStage(context, "clean_exit")
        runCatching { File(sessionDir(context), MARKER_NAME).delete() }
    }

    /**
     * If a native crash killed the emulation process, the marker survives.
     * We keep the log and remove only the marker so the next test can start.
     */
    fun recoverPreviousSession(context: Context): Boolean {
        val dir = sessionDir(context)
        val marker = File(dir, MARKER_NAME)
        if (!marker.exists()) return false

        val log = File(dir, LOG_NAME)
        runCatching {
            log.appendText("${timestamp()} stage=previous_session_unclean\n")
            marker.delete()
        }
        return true
    }

    private fun sessionDir(context: Context) = File(context.filesDir, DIR_NAME)

    private fun timestamp(): String =
        SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSSZ", Locale.US).format(Date())
}
