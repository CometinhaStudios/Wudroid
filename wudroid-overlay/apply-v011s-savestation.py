#!/usr/bin/env python3
from pathlib import Path

screen_path = Path('cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationScreen.kt')
if not screen_path.exists():
    raise SystemExit('EmulationScreen.kt not found')

screen = screen_path.read_text()
marker = 'WUDROID_SAVESTATION_TEST11'
if marker in screen:
    print('Wudroid Save Station Test11 already applied')
    raise SystemExit(0)

if 'WUDROID_QUICKSTATE_ENGINE_TEST10' not in screen:
    raise SystemExit('Quick State Engine Test10 must be applied before Save Station Test11')

# Compose pieces used by the compact 3x2 slot dialog.
imports = [
    'import androidx.compose.foundation.BorderStroke',
    'import androidx.compose.foundation.background',
    'import androidx.compose.foundation.gestures.detectTapGestures',
    'import androidx.compose.foundation.layout.aspectRatio',
    'import androidx.compose.foundation.layout.widthIn',
    'import androidx.compose.foundation.shape.RoundedCornerShape',
    'import androidx.compose.material3.Surface',
    'import androidx.compose.ui.input.pointer.pointerInput',
    'import androidx.compose.ui.text.font.FontWeight',
    'import androidx.compose.ui.window.Dialog',
]
for imp in imports:
    if imp not in screen:
        screen = screen.replace(
            'package info.cemu.cemu.emulation\n',
            'package info.cemu.cemu.emulation\n' + imp + '\n',
            1,
        )

# ---------------------------------------------------------------------------
# 1) State owned by EmulationScreen.
#    Slots are per-game and stored in filesDir. The Test10 engine still only
#    allows loading within the same Android process/session; a tiny .session
#    sidecar makes that limitation visible instead of pretending persistence.
# ---------------------------------------------------------------------------
state_anchor = '    val wudroidQuickStateContext = LocalContext.current // WUDROID_QUICKSTATE_ENGINE_TEST10\n'
if state_anchor not in screen:
    raise SystemExit('Quick State context anchor missing')

state_block = state_anchor + '''    var showWudroidSaveStation by remember { mutableStateOf(false) } // WUDROID_SAVESTATION_TEST11
    var wudroidSaveStationRevision by remember { mutableStateOf(0) }
    var wudroidSaveStationBusy by remember { mutableStateOf(false) }
    val wudroidSaveStationGameKey = remember(gamePath) {
        java.lang.Integer.toHexString(gamePath.hashCode())
    }
'''
screen = screen.replace(state_anchor, state_block, 1)

# Keep gameplay input disabled and keep a menu-owned pause active while the
# Save Station dialog is visible. Closing it resumes exactly like closing menu.
old_effect = '''    LaunchedEffect(drawerState.isClosed, quickDrawerState.isClosed, menuTransitionInProgress) {
        val menusClosed = drawerState.isClosed && quickDrawerState.isClosed
        setInputListeningEnabled(menusClosed)
        if (menusClosed && pausedByMenu && !menuTransitionInProgress) {
            NativeEmulation.resumeTitle()
            isWudroidPaused = false
            pausedByMenu = false
        }
    }
'''
new_effect = '''    LaunchedEffect(
        drawerState.isClosed,
        quickDrawerState.isClosed,
        menuTransitionInProgress,
        showWudroidSaveStation,
    ) {
        val menusClosed = drawerState.isClosed && quickDrawerState.isClosed
        val overlaysClosed = !showWudroidSaveStation
        setInputListeningEnabled(menusClosed && overlaysClosed)
        if (menusClosed && overlaysClosed && pausedByMenu && !menuTransitionInProgress) {
            NativeEmulation.resumeTitle()
            isWudroidPaused = false
            pausedByMenu = false
        }
    }
'''
if old_effect not in screen:
    raise SystemExit('Menu pause/input effect anchor missing')
screen = screen.replace(old_effect, new_effect, 1)

# ---------------------------------------------------------------------------
# 2) Add Save Game callback to the real left-side menu.
# ---------------------------------------------------------------------------
load_start = screen.find('                        onQuickLoad = {')
if load_start < 0:
    raise SystemExit('Quick Load callback missing')
