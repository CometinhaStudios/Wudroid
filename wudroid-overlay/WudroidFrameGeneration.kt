package info.cemu.cemu

import android.content.Context
import android.net.Uri
import android.provider.OpenableColumns
import info.cemu.cemu.nativeinterface.NativeGameTitles
import info.cemu.cemu.nativeinterface.NativeSettings
import java.io.File
import java.io.RandomAccessFile

object WudroidFrameGenerationManager {
    private const val PREFS = "wudroid_frame_generation"
    private const val DLL_DIR = "wudroid/lsfg"
    private const val DLL_NAME = "Lossless.dll"

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

    private fun prefs(context: Context) =
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)

    private fun gamePrefix(titleId: Long) = "game_${java.lang.Long.toUnsignedString(titleId, 16)}_"

    private fun dllFile(context: Context): File =
        File(context.filesDir, "$DLL_DIR/$DLL_NAME")

    fun globalConfig(context: Context): Config {
        val p = prefs(context)
        return Config(
            enabled = p.getBoolean("global_enabled", false),
            useGlobal = false,
            targetFps = p.getInt("global_target_fps", TARGET_FIXED_MULTIPLIER),
            multiplier = p.getInt("global_multiplier", 2).coerceIn(2, 4),
            queueTarget = p.getInt("global_queue", QUEUE_BALANCED).coerceIn(0, 2),
            matchMotionToGame = p.getBoolean("global_match_motion", true),
            halfPrecisionShaders = p.getBoolean("global_fp16", true),
        )
    }

    fun gameConfig(context: Context, titleId: Long): Config {
        val p = prefs(context)
        val prefix = gamePrefix(titleId)
        val useGlobal = p.getBoolean("${prefix}use_global", false)
        if (useGlobal) return globalConfig(context).copy(useGlobal = true)

        return Config(
            enabled = p.getBoolean("${prefix}enabled", false),
            useGlobal = false,
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
            .putBoolean("${prefix}use_global", config.useGlobal)
            .putBoolean("${prefix}enabled", config.enabled)
            .putInt("${prefix}target_fps", config.targetFps)
            .putInt("${prefix}multiplier", config.multiplier.coerceIn(2, 4))
            .putInt("${prefix}queue", config.queueTarget.coerceIn(0, 2))
            .putBoolean("${prefix}match_motion", config.matchMotionToGame)
            .putBoolean("${prefix}fp16", config.halfPrecisionShaders)
            .apply()
    }

    fun useGlobalForGame(context: Context, titleId: Long) {
        val prefix = gamePrefix(titleId)
        prefs(context).edit().putBoolean("${prefix}use_global", true).apply()
    }

    fun hasLosslessDll(context: Context): Boolean =
        dllFile(context).let { it.isFile && it.length() > 0L }

    fun losslessDllInfo(context: Context): String {
        val file = dllFile(context)
        if (!file.isFile) return "Lossless.dll não importado"
        val mb = file.length().toDouble() / 1024.0 / 1024.0
        return "Lossless.dll • %.1f MB".format(mb)
    }

    /**
     * Copies a user-supplied Lossless.dll into private app storage.
     * The original file selected by the user is never modified or deleted.
     *
     * This validates the DOS MZ header and PE signature before accepting it.
     */
    fun importLosslessDll(context: Context, uri: Uri): Result<String> = runCatching {
        val name = queryDisplayName(context, uri)
        if (name != null && !name.endsWith(".dll", ignoreCase = true)) {
            error("Selecione um arquivo .dll")
        }

        val target = dllFile(context)
        target.parentFile?.mkdirs()
        val temp = File(target.parentFile, "$DLL_NAME.importing")
        temp.delete()

        context.contentResolver.openInputStream(uri)?.use { input ->
            temp.outputStream().use { output ->
                input.copyTo(output, bufferSize = 1024 * 1024)
            }
        } ?: error("Não foi possível abrir o arquivo")

        if (temp.length() < 1024L) {
            temp.delete()
            error("Arquivo DLL pequeno ou inválido")
        }

        if (!isPortableExecutable(temp)) {
            temp.delete()
            error("O arquivo não parece ser uma DLL/PE válida")
        }

        if (target.exists() && !target.delete()) {
            temp.delete()
            error("Não foi possível substituir a DLL anterior")
        }

        if (!temp.renameTo(target)) {
            temp.copyTo(target, overwrite = true)
            temp.delete()
        }

        losslessDllInfo(context)
    }

    fun removeLosslessDll(context: Context): Boolean =
        dllFile(context).let { !it.exists() || it.delete() }

    /**
     * Test-1 launch preparation.
     *
     * The settings are real and persisted now. If frame generation is enabled
     * and the DLL is installed, Wudroid forces FIFO-style VSync before boot,
     * matching the requirement of the LSFG presentation path.
     *
     * Native interpolation is wired in the next renderer stage; this method
     * intentionally does not pretend generated frames already exist.
     */
    fun prepareBeforeLaunch(
        context: Context,
        game: NativeGameTitles.Game,
    ): Config {
        val config = gameConfig(context, game.titleId)
        if (config.enabled && hasLosslessDll(context)) {
            runCatching {
                NativeSettings.setVsyncMode(NativeSettings.VSyncMode.DOUBLE_BUFFERING)
                NativeSettings.saveSettings()
            }
        }
        return config
    }

    private fun queryDisplayName(context: Context, uri: Uri): String? =
        runCatching {
            context.contentResolver.query(
                uri,
                arrayOf(OpenableColumns.DISPLAY_NAME),
                null,
                null,
                null,
            )?.use { cursor ->
                if (!cursor.moveToFirst()) return@use null
                val index = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                if (index < 0) null else cursor.getString(index)
            }
        }.getOrNull()

    private fun isPortableExecutable(file: File): Boolean = runCatching {
        RandomAccessFile(file, "r").use { raf ->
            if (raf.length() < 64L) return@use false
            if (raf.readUnsignedByte() != 'M'.code) return@use false
            if (raf.readUnsignedByte() != 'Z'.code) return@use false

            raf.seek(0x3CL)
            val peOffset =
                (raf.readUnsignedByte()) or
                (raf.readUnsignedByte() shl 8) or
                (raf.readUnsignedByte() shl 16) or
                (raf.readUnsignedByte() shl 24)

            if (peOffset <= 0 || peOffset.toLong() + 4L > raf.length()) return@use false
            raf.seek(peOffset.toLong())
            raf.readUnsignedByte() == 'P'.code &&
                raf.readUnsignedByte() == 'E'.code &&
                raf.readUnsignedByte() == 0 &&
                raf.readUnsignedByte() == 0
        }
    }.getOrDefault(false)
}
