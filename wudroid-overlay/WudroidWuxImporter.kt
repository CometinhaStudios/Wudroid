package info.cemu.cemu

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Handler
import android.os.Looper
import android.system.ErrnoException
import android.system.Os
import androidx.documentfile.provider.DocumentFile
import com.wudcompress.android.core.WudEngine
import info.cemu.cemu.nativeinterface.NativeSettings
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.FileDescriptor
import java.io.IOException

/**
 * Wudroid 0.1.0-A importer test.
 *
 * Uses WudEngine from CometinhaStudios/WudCompressAndroid.
 * This first integration test does WUX -> verified WUD in the selected
 * library folder. The original WUX is never deleted.
 */
object WudroidWuxImporter {
    private const val PREFS = "wudroid_game_importer"
    private const val KEY_LIBRARY_TREE = "library_tree_uri"

    data class Progress(val stage: String, val percent: Int)

    data class Result(
        val success: Boolean,
        val message: String,
        val outputUri: Uri? = null,
        val outputName: String? = null,
    )

    fun rememberLibraryFolder(context: Context, uri: Uri) {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit()
            .putString(KEY_LIBRARY_TREE, uri.toString())
            .apply()
    }

    fun libraryFolderUri(context: Context): Uri? {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .getString(KEY_LIBRARY_TREE, null)
            ?.let { raw -> runCatching { Uri.parse(raw) }.getOrNull() }
            ?.let { return it }

        val existing = runCatching {
            NativeSettings.getGamesPaths().firstOrNull { it.startsWith("content://") }
        }.getOrNull()
        return existing?.let { Uri.parse(it) }
    }

    suspend fun importWuxToLibrary(
        context: Context,
        inputUri: Uri,
        libraryTreeUri: Uri,
        onProgress: (Progress) -> Unit,
    ): Result = withContext(Dispatchers.IO) {
        val resolver = context.contentResolver
        val mainHandler = Handler(Looper.getMainLooper())

        runCatching {
            resolver.takePersistableUriPermission(
                inputUri,
                Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION,
            )
        }

        val sourceDocument = DocumentFile.fromSingleUri(context, inputUri)
        val sourceName = sourceDocument?.name ?: "game.wux"
        if (!sourceName.endsWith(".wux", ignoreCase = true)) {
            return@withContext Result(false, "Selecione um arquivo .wux válido.")
        }

        val tree = DocumentFile.fromTreeUri(context, libraryTreeUri)
            ?: return@withContext Result(
                false,
                "A pasta da biblioteca não pôde ser aberta. Selecione-a novamente."
            )

        if (!tree.canWrite()) {
            return@withContext Result(false, "A pasta da biblioteca não permite gravação.")
        }

        postProgress(mainHandler, onProgress, "Validando WUX", 0)

        val inputPfd = resolver.openFileDescriptor(inputUri, "r")
            ?: return@withContext Result(false, "Não foi possível abrir o WUX.")

        inputPfd.use { sourcePfd ->
            val source = FdRandomAccess(sourcePfd.fileDescriptor, writable = false)
            val detected = WudEngine.detect(source)
            if (detected != WudEngine.MODE_WUX_TO_WUD) {
                return@withContext Result(
                    false,
                    "O arquivo não possui um cabeçalho WUX0 reconhecido pelo WudCompressMobile."
                )
            }

            val outputName = uniqueOutputName(tree, sourceName)
            val outputDocument = tree.createFile("application/octet-stream", outputName)
                ?: return@withContext Result(
                    false,
                    "Não foi possível criar o WUD na pasta escolhida."
                )

            val outputPfd = resolver.openFileDescriptor(outputDocument.uri, "rw")
            if (outputPfd == null) {
                runCatching { outputDocument.delete() }
                return@withContext Result(false, "Não foi possível abrir o WUD de destino.")
            }

            outputPfd.use { destinationPfd ->
                val destination = FdRandomAccess(destinationPfd.fileDescriptor, writable = true)
                var lastStage: WudEngine.Stage? = null
                var lastPercent = -1

                val resultCode = try {
                    WudEngine.process(
                        source,
                        destination,
                        true,
                    ) { stage, perMille ->
                        val percent = (perMille / 10).coerceIn(0, 100)
                        if (stage != lastStage || percent != lastPercent) {
                            lastStage = stage
                            lastPercent = percent
                            postProgress(
                                mainHandler,
                                onProgress,
                                stageLabel(stage),
                                percent,
                            )
                        }
                    }
                } catch (t: Throwable) {
                    runCatching { outputDocument.delete() }
                    return@withContext Result(
                        false,
                        "Falha durante a importação: ${t.javaClass.simpleName}. O WUX original foi mantido."
                    )
                }

                if (resultCode != WudEngine.OK) {
                    runCatching { outputDocument.delete() }
                    return@withContext Result(
                        false,
                        "WudCompressMobile retornou erro ${errorLabel(resultCode)}. O WUX original foi mantido."
                    )
                }

                postProgress(mainHandler, onProgress, "Concluído", 100)
                return@withContext Result(
                    true,
                    "Importação concluída e verificada.",
                    outputDocument.uri,
                    outputDocument.name ?: outputName,
                )
            }
        }
    }

