package info.cemu.cemu

import android.content.Context
import android.net.Uri
import android.provider.OpenableColumns
import com.lsfg.android.prefs.LsfgPreferences
import com.lsfg.android.session.NativeBridge
import info.cemu.cemu.nativeinterface.NativeGameTitles
import info.cemu.cemu.nativeinterface.NativeSettings
import java.io.File
import java.io.RandomAccessFile
import java.security.MessageDigest

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

    data class NativeState(
        val bridgeCompiled: Boolean,
        val ahbSupported: Boolean,
        val engine: String,
    ) {
        val realLsfgBackendLoaded: Boolean
            get() = bridgeCompiled && engine.contains("lsfg", ignoreCase = true)
    }

    private fun prefs(context: Context) =
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)

    private fun gamePrefix(titleId: Long) =
        "game_${java.lang.Long.toUnsignedString(titleId, 16)}_"

    private fun dllFile(context: Context): File =
        File(context.filesDir, "$DLL_DIR/$DLL_NAME")

    private fun shaderDir(context: Context): File = File(context.filesDir, "spirv")

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

    fun shadersReady(context: Context): Boolean =
        WudroidLsfgCaptureController.shadersReady(context)

    fun losslessDllInfo(context: Context): String {
        val file = dllFile(context)
        if (!file.isFile) return "Lossless.dll não importado"
        val mb = file.length().toDouble() / 1024.0 / 1024.0
        return if (shadersReady(context)) {
            "Lossless.dll • %.1f MB • shaders preparados".format(mb)
        } else {
            "Lossless.dll • %.1f MB • shaders ainda não preparados".format(mb)
        }
    }

    fun nativeState(): NativeState {
        val engine = runCatching { NativeBridge.nativeVersion() }
            .getOrElse { "LSFG Android indisponível: ${it.javaClass.simpleName}" }
        val bridge = !engine.contains("indisponível", ignoreCase = true)
        val ahb = runCatching {
            WudroidFrameGenerationNative.hasAhardwareBufferSupport()
        }.getOrDefault(false)
        return NativeState(bridge, ahb, engine)
    }

    fun backendStatusText(context: Context, config: Config): String {
        if (!config.enabled) return "Desativado"
        if (!hasLosslessDll(context)) return "Aguardando Lossless.dll"
        if (!shadersReady(context)) return "DLL importada • preparando shaders LSFG"

        val state = nativeState()
        if (!state.bridgeCompiled) return "Backend LSFG Android não carregado"
        if (!state.ahbSupported) return "AHardwareBuffer GPU não suportado"
        if (!state.realLsfgBackendLoaded) return "liblsfg-android não carregada"

        return "Pronto • inicia captura LSFG ao abrir o jogo"
    }

    /**
     * Copies the user's DLL to private app storage, then uses the real LSFG
     * Android native extractor to translate its DXBC resources to SPIR-V.
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

        val cache = shaderDir(context)
        cache.mkdirs()
        val sha256 = sha256(target)
        val upstreamPrefs = LsfgPreferences(context)
        upstreamPrefs.setDll(uri.toString(), name ?: DLL_NAME)
        upstreamPrefs.setShadersReady(false)

        val extractRc = NativeBridge.extractShaders(
            target.absolutePath,
            sha256,
            cache.absolutePath,
        )
        if (extractRc != 0) {
            error("Falha ao extrair shaders LSFG (código $extractRc)")
        }

        val probeRc = NativeBridge.probeShaders(cache.absolutePath)
        if (probeRc != 0) {
            error("Shaders extraídos, mas o Vulkan recusou o cache (código $probeRc)")
        }

        upstreamPrefs.setShadersReady(true)
        losslessDllInfo(context)
    }

    fun removeLosslessDll(context: Context): Boolean {
        WudroidLsfgCaptureController.disarm(context, stopRunning = true)
        runCatching { LsfgPreferences(context).setShadersReady(false) }
        runCatching { shaderDir(context).deleteRecursively() }
        val file = dllFile(context)
        return !file.exists() || file.delete()
    }

    /**
     * Arms the LSFG capture backend for the EmulationActivity that is about to
     * start. EmulationActivity requests overlay + MediaProjection permissions
     * after Cemu has created the game surface.
     */
    fun prepareBeforeLaunch(
        context: Context,
        game: NativeGameTitles.Game,
    ): Config {
        val config = gameConfig(context, game.titleId)
        if (config.enabled && shadersReady(context)) {
            runCatching {
                NativeSettings.setVsyncMode(NativeSettings.VSyncMode.DOUBLE_BUFFERING)
                NativeSettings.saveSettings()
            }
            WudroidLsfgCaptureController.armForNextLaunch(context, config)
        } else {
            WudroidLsfgCaptureController.disarm(context, stopRunning = !config.enabled)
        }
        return config
    }

    private fun sha256(file: File): String {
        val digest = MessageDigest.getInstance("SHA-256")
        file.inputStream().use { input ->
            val buffer = ByteArray(1024 * 1024)
            while (true) {
                val read = input.read(buffer)
                if (read <= 0) break
                digest.update(buffer, 0, read)
            }
        }
        return digest.digest().joinToString("") { "%02x".format(it) }
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

            if (peOffset <= 0 || peOffset.toLong() + 24L > raf.length()) return@use false
            raf.seek(peOffset.toLong())
            if (raf.readUnsignedByte() != 'P'.code ||
                raf.readUnsignedByte() != 'E'.code ||
                raf.readUnsignedByte() != 0 ||
                raf.readUnsignedByte() != 0
            ) {
                return@use false
            }

            val machine = raf.readUnsignedByte() or (raf.readUnsignedByte() shl 8)
            machine != 0
        }
    }.getOrDefault(false)
}
