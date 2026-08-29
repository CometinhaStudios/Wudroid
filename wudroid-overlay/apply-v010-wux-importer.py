#!/usr/bin/env python3
from pathlib import Path

path = Path("cemu-engine/src/android/app/src/main/java/info/cemu/cemu/MainActivity.kt")
s = path.read_text()

anchor = "import androidx.compose.runtime.remember\n"
if "import androidx.compose.runtime.rememberCoroutineScope\n" not in s:
    if anchor not in s:
        raise SystemExit("Could not find remember import")
    s = s.replace(anchor, anchor + "import androidx.compose.runtime.rememberCoroutineScope\n", 1)

anchor = "import kotlinx.coroutines.runBlocking\n"
if "import kotlinx.coroutines.launch\n" not in s:
    if anchor not in s:
        raise SystemExit("Could not find coroutine import anchor")
    s = s.replace(anchor, anchor + "import kotlinx.coroutines.launch\n", 1)

needle = """    var keysMessage by remember { mutableStateOf<String?>(null) }
    var selectedProfileGame by remember { mutableStateOf<Game?>(null) }
"""
replacement = """    var keysMessage by remember { mutableStateOf<String?>(null) }
    var selectedProfileGame by remember { mutableStateOf<Game?>(null) }
    var showAddGameDialog by remember { mutableStateOf(false) }
    var wuxImportProgress by remember { mutableStateOf<WudroidWuxImporter.Progress?>(null) }
    val importerScope = rememberCoroutineScope()
"""
if "showAddGameDialog" not in s:
    if needle not in s:
        raise SystemExit("Could not find WudroidRoot state block")
    s = s.replace(needle, replacement, 1)

folder_block = """    val folderLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.OpenDocumentTree()
    ) { uri ->
        if (uri != null && addGameFolder(context, uri)) {
            // Do not reload native titles inside the SAF callback.
            // Let the ViewModel refresh after the picker has returned.
            refreshLibraryRequest++
        }
    }
"""
wux_launcher = folder_block + """

    val wuxLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.OpenDocument()
    ) { uri ->
        if (uri != null) {
            val libraryTree = WudroidWuxImporter.libraryFolderUri(context)
            if (libraryTree == null) {
                Toast.makeText(
                    context,
                    \"Escolha primeiro a pasta onde o Wudroid guardará os jogos.\",
                    Toast.LENGTH_LONG
                ).show()
            } else {
                importerScope.launch {
                    wuxImportProgress = WudroidWuxImporter.Progress(\"Preparando\", 0)
                    val result = WudroidWuxImporter.importWuxToLibrary(
                        context = context,
                        inputUri = uri,
                        libraryTreeUri = libraryTree,
                        onProgress = { wuxImportProgress = it },
                    )
                    wuxImportProgress = null
                    Toast.makeText(context, result.message, Toast.LENGTH_LONG).show()
                    if (result.success) {
                        refreshLibraryRequest++
                    }
                }
            }
        }
    }
"""
# Undo escaping that is only needed inside this Python source literal.
wux_launcher = wux_launcher.replace('\\"', '"')
if "val wuxLauncher = rememberLauncherForActivityResult" not in s:
    if folder_block not in s:
        raise SystemExit("Could not find folder launcher block")
    s = s.replace(folder_block, wux_launcher, 1)

old_call = """            onChooseFolder = { folderLauncher.launch(null) },
            onGameProfile = { selectedProfileGame = it }
"""
new_call = """            onChooseFolder = { showAddGameDialog = true },
            onGameProfile = { selectedProfileGame = it }
"""
if old_call in s:
    s = s.replace(old_call, new_call, 1)
elif new_call not in s:
    raise SystemExit("Could not patch LibraryScreen add action")

