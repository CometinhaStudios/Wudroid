package info.cemu.cemu.graphicpacks

import android.content.Context
import android.util.Log
import java.io.File

/**
 * Installs small compatibility graphic packs shipped by Wudroid before Cemu
 * performs GraphicPack2::LoadAll().
 *
 * Test 1 intentionally bundles only the official New Super Mario Bros. U / 
 * New Super Luigi U Title Screen Crash Fix from cemu_graphic_packs Github980.
 * The original rules/patch files are kept unchanged.
 */
object WudroidBundledGraphicPacks {
    private const val TAG = "WudroidGraphicPacks"
    private const val PACK_VERSION = "Github980-NSMBU-CrashFix"
    private const val ASSET_ROOT =
        "wudroid_graphic_packs/NewSuperMarioBrosU/Workarounds/CrashFix"

    private val assetFiles = listOf(
        "rules.txt",
        "patch_CrashFix.asm",
    )

    /**
     * @return true when files were installed/refreshed during this launch.
     */
    fun install(context: Context): Boolean {
        val userDataRoot = context.getExternalFilesDir(null) ?: context.filesDir
        val targetDir = File(
            userDataRoot,
            "graphicPacks/WudroidBundled/NewSuperMarioBrosU/Workarounds/CrashFix"
        )
        val versionMarker = File(targetDir, ".wudroid_pack_version")

        val alreadyCurrent =
            versionMarker.takeIf { it.isFile }?.readText()?.trim() == PACK_VERSION &&
                assetFiles.all { File(targetDir, it).isFile }

        if (alreadyCurrent) {
            Log.i(TAG, "Bundled NSMBU CrashFix is already installed ($PACK_VERSION)")
            return false
        }

        if (!targetDir.exists() && !targetDir.mkdirs()) {
            Log.e(TAG, "Unable to create graphic-pack directory: ${targetDir.absolutePath}")
            return false
        }

        return runCatching {
            assetFiles.forEach { fileName ->
                val destination = File(targetDir, fileName)
                context.assets.open("$ASSET_ROOT/$fileName").use { input ->
                    destination.outputStream().use { output -> input.copyTo(output) }
                }
            }
            versionMarker.writeText(PACK_VERSION)
            Log.i(TAG, "Installed bundled NSMBU Title Screen Crash Fix ($PACK_VERSION)")
            true
        }.getOrElse { error ->
            Log.e(TAG, "Failed to install bundled NSMBU CrashFix", error)
            false
        }
    }
}
