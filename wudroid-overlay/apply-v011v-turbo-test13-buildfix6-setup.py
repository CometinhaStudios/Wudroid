#!/usr/bin/env python3
from pathlib import Path

path = Path("cemu-engine/src/android/app/src/main/java/info/cemu/cemu/MainActivity.kt")
if not path.exists():
    raise SystemExit("MainActivity.kt not found")

s = path.read_text()
marker = "WUDROID_TURBO_TEST13_BUILDFIX6_SETUP"

if marker in s:
    print("Wudroid Turbo Test13 BuildFix6 setup already applied")
    raise SystemExit(0)

anchor = "    var selectedProfileGame by remember { mutableStateOf<Game?>(null) }\n"
if anchor not in s:
    raise SystemExit("BuildFix6 setup state anchor missing")

state = anchor + f'''    // {marker}
    var setupKeysPresent by remember {{ mutableStateOf(hasImportedKeys()) }}
    var setupFolderPresent by remember {{ mutableStateOf(safeGamePaths().isNotEmpty()) }}

'''
s = s.replace(anchor, state, 1)

refresh_anchor = "    var refreshLibraryRequest by remember { mutableIntStateOf(0) }\n"
if refresh_anchor not in s:
    raise SystemExit("BuildFix6 refresh state anchor missing")

refresh_block = refresh_anchor + f'''
    // {marker}
    LaunchedEffect(refreshLibraryRequest) {{
        setupFolderPresent = safeGamePaths().isNotEmpty()
    }}

    LaunchedEffect(keysMessage) {{
        setupKeysPresent = hasImportedKeys()
    }}
'''
s = s.replace(refresh_anchor, refresh_block, 1)

old_args = '''        SetupWizard(
            keysPresent = hasImportedKeys(),
            gameFolderPresent = safeGamePaths().isNotEmpty(),'''
new_args = '''        SetupWizard(
            keysPresent = setupKeysPresent,
            gameFolderPresent = setupFolderPresent,'''
if old_args in s:
    s = s.replace(old_args, new_args, 1)
elif "keysPresent = setupKeysPresent" not in s:
    raise SystemExit("BuildFix6 SetupWizard invocation anchor missing")

start = s.find("@Composable\nprivate fun SetupWizard(")
if start < 0:
    raise SystemExit("BuildFix6 SetupWizard function missing")

end = s.find("\n@Composable\n", start + len("@Composable\nprivate fun SetupWizard("))
if end < 0:
    raise SystemExit("BuildFix6 SetupWizard end anchor missing")

new_setup = r'''@Composable
private fun SetupWizard(
    keysPresent: Boolean,
    gameFolderPresent: Boolean,
    keysMessage: String?,
    onImportKeys: () -> Unit,
    onChooseFolder: () -> Unit,
    onFinish: () -> Unit,
) {
    // WUDROID_TURBO_TEST13_BUILDFIX6_SETUP
    val currentKeysPresent = keysPresent
    val currentFolderPresent = gameFolderPresent

    Scaffold(
        contentWindowInsets = WindowInsets.safeDrawing,
        containerColor = WBg
    ) { pad ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(pad)
                .padding(horizontal = 26.dp, vertical = 24.dp),
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            Column {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    WudroidMark(64.dp)
                    Spacer(Modifier.width(16.dp))
                    Column {
                        Text("Wudroid", fontWeight = FontWeight.Bold, fontSize = 30.sp)
                        Text("Configuração inicial", color = WMuted)
                    }
                }

                Spacer(Modifier.height(30.dp))
                SetupTitle("Bem-vindo ao Wudroid")
                SetupBody(
                    "Selecione as chaves do seu próprio Wii U e a pasta dos jogos. " +
                        "As duas opções ficam disponíveis nesta tela."
                )

                Spacer(Modifier.height(20.dp))
                SetupActionCard(
                    icon = WIcon.Key,
                    title = "Selecionar keys.txt",
                    subtitle = if (currentKeysPresent)
                        "Arquivo importado e validado"
                    else
                        "Necessário para jogos WUD/WUX",
                    good = currentKeysPresent,
                    onClick = onImportKeys
                )

                if (keysMessage != null) {
                    Spacer(Modifier.height(9.dp))
                    Text(
                        keysMessage,
                        color = if (currentKeysPresent) WGreen else WRed,
                        fontSize = 13.sp
                    )
                }

                Spacer(Modifier.height(14.dp))
                SetupActionCard(
                    icon = WIcon.Folder,
                    title = "Selecionar pasta de jogos",
                    subtitle = if (currentFolderPresent)
                        "Pasta configurada ✓"
                    else
                        "Nenhuma pasta configurada",
                    good = currentFolderPresent,
                    onClick = onChooseFolder
                )

                Spacer(Modifier.height(18.dp))
                StatusPill(
                    "keys.txt",
                    currentKeysPresent,
                    if (currentKeysPresent) "Pronta" else "Ainda não selecionada"
                )
                Spacer(Modifier.height(10.dp))
                StatusPill(
                    "Pasta de jogos",
                    currentFolderPresent,
                    if (currentFolderPresent) "Configurada" else "Ainda não selecionada"
                )
            }

            Button(
                modifier = Modifier.fillMaxWidth(),
                onClick = onFinish,
                colors = ButtonDefaults.buttonColors(containerColor = WBlue)
            ) {
                Text("Entrar no Wudroid", color = Color.Black)
            }
        }
    }
}
'''

s = s[:start] + new_setup + s[end:]

for needle in (
    marker,
    "keysPresent = setupKeysPresent",
    "gameFolderPresent = setupFolderPresent",
    "LaunchedEffect(refreshLibraryRequest)",
    'title = "Selecionar keys.txt"',
    'title = "Selecionar pasta de jogos"',
    '"Pasta configurada ✓"',
):
    if needle not in s:
        raise SystemExit(f"BuildFix6 setup verification failed: {needle}")

path.write_text(s)
print("Wudroid Turbo Test13 BuildFix6 setup applied")
print("- setup: keys + folder on the first screen")
print("- folder state: green from real configured path state")
print("- legacy folder/WUX launcher logic preserved")
