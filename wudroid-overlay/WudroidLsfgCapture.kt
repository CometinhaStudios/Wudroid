package info.cemu.cemu

import android.app.Activity
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import com.lsfg.android.prefs.CaptureSource
import com.lsfg.android.prefs.LsfgPreferences
import com.lsfg.android.prefs.PacingPreset
import com.lsfg.android.session.LsfgForegroundService
import com.lsfg.android.ui.ProjectionRequestActivity
import java.io.File

/**
 * Starts the real LSFG Android capture/overlay pipeline from inside Wudroid.
 *
 * We intentionally use the proven MediaProjection -> AHardwareBuffer -> LSFG
 * path instead of pretending the old JNI bridge is already connected to
 * Cemu's VkSwapchain. This keeps the work inside the Wudroid process while
 * the LSFG library owns its Vulkan frame-generation device and output overlay.
 */
object WudroidLsfgCaptureController {
    private const val PREFS = "wudroid_lsfg_capture"
    private const val KEY_PENDING = "pending"
    private const val KEY_REQUEST_STARTED = "request_started"
    private const val KEY_OVERLAY_SETTINGS_OPENED = "overlay_settings_opened"

    private fun prefs(context: Context) =
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)

    fun shadersReady(context: Context): Boolean {
        val cache = File(context.filesDir, "spirv")
        val upstreamReady = runCatching { LsfgPreferences(context).load().shadersReady }
            .getOrDefault(false)
        return upstreamReady && cache.isDirectory &&
            cache.walkTopDown().any { it.isFile && it.extension.equals("spv", ignoreCase = true) }
    }

    fun syncLsfgPreferences(
        context: Context,
        config: WudroidFrameGenerationManager.Config,
    ) {
        val p = LsfgPreferences(context)
        val resolvedMultiplier = when (config.targetFps) {
            WudroidFrameGenerationManager.TARGET_FIXED_MULTIPLIER -> config.multiplier
            in 1..60 -> 2
            in 61..90 -> 3
            else -> 4
        }.coerceIn(2, 4)

        p.setLsfgEnabled(config.enabled)
        p.setMultiplier(resolvedMultiplier)
        p.setTargetFpsCap(
            if (config.targetFps == WudroidFrameGenerationManager.TARGET_FIXED_MULTIPLIER) {
                0
            } else {
                config.targetFps
            }
        )
        p.setTargetPackage(context.packageName)
        p.setCaptureSource(CaptureSource.MEDIA_PROJECTION)
        p.setFpsCounterEnabled(true)
        p.setFrameGraphEnabled(false)
        p.setPerformance(true)
        p.setHdr(false)

        when (config.queueTarget) {
            WudroidFrameGenerationManager.QUEUE_LOWEST_LATENCY -> {
                p.setPacingPreset(PacingPreset.LOW_LATENCY)
                p.setQueueDepth(2)
            }
            WudroidFrameGenerationManager.QUEUE_SMOOTHEST -> {
                p.setPacingPreset(PacingPreset.SMOOTH)
                p.setQueueDepth(6)
            }
            else -> {
                p.setPacingPreset(PacingPreset.BALANCED)
                p.setQueueDepth(4)
            }
        }

        val cache = File(context.filesDir, "spirv").absolutePath
        val fp16Usable = config.halfPrecisionShaders && runCatching {
            com.lsfg.android.session.NativeBridge.isFramegenFp16Supported(cache)
        }.getOrDefault(false)
        p.setFramegenFp16(fp16Usable)
    }

    fun armForNextLaunch(
        context: Context,
        config: WudroidFrameGenerationManager.Config,
    ) {
        if (!config.enabled || !shadersReady(context)) {
            disarm(context, stopRunning = !config.enabled)
            return
        }
        syncLsfgPreferences(context, config)
        prefs(context).edit()
            .putBoolean(KEY_PENDING, true)
            .putBoolean(KEY_REQUEST_STARTED, false)
            .putBoolean(KEY_OVERLAY_SETTINGS_OPENED, false)
            .apply()
    }

    fun disarm(context: Context, stopRunning: Boolean = false) {
        prefs(context).edit()
            .putBoolean(KEY_PENDING, false)
            .putBoolean(KEY_REQUEST_STARTED, false)
            .putBoolean(KEY_OVERLAY_SETTINGS_OPENED, false)
            .apply()
        if (stopRunning) {
            runCatching { context.stopService(Intent(context, LsfgForegroundService::class.java)) }
        }
    }

    /**
     * Called from EmulationActivity.onResume(). The first pass may only open
     * Android's overlay-permission screen. When the activity resumes again,
     * it proceeds to the MediaProjection consent dialog.
     */
    fun maybeStartForEmulation(activity: Activity) {
        val p = prefs(activity)
        if (!p.getBoolean(KEY_PENDING, false)) return
        if (!shadersReady(activity)) {
            disarm(activity)
            return
        }

        if (!Settings.canDrawOverlays(activity)) {
            if (!p.getBoolean(KEY_OVERLAY_SETTINGS_OPENED, false)) {
                p.edit().putBoolean(KEY_OVERLAY_SETTINGS_OPENED, true).apply()
                val intent = Intent(
                    Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                    Uri.parse("package:${activity.packageName}"),
                )
                runCatching { activity.startActivity(intent) }
            }
            return
        }

        if (p.getBoolean(KEY_REQUEST_STARTED, false)) return
        p.edit().putBoolean(KEY_REQUEST_STARTED, true).apply()

        // Give Cemu a moment to create its game surface before the projection
        // prompt takes focus. This avoids starting capture against the launcher.
        Handler(Looper.getMainLooper()).postDelayed({
            if (activity.isFinishing || activity.isDestroyed) return@postDelayed
            runCatching {
                activity.startActivity(
                    ProjectionRequestActivity.buildIntent(
                        activity,
                        activity.packageName,
                    )
                )
            }.onFailure {
                // Let a later onResume retry instead of permanently wedging FG.
                prefs(activity).edit().putBoolean(KEY_REQUEST_STARTED, false).apply()
            }
        }, 900L)
    }
}
