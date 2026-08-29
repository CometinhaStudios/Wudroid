package info.cemu.cemu.graphicpacks

import android.content.Context
import android.util.Log
import java.io.File

object WudroidBundledGraphicPacks {
    private const val TAG = "WudroidGraphicPacks"

    private data class PackSpec(
        val version: String,
        val assetRoot: String,
        val targetRelative: String,
    )

    private val packs = listOf(
        PackSpec(
            version = "Github980-NSMBU-CrashFix",
            assetRoot =
                "wudroid_graphic_packs/NewSuperMarioBrosU/Workarounds/CrashFix",
            targetRelative =
                "graphicPacks/WudroidBundled/NewSuperMarioBrosU/Workarounds/CrashFix",
        ),
        PackSpec(
            version = "Github980-Wudroid-NSMBU-Resolution-v1",
            assetRoot =
                "wudroid_graphic_packs/NewSuperMarioBrosU/Graphics",
            targetRelative =
                "graphicPacks/WudroidBundled/NewSuperMarioBrosU/Graphics",
        ),
    )

    fun install(context: Context): Boolean {
        val userDataRoot = context.getExternalFilesDir(null) ?: context.filesDir
        var changed = false

        packs.forEach { spec ->
            val targetDir = File(userDataRoot, spec.targetRelative)
            val marker = File(targetDir, ".wudroid_pack_version")
            val current = marker.takeIf { it.isFile }?.readText()?.trim()

            if (current == spec.version) return@forEach

            runCatching {
                if (!targetDir.exists() && !targetDir.mkdirs()) {
                    error("Unable to create ${targetDir.absolutePath}")
                }
                copyAssetTree(context, spec.assetRoot, targetDir)
                marker.writeText(spec.version)
                Log.i(TAG, "Installed ${spec.targetRelative} (${spec.version})")
                changed = true
            }.onFailure {
                Log.e(TAG, "Failed to install ${spec.targetRelative}", it)
            }
        }

        return changed
    }

    private fun copyAssetTree(
        context: Context,
        assetPath: String,
        destination: File,
    ) {
        val children = context.assets.list(assetPath).orEmpty()
        if (children.isEmpty()) {
            destination.parentFile?.mkdirs()
            context.assets.open(assetPath).use { input ->
                destination.outputStream().use { output -> input.copyTo(output) }
            }
            return
        }

        destination.mkdirs()
        children.forEach { child ->
            copyAssetTree(
                context,
                "$assetPath/$child",
                File(destination, child),
            )
        }
    }
}