onquit_pos = screen.find('                        onQuit = {', load_start)
if onquit_pos < 0:
    raise SystemExit('onQuit callback after Quick Load missing')

save_game_callback = '''                        onSaveGame = {
                            showWudroidSaveStation = true
                            closeDrawer()
                        },
'''
screen = screen[:onquit_pos] + save_game_callback + screen[onquit_pos:]

param_anchor = '''    onQuickSettings: () -> Unit,
    onQuickSave: () -> Unit,
    onQuickLoad: () -> Unit,
    onQuit: () -> Unit,
) {
'''
if param_anchor not in screen:
    raise SystemExit('Save Station menu parameter anchor missing')
screen = screen.replace(
    param_anchor,
    '''    onQuickSettings: () -> Unit,
    onQuickSave: () -> Unit,
    onQuickLoad: () -> Unit,
    onSaveGame: () -> Unit,
    onQuit: () -> Unit,
) {
''',
    1,
)

load_button = '''    TextButtonItem(
        label = "Carregar rápido",
        onClick = onQuickLoad,
    )
'''
if load_button not in screen:
    raise SystemExit('Carregar rápido button anchor missing')
screen = screen.replace(
    load_button,
    load_button + '''    TextButtonItem(
        label = "Save Game • 6 slots",
        onClick = onSaveGame,
    )
''',
    1,
)

# ---------------------------------------------------------------------------
# 3) Wire slot save/load/delete operations to the working Test10 JNI engine.
# ---------------------------------------------------------------------------
dialog_anchor = '    EmulationTextInputDialog()\n'
if dialog_anchor not in screen:
    raise SystemExit('EmulationTextInputDialog anchor missing')

dialog_call = r'''    if (showWudroidSaveStation) {
        val slotDirectory = wudroidQuickStateContext.filesDir
            .resolve("wudroid_states/$wudroidSaveStationGameKey/slots")
        WudroidSaveStationDialog(
            directory = slotDirectory,
            revision = wudroidSaveStationRevision,
            busy = wudroidSaveStationBusy,
            onDismiss = {
                if (!wudroidSaveStationBusy) showWudroidSaveStation = false
            },
            onSaveSlot = { slot ->
                if (!wudroidSaveStationBusy) {
                    scope.launch {
                        wudroidSaveStationBusy = true
                        val stateFile = slotDirectory.resolve("slot_$slot.wstate")
                        val sessionFile = slotDirectory.resolve("slot_$slot.session")
                        val result = withContext(Dispatchers.IO) {
                            slotDirectory.mkdirs()
                            val code = NativeEmulation.saveQuickState(stateFile.absolutePath)
                            if (code == 0) {
                                sessionFile.writeText(android.os.Process.myPid().toString())
                            }
                            code
                        }
                        wudroidSaveStationBusy = false
                        if (result == 0) wudroidSaveStationRevision++
                        snackbarHostState.showSnackbar(
                            when (result) {
                                0 -> "Slot $slot salvo"
                                2 -> "Memória do Wii U ainda não está disponível"
                                3 -> "Nenhuma região de RAM do jogo foi encontrada"
                                4 -> "Falha ao gravar o slot $slot"
                                8 -> "Estado grande demais para o limite de segurança"
                                else -> "Falha ao salvar slot (código $result)"
                            }
                        )
                    }
                }
            },
            onLoadSlot = { slot ->
                if (!wudroidSaveStationBusy) {
                    scope.launch {
                        val stateFile = slotDirectory.resolve("slot_$slot.wstate")
                        val sessionFile = slotDirectory.resolve("slot_$slot.session")
                        val currentPid = android.os.Process.myPid().toString()
                        val sameSession = withContext(Dispatchers.IO) {
                            stateFile.isFile && sessionFile.isFile &&
                                sessionFile.readText().trim() == currentPid
                        }
                        if (!sameSession) {
                            snackbarHostState.showSnackbar(
                                "Slot $slot pertence a outra sessão. Segure para apagar e reutilizar."
                            )
                        } else {
                            wudroidSaveStationBusy = true
                            val result = withContext(Dispatchers.IO) {
                                NativeEmulation.loadQuickState(stateFile.absolutePath)
                            }
                            wudroidSaveStationBusy = false
                            snackbarHostState.showSnackbar(
                                when (result) {
                                    0 -> "Slot $slot carregado"
                                    4 -> "Slot $slot não encontrado"
                                    5 -> "Slot pertence a outra sessão do Wudroid"
                                    6 -> "Slot inválido ou incompleto"
                                    7 -> "O mapa de memória mudou; carregamento cancelado"
                                    else -> "Falha ao carregar slot (código $result)"
                                }
                            )
                            if (result == 0) showWudroidSaveStation = false
                        }
                    }
                }
            },
            onDeleteSlot = { slot ->
                if (!wudroidSaveStationBusy) {
                    scope.launch {
                        withContext(Dispatchers.IO) {
                            slotDirectory.resolve("slot_$slot.wstate").delete()
                            slotDirectory.resolve("slot_$slot.session").delete()
                        }
                        wudroidSaveStationRevision++
                        snackbarHostState.showSnackbar("Slot $slot apagado")
                    }
                }
            },
        )
    }

'''
screen = screen.replace(dialog_anchor, dialog_call + dialog_anchor, 1)

