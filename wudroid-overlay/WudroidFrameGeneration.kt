package info.cemu.cemu

import android.content.Context
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import info.cemu.cemu.nativeinterface.NativeGameTitles
import java.io.File
import java.io.RandomAccessFile
import java.security.MessageDigest
import java.util.Locale

/**
 * Wudroid Frame Generation — foundation layer.
 *
 * This build intentionally does NOT claim that interpolation is active yet.
 * It implements the user-owned Lossless.dll import/validation path and the
 * per-game configuration that the native Vulkan hook will consume next.
 */
object WudroidFrameGeneration {
    private const val PREFS = "wudroid_frame_generation"
    private const val KEY_DLL_HASH = "dll_sha256"
    private const val KEY_DLL_SIZE = "dll_size"
    private const val KEY_DLL_NAME = "dll_name"

    const val MODE_OFF = 0
    const val MODE_LSFG_2X = 1

    private fun prefs(context: Context) =
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)

    private fun dir(context: Context) =
        File(context.filesDir, "wudroid/framegen").apply { mkdirs() }

    fun dllFile(context: Context) = File(dir(context), "Lossless.dll")

    fun hasDll(context: Context): Boolean {
        val file = dllFile(context)
        return file.isFile && file.length() > 1024 * 1024 && isPeDll(file)
    }

    fun dllSummary(context: Context): String {
        if (!hasDll(context)) return "Lossless.dll não importada"
        val p = prefs(context)
        val sizeMb = p.getLong(KEY_DLL_SIZE, dllFile(context).length()) / (1024.0 * 1024.0)
        val hash = p.getString(KEY_DLL_HASH, "") ?: ""
        val hashShort = if (hash.length >= 12) hash.take(12) else hash
        return String.format(
            Locale.US,
            "DLL válida • %.1f MB%s",
            sizeMb,
            if (hashShort.isNotBlank()) " • $hashShort…" else ""
        )
    }

    fun importDll(context: Context, uri: Uri): Result<String> = runCatching {
        val target = dllFile(context)
        val temp = File(target.parentFile, "Lossless.dll.importing")
        temp.delete()

        context.contentResolver.openInputStream(uri)?.use { input ->
            temp.outputStream().use { output -> input.copyTo(output, 1024 * 1024) }
        } ?: error("Não foi possível abrir o arquivo.")

        if (temp.length() < 1024 * 1024) {
            temp.delete()
            error("Arquivo pequeno demais para ser Lossless.dll.")
        }
        if (!isPeDll(temp)) {
            temp.delete()
            error("O arquivo selecionado não parece ser uma DLL PE válida.")
        }

        val hash = sha256(temp)
        if (target.exists() && !target.delete()) {
            temp.delete()
            error("Não foi possível substituir a DLL anterior.")
        }
        if (!temp.renameTo(target)) {
            temp.copyTo(target, overwrite = true)
            temp.delete()
        }

        prefs(context).edit()
            .putString(KEY_DLL_HASH, hash)
            .putLong(KEY_DLL_SIZE, target.length())
            .putString(KEY_DLL_NAME, "Lossless.dll")
            .apply()

        "Lossless.dll importada e validada."
    }

    fun removeDll(context: Context) {
        dllFile(context).delete()
        File(dir(context), "session.properties").delete()
        prefs(context).edit()
            .remove(KEY_DLL_HASH)
            .remove(KEY_DLL_SIZE)
            .remove(KEY_DLL_NAME)
            .apply()
    }

    fun getMode(context: Context, titleId: Long): Int =
        prefs(context).getInt("mode_$titleId", MODE_OFF)

    fun setMode(context: Context, titleId: Long, mode: Int) {
        prefs(context).edit().putInt("mode_$titleId", mode).apply()
    }

    /**
     * Creates a tiny private session file for the upcoming native Vulkan
     * presenter. No proprietary DLL data is copied into the repository/APK.
     */
    fun prepareForLaunch(
        context: Context,
        game: NativeGameTitles.Game,
    ) {
        val mode = getMode(context, game.titleId)
        val enabled = mode == MODE_LSFG_2X && hasDll(context)

        File(dir(context), "session.properties").writeText(
            buildString {
                appendLine("titleId=${java.lang.Long.toUnsignedString(game.titleId, 16)}")
                appendLine("enabled=$enabled")
                appendLine("multiplier=${if (enabled) 2 else 1}")
                appendLine("dll=${dllFile(context).absolutePath}")
                // Test 1 is the integration foundation only.
                appendLine("nativeHook=not_connected")
            }
        )
    }

    private fun isPeDll(file: File): Boolean = runCatching {
        RandomAccessFile(file, "r").use { raf ->
            if (raf.length() < 0x100) return@use false
            if (raf.readUnsignedByte() != 0x4D || raf.readUnsignedByte() != 0x5A) {
                return@use false
            }

            raf.seek(0x3C)
            val peOffset = Integer.reverseBytes(raf.readInt()).toLong() and 0xffffffffL
            if (peOffset <= 0L || peOffset + 4L >= raf.length()) return@use false

            raf.seek(peOffset)
            raf.readUnsignedByte() == 0x50 &&
                raf.readUnsignedByte() == 0x45 &&
                raf.readUnsignedByte() == 0x00 &&
                raf.readUnsignedByte() == 0x00
        }
    }.getOrDefault(false)

    private fun sha256(file: File): String {
        val digest = MessageDigest.getInstance("SHA-256")
        file.inputStream().use { input ->
            val buffer = ByteArray(1024 * 1024)
            while (true) {
                val count = input.read(buffer)
                if (count <= 0) break
                digest.update(buffer, 0, count)
            }
        }
        return digest.digest().joinToString("") { "%02x".format(it) }
    }
}