    fun deleteOriginalWux(context: Context, inputUri: Uri): Boolean {
        val resolver = context.contentResolver
        return runCatching {
            val document = DocumentFile.fromSingleUri(context, inputUri)
            if (document != null && document.exists()) {
                document.delete()
            } else {
                resolver.delete(inputUri, null, null) > 0
            }
        }.getOrDefault(false)
    }

    private fun uniqueOutputName(tree: DocumentFile, inputName: String): String {
        val base = inputName.substringBeforeLast('.', inputName).ifBlank { "game" }
        var candidate = "$base.wud"
        var index = 1
        while (tree.findFile(candidate) != null) {
            candidate = "${base}_$index.wud"
            index++
        }
        return candidate
    }

    private fun postProgress(
        handler: Handler,
        callback: (Progress) -> Unit,
        stage: String,
        percent: Int,
    ) {
        handler.post { callback(Progress(stage, percent)) }
    }

    private fun stageLabel(stage: WudEngine.Stage): String = when (stage) {
        WudEngine.Stage.READING -> "Lendo WUX"
        WudEngine.Stage.COMPRESSING -> "Compactando"
        WudEngine.Stage.DECOMPRESSING -> "Convertendo WUX para WUD"
        WudEngine.Stage.VERIFYING -> "Verificando arquivo"
        WudEngine.Stage.DONE -> "Concluído"
    }

    private fun errorLabel(code: Int): String = when (code) {
        WudEngine.ERR_INPUT -> "de entrada"
        WudEngine.ERR_NOT_SEEKABLE -> "de acesso aleatório"
        WudEngine.ERR_OUTPUT -> "de saída"
        WudEngine.ERR_IO -> "de leitura/gravação"
        WudEngine.ERR_VERIFY -> "na verificação"
        WudEngine.ERR_MEMORY -> "de memória"
        WudEngine.ERR_FORMAT -> "de formato"
        else -> code.toString()
    }

    private class FdRandomAccess(
        private val fd: FileDescriptor,
        private val writable: Boolean,
    ) : WudEngine.RandomAccessFileLike {
        override fun size(): Long = try {
            Os.fstat(fd).st_size
        } catch (e: ErrnoException) {
            throw IOException(e.message, e)
        }

        override fun read(
            position: Long,
            buffer: ByteArray,
            offset: Int,
            length: Int,
        ): Int = try {
            Os.pread(fd, buffer, offset, length, position)
        } catch (e: ErrnoException) {
            throw IOException(e.message, e)
        }

        override fun write(
            position: Long,
            buffer: ByteArray,
            offset: Int,
            length: Int,
        ) {
            if (!writable) throw IOException("File is read-only")
            var done = 0
            while (done < length) {
                try {
                    val written = Os.pwrite(
                        fd,
                        buffer,
                        offset + done,
                        length - done,
                        position + done,
                    )
                    if (written <= 0) throw IOException("Short write")
                    done += written
                } catch (e: ErrnoException) {
                    throw IOException(e.message, e)
                }
            }
        }

        override fun truncate(size: Long) {
            if (!writable) throw IOException("File is read-only")
            try {
                Os.ftruncate(fd, size)
            } catch (e: ErrnoException) {
                throw IOException(e.message, e)
            }
        }

        override fun force() {
            if (!writable) return
            try {
                Os.fsync(fd)
            } catch (e: ErrnoException) {
                throw IOException(e.message, e)
            }
        }
    }
}