# ---------------------------------------------------------------------------
# 4) Compact floating Save Station UI: 6 slots in a strict 3 x 2 grid.
#    Empty tap = save; filled tap = load; filled long-press = delete/reuse.
# ---------------------------------------------------------------------------
function_anchor = '@Composable\nprivate fun EmulationQuitConfirmationDialog('
if function_anchor not in screen:
    raise SystemExit('Quit dialog function anchor missing')

save_station_functions = r'''@Composable
private fun WudroidSaveStationDialog(
    directory: java.io.File,
    revision: Int,
    busy: Boolean,
    onDismiss: () -> Unit,
    onSaveSlot: (Int) -> Unit,
    onLoadSlot: (Int) -> Unit,
    onDeleteSlot: (Int) -> Unit,
) {
    // Read revision so a successful save/delete refreshes file metadata cards.
    val refreshRevision = revision
    val currentPid = android.os.Process.myPid().toString()
    val formatter = remember(refreshRevision) {
        java.text.SimpleDateFormat("dd/MM/yyyy  HH:mm", java.util.Locale.getDefault())
    }

    Dialog(onDismissRequest = onDismiss) {
        Surface(
            modifier = Modifier
                .fillMaxWidth(0.92f)
                .widthIn(max = 640.dp),
            shape = RoundedCornerShape(22.dp),
            color = WudroidDrawerBackground,
            border = BorderStroke(1.dp, WudroidDrawerOutline),
            shadowElevation = 14.dp,
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = "SAVE STATION",
                            color = WudroidCyan,
                            fontSize = 18.sp,
                            fontWeight = FontWeight.Bold,
                        )
                        Text(
                            text = "6 slots • 3 × 2",
                            color = WudroidDrawerMuted,
                            fontSize = 11.sp,
                        )
                    }
                    TextButton(onClick = onDismiss, enabled = !busy) {
                        Text("Fechar", color = WudroidDrawerText)
                    }
                }

                Text(
                    text = if (busy) {
                        "Processando estado..."
                    } else {
                        "Vazio: toque para salvar • Salvo: toque para carregar • Segure para apagar"
                    },
                    color = if (busy) WudroidCyan else WudroidDrawerMuted,
                    fontSize = 10.sp,
                    modifier = Modifier.padding(top = 6.dp, bottom = 10.dp),
                )

                for (row in 0 until 2) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(9.dp),
                    ) {
                        for (column in 0 until 3) {
                            val slot = row * 3 + column + 1
                            val stateFile = directory.resolve("slot_$slot.wstate")
                            val sessionFile = directory.resolve("slot_$slot.session")
                            val filled = stateFile.isFile
                            val sameSession = filled && sessionFile.isFile && runCatching {
                                sessionFile.readText().trim() == currentPid
                            }.getOrDefault(false)
                            val dateLabel = if (filled) {
                                formatter.format(java.util.Date(stateFile.lastModified()))
                            } else {
                                "Slot vazio"
                            }

                            WudroidSaveSlotCard(
                                modifier = Modifier.weight(1f),
                                slot = slot,
                                filled = filled,
                                sameSession = sameSession,
                                dateLabel = dateLabel,
                                busy = busy,
                                onTap = {
                                    if (!busy) {
                                        if (filled) onLoadSlot(slot) else onSaveSlot(slot)
                                    }
                                },
                                onLongPress = {
                                    if (!busy && filled) onDeleteSlot(slot)
                                },
                            )
                        }
                    }
                    if (row == 0) {
                        androidx.compose.foundation.layout.Spacer(
                            modifier = Modifier.padding(top = 9.dp)
                        )
                    }
                }

                Text(
                    text = "Test11 usa o motor Quick State atual: carregar ainda é limitado à sessão atual.",
                    color = WudroidDrawerMuted,
                    fontSize = 9.sp,
                    modifier = Modifier.padding(top = 10.dp),
                )
            }
        }
    }
}

@Composable
private fun WudroidSaveSlotCard(
    modifier: Modifier,
    slot: Int,
    filled: Boolean,
    sameSession: Boolean,
    dateLabel: String,
    busy: Boolean,
    onTap: () -> Unit,
    onLongPress: () -> Unit,
) {
    Surface(
        modifier = modifier
            .aspectRatio(1.18f)
            .pointerInput(slot, filled, busy) {
                detectTapGestures(
                    onTap = { if (!busy) onTap() },
                    onLongPress = { if (!busy && filled) onLongPress() },
                )
            },
        shape = RoundedCornerShape(15.dp),
        color = if (filled) WudroidDrawerSurfacePressed else WudroidDrawerSurface,
        border = BorderStroke(
            width = if (filled) 1.5.dp else 1.dp,
            color = if (filled && sameSession) WudroidCyan else WudroidDrawerOutline,
        ),
    ) {
        Column(
            modifier = Modifier.padding(9.dp),
            verticalArrangement = Arrangement.SpaceBetween,
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    text = "SLOT $slot",
                    color = if (filled) WudroidCyan else WudroidDrawerText,
                    fontWeight = FontWeight.Bold,
                    fontSize = 12.sp,
                    modifier = Modifier.weight(1f),
                )
                Text(
                    text = if (filled) "●" else "+",
                    color = if (filled && sameSession) WudroidCyan else WudroidDrawerMuted,
                    fontSize = 13.sp,
                )
            }

            // Test11 preview tile. A real gameplay frame thumbnail will be wired
            // after the slot flow itself is build/runtime validated.
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f)
                    .padding(vertical = 6.dp)
                    .background(WudroidDrawerBackground, RoundedCornerShape(9.dp)),
                contentAlignment = Alignment.Center,
            ) {
                Text(
                    text = if (!filled) "SALVAR" else if (sameSession) "PRONTO" else "SESSÃO ANTERIOR",
                    color = if (filled && sameSession) WudroidCyan else WudroidDrawerMuted,
                    fontSize = if (sameSession) 10.sp else 8.sp,
                    fontWeight = FontWeight.Bold,
                )
            }

            Text(
                text = dateLabel,
                color = WudroidDrawerMuted,
                fontSize = 8.sp,
                maxLines = 1,
            )
        }
    }
}

'''
screen = screen.replace(function_anchor, save_station_functions + function_anchor, 1)

