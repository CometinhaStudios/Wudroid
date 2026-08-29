#!/usr/bin/env python3
from pathlib import Path
import re

path = Path("cemu-engine/src/android/app/src/main/java/info/cemu/cemu/MainActivity.kt")
s = path.read_text()

# Explicit post-import deletion confirmation.
state = "    var wuxImportProgress by remember { mutableStateOf<WudroidWuxImporter.Progress?>(null) }\n"
if "pendingDeleteWuxUri" not in s:
    if state not in s:
        raise SystemExit("WUX progress state anchor missing")
    s = s.replace(
        state,
        state + "    var pendingDeleteWuxUri by remember { mutableStateOf<Uri?>(null) }\n",
        1,
    )

old_result = """                    wuxImportProgress = null
                    Toast.makeText(context, result.message, Toast.LENGTH_LONG).show()
                    if (result.success) {
                        refreshLibraryRequest++
                    }
"""
new_result = """                    wuxImportProgress = null
                    if (result.success) {
                        refreshLibraryRequest++
                        pendingDeleteWuxUri = uri
                    } else {
                        Toast.makeText(context, result.message, Toast.LENGTH_LONG).show()
                    }
"""
if old_result in s:
    s = s.replace(old_result, new_result, 1)
elif new_result not in s:
    raise SystemExit("WUX result block missing")

# Remove old test-only footer under Add Game.
s = re.sub(
    r'\n\s*Text\(\n\s*"Teste 0\.1\.0-A: o WUX é convertido para WUD e verificado\. " \+\n'
    r'\s*"O arquivo WUX original NÃO é apagado\.",\n\s*color = WMuted,\n'
    r'\s*fontSize = 12\.sp\n\s*\)',
    '',
    s,
    count=1,
)

# Requested minimal progress UI: title + spinner only.
start = s.find("    if (wuxImportProgress != null) {")
end = s.find("    if (selectedProfileGame != null) {", start)
if start < 0 or end < 0:
    raise SystemExit("WUX progress dialog region missing")
progress = """    if (wuxImportProgress != null) {
        AlertDialog(
            onDismissRequest = {},
            title = { Text("Importando jogo") },
            text = {
                Column(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    CircularProgressIndicator()
                }
            },
            confirmButton = {}
        )
    }

    if (pendingDeleteWuxUri != null) {
        AlertDialog(
            onDismissRequest = { pendingDeleteWuxUri = null },
            title = { Text("Jogo importado") },
            text = {
                Text("A importação terminou e foi verificada. Deseja apagar o arquivo WUX original?")
            },
            confirmButton = {
                Button(onClick = {
                    val original = pendingDeleteWuxUri
                    pendingDeleteWuxUri = null
                    if (original != null) {
                        val deleted = WudroidWuxImporter.deleteOriginalWux(context, original)
                        Toast.makeText(
                            context,
                            if (deleted) "WUX original apagado."
                            else "Não foi possível apagar o WUX; ele foi mantido.",
                            Toast.LENGTH_LONG
                        ).show()
                    }
                }) {
                    Text("Apagar WUX", color = Color.Black)
                }
            },
            dismissButton = {
                Button(
                    onClick = { pendingDeleteWuxUri = null },
                    colors = ButtonDefaults.buttonColors(containerColor = WCard2)
                ) {
                    Text("Manter WUX")
                }
            }
        )
    }

"""
s = s[:start] + progress + s[end:]

# Long-press profile: add a separate graphics dialog.
profile_state = "    var favorite by remember { mutableStateOf(game.isFavorite) }\n"
if "showPerGameGraphics" not in s:
    if profile_state not in s:
        raise SystemExit("Game profile state anchor missing")
    s = s.replace(
        profile_state,
        profile_state + "    var showPerGameGraphics by remember { mutableStateOf(false) }\n",
        1,
    )

shader_button = """                Button(
                    modifier = Modifier.fillMaxWidth(),
                    onClick = {
                        safeRun { NativeGameTitles.removeShaderCacheFilesForTitle(game.titleId) }
                    },
"""
advanced_button = """                Button(
                    modifier = Modifier.fillMaxWidth(),
                    onClick = { showPerGameGraphics = true },
                    colors = ButtonDefaults.buttonColors(containerColor = WCard2)
                ) {
                    WudroidIcon(WIcon.Sliders, Modifier.size(18.dp), WBlue)
                    Spacer(Modifier.width(7.dp))
                    Text("Configurações gráficas deste jogo")
                }

"""
if "Configurações gráficas deste jogo" not in s:
    if shader_button not in s:
        raise SystemExit("Shader cache button anchor missing")
    s = s.replace(shader_button, advanced_button + shader_button, 1)

profile_end = """        }
    )
}

private fun startGame(context: Context, game: Game) {"""
profile_end_new = """        }
    )

    if (showPerGameGraphics) {
        WudroidPerGameGraphicsDialog(
            game = game,
            onDismiss = { showPerGameGraphics = false },
        )
    }
}

private fun startGame(context: Context, game: Game) {"""
if "WudroidPerGameGraphicsDialog(" not in s:
    if profile_end not in s:
        raise SystemExit("GameProfileDialog closing anchor missing")
    s = s.replace(profile_end, profile_end_new, 1)

# Known compatibility packs before graphics profile application.
old_resolution = """    // Apply the selected Wudroid resolution profile to real Graphic Pack presets.
    WudroidResolutionManager.applyForGame(context, game)

"""
new_resolution = """    // Apply known compatibility workarounds before boot.
    WudroidCompatibilityManager.applyForGame(game)

"""
if old_resolution in s:
    s = s.replace(old_resolution, new_resolution, 1)
elif new_resolution not in s:
    raise SystemExit("Old resolution launch hook missing")

old_engine = """    val graphicsEngine = context
        .getSharedPreferences(GRAPHICS_PREFS, Context.MODE_PRIVATE)
        .getInt(GRAPHICS_ENGINE_KEY, GRAPHICS_ENGINE_CEMU_VULKAN)
"""
new_engine = """    val globalGraphicsEngine = context
        .getSharedPreferences(GRAPHICS_PREFS, Context.MODE_PRIVATE)
        .getInt(GRAPHICS_ENGINE_KEY, GRAPHICS_ENGINE_CEMU_VULKAN)
    val graphicsEngine = WudroidGameGraphicsProfiles.applyBeforeLaunch(
        context = context,
        game = game,
        globalEngineFallback = globalGraphicsEngine,
    )
"""
if old_engine in s:
    s = s.replace(old_engine, new_engine, 1)
elif new_engine not in s:
    raise SystemExit("Graphics engine launch block missing")

# Keep global engine baseline synced for games configured as 'Use global'.
engine_save = "            graphicsPrefs.edit().putInt(GRAPHICS_ENGINE_KEY, engine).apply()\n"
engine_save_new = engine_save + \
    "            WudroidGameGraphicsProfiles.setGlobalGraphicsEngine(context, engine)\n"
if "setGlobalGraphicsEngine(context, engine)" not in s:
    if engine_save not in s:
        raise SystemExit("Global graphics engine save anchor missing")
    s = s.replace(engine_save, engine_save_new, 1)

# Version labels.
s = s.replace('"Wudroid 0.0.8 • frontend independente"', '"Wudroid 0.1.0 • frontend independente"')
s = s.replace('InfoRow("Wudroid", "0.0.8")', 'InfoRow("Wudroid", "0.1.0")')
s = s.replace('Text("0.0.8", color = WBlue', 'Text("0.1.0", color = WBlue')

path.write_text(s)
print("Wudroid 0.1.0-B features applied")
