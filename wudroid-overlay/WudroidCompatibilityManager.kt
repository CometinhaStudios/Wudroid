package info.cemu.cemu

import android.util.Log
import info.cemu.cemu.nativeinterface.NativeGameTitles
import info.cemu.cemu.nativeinterface.NativeGraphicPacks

object WudroidCompatibilityManager {
    private const val TAG = "WudroidCompat"

    private val minecraftIds = setOf(
        0x00050000101D9D00L,
        0x00050000101D7500L,
        0x00050000101DBE00L,
    )

    private val nsmbuIds = setOf(
        0x0005000010101D00L,
        0x0005000010101E00L,
        0x000500001014B700L,
        0x000500001014B800L,
        0x0005000010101C00L,
        0x0005000010142300L,
        0x0005000010142400L,
        0x0005000010142200L,
    )

    fun applyForGame(game: NativeGameTitles.Game): List<String> = runCatching {
        NativeGraphicPacks.refreshGraphicPacks()
        val infos = NativeGraphicPacks.getGraphicPackBasicInfos()
            .filter { it.titleIds.any { id -> id == game.titleId } }
        val enabled = mutableListOf<String>()

        for (info in infos) {
            val pack = NativeGraphicPacks.getGraphicPack(info.id) ?: continue
            val shouldEnable = when {
                game.titleId in minecraftIds ->
                    pack.name.equals("Crash Fix", ignoreCase = true) ||
                        (info.virtualPath.contains("Minecraft", ignoreCase = true) &&
                            pack.name.contains("Crash", ignoreCase = true))
                game.titleId in nsmbuIds ->
                    pack.name.contains("Title Screen Crash Fix", ignoreCase = true)
                else -> false
            }
            if (shouldEnable) {
                if (!pack.isActive()) pack.setActive(true)
                enabled += pack.name
                Log.i(TAG, "Enabled compatibility pack: ${pack.name}")
            }
        }
        enabled
    }.getOrElse {
        Log.e(TAG, "Compatibility pack activation failed", it)
        emptyList()
    }
}
