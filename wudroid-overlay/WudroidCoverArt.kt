package info.cemu.cemu

import android.content.Context
import android.graphics.BitmapFactory
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import info.cemu.cemu.nativeinterface.NativeGameTitles
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import java.text.Normalizer
import java.util.Locale

@Composable
fun WudroidGameCover(
    game: NativeGameTitles.Game,
    modifier: Modifier = Modifier,
) {
    val context = LocalContext.current
    var cover by remember(game.titleId, game.name, game.region) {
        mutableStateOf<ImageBitmap?>(null)
    }

    LaunchedEffect(game.titleId, game.name, game.region) {
        cover = WudroidCoverArtRepository.loadCover(context, game)
    }

    Box(
        modifier = modifier
            .clip(RoundedCornerShape(12.dp))
            .background(Color(0xFF101820)),
        contentAlignment = Alignment.Center
    ) {
        when {
            cover != null -> {
                Image(
                    bitmap = cover!!,
                    contentDescription = game.name,
                    modifier = Modifier.fillMaxSize(),
                    contentScale = ContentScale.Fit,
                )
            }
            game.icon != null -> {
                Image(
                    bitmap = game.icon!!,
                    contentDescription = game.name,
                    modifier = Modifier.fillMaxSize(),
                    contentScale = ContentScale.Crop,
                )
            }
            else -> {
                // Keep this fallback self-contained. WudroidIcon/WIcon are
                // private to MainActivity.kt and cannot be referenced here.
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center,
                ) {
                    androidx.compose.material3.Text(
                        text = "W",
                        color = Color(0xFF00B8F5),
                    )
                }
            }
        }
    }
}

object WudroidCoverArtRepository {
    private const val DB_URL_PRIMARY =
        "https://www.gametdb.com/wiiutdb.txt?LANG=EN"
    private const val DB_URL_FALLBACK =
        "https://www.gametdb.com/WiiU/wiiutdb.txt?LANG=EN"

    private val databaseMutex = Mutex()

    @Volatile
    private var databaseEntries: List<Pair<String, String>>? = null

    suspend fun loadCover(
        context: Context,
        game: NativeGameTitles.Game,
    ): ImageBitmap? = withContext(Dispatchers.IO) {
        val coverDir = File(context.filesDir, "wudroid/boxart").apply { mkdirs() }
        val titleKey = java.lang.Long.toUnsignedString(game.titleId, 16)
            .uppercase(Locale.ROOT)
            .padStart(16, '0')
        val cached = File(coverDir, "$titleKey.img")

        decode(cached)?.let { return@withContext it }

        val gameTdbId = resolveGameTdbId(context, game) ?: return@withContext null
        val regions = artworkRegions(gameTdbId, game.region)

        val urls = buildList {
            for (region in regions) {
                add("https://art.gametdb.com/wiiu/cover3D/$region/$gameTdbId.png")
                add("https://art.gametdb.com/wiiu/cover3D/$region/$gameTdbId.jpg")
                add("https://art.gametdb.com/wiiu/cover/$region/$gameTdbId.png")
                add("https://art.gametdb.com/wiiu/cover/$region/$gameTdbId.jpg")
                add("https://art.gametdb.com/wiiu/coverHQ/$region/$gameTdbId.jpg")
            }
        }

        for (url in urls) {
            val bytes = downloadBytes(url) ?: continue
            val bitmap = BitmapFactory.decodeByteArray(bytes, 0, bytes.size) ?: continue
            runCatching { cached.writeBytes(bytes) }
            return@withContext bitmap.asImageBitmap()
        }

        null
    }

    private fun decode(file: File): ImageBitmap? {
        if (!file.isFile || file.length() <= 0L) return null
        return runCatching {
            BitmapFactory.decodeFile(file.absolutePath)?.asImageBitmap()
        }.getOrNull()
    }

    private suspend fun resolveGameTdbId(
        context: Context,
        game: NativeGameTitles.Game,
    ): String? {
        Regex("""\[([A-Za-z0-9]{4,6})]""")
            .find(game.path)
            ?.groupValues
            ?.getOrNull(1)
            ?.uppercase(Locale.ROOT)
            ?.let { if (it.length in 4..6) return it }

        val normalizedName = normalize(game.name ?: return null)
        if (normalizedName.isBlank()) return null

        val mappingPrefs =
            context.getSharedPreferences("wudroid_boxart_ids", Context.MODE_PRIVATE)
        mappingPrefs.getString(normalizedName, null)?.let { return it }

        val known = knownCandidates(normalizedName)
        chooseRegionCandidate(known, game.region)?.let { id ->
            mappingPrefs.edit().putString(normalizedName, id).apply()
            return id
        }

        val entries = getDatabase(context)
        if (entries.isEmpty()) return null

        val exact = entries.filter { (_, title) -> normalize(title) == normalizedName }
        val candidates = if (exact.isNotEmpty()) {
            exact
        } else {
            entries.filter { (_, title) ->
                val normalizedTitle = normalize(title)
                normalizedTitle.contains(normalizedName) ||
                    normalizedName.contains(normalizedTitle)
            }.take(16)
        }

        val id = chooseRegionCandidate(candidates.map { it.first }, game.region)
            ?: candidates.firstOrNull()?.first

        if (id != null) {
            mappingPrefs.edit().putString(normalizedName, id).apply()
        }
        return id
    }