screen_path.write_text(screen)

# Fail during Apply rather than minutes later in Gradle if an anchor regresses.
check = screen_path.read_text()
required = [
    marker,
    'label = "Save Game • 6 slots"',
    'private fun WudroidSaveStationDialog(',
    'private fun WudroidSaveSlotCard(',
    'for (row in 0 until 2)',
    'for (column in 0 until 3)',
    'onLongPress = { if (!busy && filled) onLongPress() }',
    'NativeEmulation.saveQuickState(stateFile.absolutePath)',
    'NativeEmulation.loadQuickState(stateFile.absolutePath)',
    'showWudroidSaveStation = false',
    'setInputListeningEnabled(menusClosed && overlaysClosed)',
]
missing = [x for x in required if x not in check]
if missing:
    raise SystemExit('Save Station Test11 verification failed: ' + ', '.join(missing))

print('Wudroid 0.1.1 Save Station Test11 applied')
print('- working Quick State engine reused without native changes')
print('- per-game Save Station dialog added')
print('- 6 slots arranged 3 x 2')
print('- empty tap saves; filled tap loads')
print('- long press deletes and frees a filled slot')
print('- date/time shown from slot file metadata')
print('- previous-session states are visibly blocked by Test10 session guard')
print('- preview tile is placeholder; gameplay-frame thumbnail intentionally comes after validation')