dialog_anchor = """    if (selectedProfileGame != null) {
"""
add_dialog = '''    if (showAddGameDialog) {
        AlertDialog(
            onDismissRequest = { showAddGameDialog = false },
            title = { Text("Adicionar jogo") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Text(
                        "Escolha como adicionar o jogo à biblioteca.",
                        color = WMuted
                    )
                    Button(
                        modifier = Modifier.fillMaxWidth(),
                        onClick = {
                            showAddGameDialog = false
                            folderLauncher.launch(null)
                        }
                    ) {
                        WudroidIcon(WIcon.Folder, Modifier.size(20.dp), Color.Black)
                        Spacer(Modifier.width(8.dp))
                        Text("Adicionar pasta", color = Color.Black)
                    }
                    Button(
                        modifier = Modifier.fillMaxWidth(),
                        onClick = {
                            val libraryTree = WudroidWuxImporter.libraryFolderUri(context)
                            if (libraryTree == null) {
                                showAddGameDialog = false
                                Toast.makeText(
                                    context,
                                    "Escolha primeiro a pasta de jogos.",
                                    Toast.LENGTH_LONG
                                ).show()
                                folderLauncher.launch(null)
                            } else {
                                showAddGameDialog = false
                                wuxLauncher.launch(arrayOf("application/octet-stream", "*/*"))
                            }
                        }
                    ) {
                        WudroidIcon(WIcon.Gamepad, Modifier.size(20.dp), Color.Black)
                        Spacer(Modifier.width(8.dp))
                        Text("Importar arquivo WUX", color = Color.Black)
                    }
                    Text(
                        "Teste 0.1.0-A: o WUX é convertido para WUD e verificado. " +
                            "O arquivo WUX original NÃO é apagado.",
                        color = WMuted,
                        fontSize = 12.sp
                    )
                }
            },
            confirmButton = {
                Button(
                    onClick = { showAddGameDialog = false },
                    colors = ButtonDefaults.buttonColors(containerColor = WCard2)
                ) { Text("Cancelar") }
            }
        )
    }

    if (wuxImportProgress != null) {
        val progress = wuxImportProgress!!
        AlertDialog(
            onDismissRequest = {},
            title = { Text("Importando WUX") },
            text = {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    CircularProgressIndicator()
                    Spacer(Modifier.height(14.dp))
                    Text(progress.stage, fontWeight = FontWeight.Bold)
                    Spacer(Modifier.height(4.dp))
                    Text("${progress.percent}%", color = WBlue, fontSize = 20.sp)
                    Spacer(Modifier.height(8.dp))
                    Text(
                        "Não feche o Wudroid durante este primeiro teste. O WUX original será preservado.",
                        color = WMuted,
                        fontSize = 12.sp
                    )
                }
            },
            confirmButton = {}
        )
    }

'''
if "Importando WUX" not in s:
    if dialog_anchor not in s:
        raise SystemExit("Could not find profile dialog anchor")
    s = s.replace(dialog_anchor, add_dialog + dialog_anchor, 1)

s = s.replace('Text("Pasta", fontWeight = FontWeight.Bold)', 'Text("Adicionar", fontWeight = FontWeight.Bold)', 1)
s = s.replace('Text("Adicionar pasta", color = Color.Black)', 'Text("Adicionar jogo", color = Color.Black)', 1)

old_refresh = """    LaunchedEffect(refreshRequest) {
        if (refreshRequest > 0 && gameListViewModel.gamePathsHaveChanged()) {
            // SAF has already returned and the Activity is stable here.
            kotlinx.coroutines.delay(150)
            gameListViewModel.refreshGames()
        }
    }
"""
new_refresh = """    LaunchedEffect(refreshRequest) {
        if (refreshRequest > 0) {
            // SAF/import work has already returned to a stable Activity here.
            kotlinx.coroutines.delay(200)
            gameListViewModel.refreshGames()
        }
    }
"""
if old_refresh in s:
    s = s.replace(old_refresh, new_refresh, 1)
elif new_refresh not in s:
    raise SystemExit("Could not find library refresh block")

folder_anchor = """        val gamesPath = documentFile.uri.toString()
"""
folder_new = folder_anchor + """        WudroidWuxImporter.rememberLibraryFolder(context, documentFile.uri)
"""
if "WudroidWuxImporter.rememberLibraryFolder" not in s:
    if folder_anchor not in s:
        raise SystemExit("Could not find addGameFolder path block")
    s = s.replace(folder_anchor, folder_new, 1)

path.write_text(s)
print("Wudroid 0.1.0-A WUX importer UI applied")