    private suspend fun getDatabase(context: Context): List<Pair<String, String>> =
        databaseMutex.withLock {
            databaseEntries?.let { return@withLock it }

            val dbDir = File(context.filesDir, "wudroid/boxart").apply { mkdirs() }
            val dbFile = File(dbDir, "wiiutdb_en.txt")

            val text =
                if (dbFile.isFile && dbFile.length() > 128L) {
                    runCatching { dbFile.readText() }.getOrNull()
                } else {
                    val downloaded =
                        downloadText(DB_URL_PRIMARY)
                            ?: downloadText(DB_URL_FALLBACK)
                    if (downloaded != null) {
                        runCatching { dbFile.writeText(downloaded) }
                    }
                    downloaded
                }

            val parsed = text.orEmpty()
                .lineSequence()
                .mapNotNull { raw ->
                    val line = raw.removePrefix("\uFEFF").trim()
                    val parts = line.split(" = ", limit = 2)
                    if (parts.size != 2) return@mapNotNull null
                    val id = parts[0].trim().uppercase(Locale.ROOT)
                    val title = parts[1].trim()
                    if (id.length !in 4..6 || title.isBlank()) null else id to title
                }
                .toList()

            databaseEntries = parsed
            parsed
        }

    private fun knownCandidates(normalizedName: String): List<String> = when (normalizedName) {
        "new super mario bros u" -> listOf("ARPE01", "ARPP01")
        "new super luigi u" -> listOf("ARSE01", "ARSP01", "ARSJ01")
        "new super mario bros u new super luigi u" -> listOf("ATWE01", "ATWP01")
        "mario kart 8" -> listOf("AMKE01", "AMKP01", "AMKJ01")
        "super mario 3d world" -> listOf("ARDE01", "ARDP01")
        else -> emptyList()
    }

    private fun chooseRegionCandidate(
        candidates: List<String>,
        cemuRegion: Int,
    ): String? {
        if (candidates.isEmpty()) return null
        val desired = when {
            cemuRegion and NativeGameTitles.ConsoleRegion.USA != 0 -> 'E'
            cemuRegion and NativeGameTitles.ConsoleRegion.EUR != 0 -> 'P'
            cemuRegion and NativeGameTitles.ConsoleRegion.JPN != 0 -> 'J'
            else -> null
        }

        if (desired != null) {
            candidates.firstOrNull { id ->
                id.length >= 4 && id[3].uppercaseChar() == desired
            }?.let { return it }
        }
        return candidates.firstOrNull()
    }

    private fun artworkRegions(gameId: String, cemuRegion: Int): List<String> {
        val fromId = gameId.getOrNull(3)?.uppercaseChar()
        val primary = when (fromId) {
            'E' -> "US"
            'P' -> "EN"
            'J' -> "JA"
            else -> when {
                cemuRegion and NativeGameTitles.ConsoleRegion.USA != 0 -> "US"
                cemuRegion and NativeGameTitles.ConsoleRegion.EUR != 0 -> "EN"
                cemuRegion and NativeGameTitles.ConsoleRegion.JPN != 0 -> "JA"
                else -> "US"
            }
        }
        return listOf(primary, "US", "EN", "JA").distinct()
    }

    private fun normalize(text: String): String {
        val decomposed = Normalizer.normalize(text, Normalizer.Form.NFD)
        return decomposed
            .replace(Regex("""\p{Mn}+"""), "")
            .replace("™", "")
            .replace("®", "")
            .replace("&", " and ")
            .lowercase(Locale.ROOT)
            .replace(Regex("""[^a-z0-9]+"""), " ")
            .trim()
            .replace(Regex("""\s+"""), " ")
    }

    private fun downloadText(url: String): String? =
        downloadBytes(url)?.toString(Charsets.UTF_8)

    private fun downloadBytes(url: String): ByteArray? {
        val connection = runCatching {
            (URL(url).openConnection() as HttpURLConnection).apply {
                connectTimeout = 5000
                readTimeout = 7000
                instanceFollowRedirects = true
                requestMethod = "GET"
                setRequestProperty(
                    "User-Agent",
                    "Wudroid/0.0.9 (GameTDB artwork client)"
                )
                setRequestProperty("Accept", "image/*,text/plain,*/*")
            }
        }.getOrNull() ?: return null

        return try {
            val code = connection.responseCode
            if (code !in 200..299) return null
            connection.inputStream.use { it.readBytes() }
        } catch (_: Throwable) {
            null
        } finally {
            connection.disconnect()
        }
    }
}