@Composable
fun WudroidFrameGenerationPanel() {
    val context = LocalContext.current
    var status by remember { mutableStateOf(WudroidFrameGeneration.dllSummary(context)) }
    var message by remember { mutableStateOf<String?>(null) }

    val launcher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.OpenDocument()
    ) { uri ->
        if (uri != null) {
            val result = WudroidFrameGeneration.importDll(context, uri)
            message = result.fold(
                onSuccess = { it },
                onFailure = { it.message ?: "Falha ao importar Lossless.dll." }
            )
            status = WudroidFrameGeneration.dllSummary(context)
        }
    }

    Text(
        "Frame Generation",
        color = Color(0xFF00B8F5),
        fontWeight = FontWeight.Bold,
        fontSize = 13.sp,
    )
    Spacer(Modifier.height(6.dp))

    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF15181D)),
        shape = RoundedCornerShape(15.dp),
    ) {
        Column(Modifier.padding(15.dp)) {
            Text("LSFG / Lossless Scaling", fontSize = 16.sp)
            Spacer(Modifier.height(4.dp))
            Text(
                status,
                color = if (WudroidFrameGeneration.hasDll(context))
                    Color(0xFF00B8F5) else Color(0xFF9DA8B4),
                fontSize = 13.sp,
            )
            Spacer(Modifier.height(6.dp))
            Text(
                "Use apenas sua própria Lossless.dll de uma cópia legítima do " +
                    "Lossless Scaling. A DLL não é incluída nem baixada pelo Wudroid.",
                color = Color(0xFF9DA8B4),
                fontSize = 11.sp,
            )
            Spacer(Modifier.height(10.dp))

            Button(
                modifier = Modifier.fillMaxWidth(),
                onClick = {
                    launcher.launch(arrayOf(
                        "application/x-msdownload",
                        "application/octet-stream",
                        "*/*"
                    ))
                }
            ) {
                Text(
                    if (WudroidFrameGeneration.hasDll(context))
                        "Trocar Lossless.dll" else "Importar Lossless.dll",
                    color = Color.Black,
                )
            }

            if (WudroidFrameGeneration.hasDll(context)) {
                Spacer(Modifier.height(6.dp))
                Button(
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Color(0xFF252A31)
                    ),
                    onClick = {
                        WudroidFrameGeneration.removeDll(context)
                        status = WudroidFrameGeneration.dllSummary(context)
                        message = "Lossless.dll removida."
                    }
                ) {
                    Text("Remover DLL")
                }
            }

            if (message != null) {
                Spacer(Modifier.height(8.dp))
                Text(message!!, color = Color(0xFF9DA8B4), fontSize = 11.sp)
            }

            Spacer(Modifier.height(8.dp))
            Text(
                "Foundation 1: importação/validação e perfil por jogo. " +
                    "O hook Vulkan de interpolação ainda não está conectado nesta build.",
                color = Color(0xFFFFB74D),
                fontSize = 11.sp,
            )
        }
    }

    Spacer(Modifier.height(8.dp))
}
