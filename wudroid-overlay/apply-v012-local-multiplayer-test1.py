#!/usr/bin/env python3
from pathlib import Path

main_path = Path('cemu-engine/src/android/app/src/main/java/info/cemu/cemu/MainActivity.kt')
screen_path = Path('cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationScreen.kt')
manifest_path = Path('cemu-engine/src/android/app/src/main/AndroidManifest.xml')

for p in (main_path, screen_path, manifest_path):
    if not p.exists():
        raise SystemExit(f'Required source missing: {p}')

main = main_path.read_text()
screen = screen_path.read_text()
manifest = manifest_path.read_text()
marker = 'WUDROID_012_LOCAL_MULTIPLAYER_TEST1'

if marker in main:
    print('Wudroid 0.1.2 Local Multiplayer Test1 already applied')
    raise SystemExit(0)


def ensure_import(source: str, imp: str) -> str:
    if imp in source:
        return source
    lines = source.splitlines(keepends=True)
    indexes = [i for i, line in enumerate(lines) if line.startswith('import ')]
    if not indexes:
        raise SystemExit('Import block missing')
    lines.insert(indexes[-1] + 1, imp + '\n')
    return ''.join(lines)

for imp in (
    'import androidx.compose.runtime.rememberCoroutineScope',
    'import kotlinx.coroutines.Dispatchers',
    'import kotlinx.coroutines.delay',
    'import kotlinx.coroutines.launch',
    'import kotlinx.coroutines.withContext',
):
    main = ensure_import(main, imp)

old_enum = '''private enum class Screen {
    Library, Settings, Advanced, Controls, GameFolders, SystemInfo, About
}'''
new_enum = '''private enum class Screen {
    Library, Settings, Advanced, Controls, ControllerPlayer, Profile,
    Multiplayer, GameFolders, SystemInfo, About
}'''
if old_enum not in main:
    raise SystemExit('Screen enum anchor missing')
main = main.replace(old_enum, new_enum, 1)

root_state = '    var selectedProfileGame by remember { mutableStateOf<Game?>(null) }\n'
if root_state not in main:
    raise SystemExit('Root state anchor missing')
main = main.replace(
    root_state,
    root_state + f'    var selectedControllerIndex by remember {{ mutableIntStateOf(0) }} // {marker}\n',
    1,
)

lib_call = '''        Screen.Library -> LibraryScreen(
            refreshRequest = refreshLibraryRequest,
            onSettings = { screen = Screen.Settings },
            onChooseFolder = { folderLauncher.launch(null) },
            onGameProfile = { selectedProfileGame = it }
        )'''
lib_new = '''        Screen.Library -> LibraryScreen(
            refreshRequest = refreshLibraryRequest,
            onSettings = { screen = Screen.Settings },
            onMultiplayer = { screen = Screen.Multiplayer },
            onChooseFolder = { folderLauncher.launch(null) },
            onGameProfile = { selectedProfileGame = it }
        )'''
if lib_call not in main:
    raise SystemExit('LibraryScreen root call anchor missing')
main = main.replace(lib_call, lib_new, 1)

settings_call_old = '''            onControls = { screen = Screen.Controls },
            onGameFolders = { screen = Screen.GameFolders },'''
settings_call_new = '''            onControls = { screen = Screen.Controls },
            onProfile = { screen = Screen.Profile },
            onGameFolders = { screen = Screen.GameFolders },'''
if settings_call_old not in main:
    raise SystemExit('Settings root call anchor missing')
main = main.replace(settings_call_old, settings_call_new, 1)

case_old = '''        Screen.Advanced -> AdvancedSettingsScreen(onBack = { screen = Screen.Settings })
        Screen.Controls -> ControlsScreen(onBack = { screen = Screen.Settings })
        Screen.GameFolders -> GameFoldersScreen('''
case_new = '''        Screen.Advanced -> AdvancedSettingsScreen(onBack = { screen = Screen.Settings })
        Screen.Controls -> ControlsScreen(
            onBack = { screen = Screen.Settings },
            onPlayer = {
                selectedControllerIndex = it
                screen = Screen.ControllerPlayer
            }
        )
        Screen.ControllerPlayer -> ControllerPlayerScreen(
            controllerIndex = selectedControllerIndex,
            onBack = { screen = Screen.Controls }
        )
        Screen.Profile -> ProfileScreen(onBack = { screen = Screen.Settings })
        Screen.Multiplayer -> MultiplayerScreen(onBack = { screen = Screen.Library })
        Screen.GameFolders -> GameFoldersScreen('''
if case_old not in main:
    raise SystemExit('Navigation case anchor missing')
main = main.replace(case_old, case_new, 1)

sig_old = '''private fun LibraryScreen(
    refreshRequest: Int,
    onSettings: () -> Unit,
    onChooseFolder: () -> Unit,
    onGameProfile: (Game) -> Unit,
) {'''
sig_new = '''private fun LibraryScreen(
    refreshRequest: Int,
    onSettings: () -> Unit,
    onMultiplayer: () -> Unit,
    onChooseFolder: () -> Unit,
    onGameProfile: (Game) -> Unit,
) {'''
if sig_old not in main:
    raise SystemExit('Library signature anchor missing')
main = main.replace(sig_old, sig_new, 1)

fab_old = '''        floatingActionButton = {
            FloatingActionButton(
                onClick = onChooseFolder,
                containerColor = WBlue,
                contentColor = Color.Black,
                shape = RoundedCornerShape(18.dp)
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 18.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    WudroidIcon(WIcon.Folder, Modifier.size(23.dp), Color.Black)
                    Spacer(Modifier.width(10.dp))
                    Text("Pasta", fontWeight = FontWeight.Bold)
                }
            }
        }
'''
fab_new = '''        floatingActionButton = {
            Column(
                horizontalAlignment = Alignment.End,
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                FloatingActionButton(
                    onClick = onMultiplayer,
                    containerColor = WCard2,
                    contentColor = WBlue,
                    shape = RoundedCornerShape(18.dp)
                ) {
                    Row(
                        modifier = Modifier.padding(horizontal = 18.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        WudroidIcon(WIcon.Controller, Modifier.size(23.dp), WBlue)
                        Spacer(Modifier.width(10.dp))
                        Text("Multiplayer", color = WText, fontWeight = FontWeight.Bold)
                    }
                }
                FloatingActionButton(
                    onClick = onChooseFolder,
                    containerColor = WBlue,
                    contentColor = Color.Black,
                    shape = RoundedCornerShape(18.dp)
                ) {
                    Row(
                        modifier = Modifier.padding(horizontal = 18.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        WudroidIcon(WIcon.Folder, Modifier.size(23.dp), Color.Black)
                        Spacer(Modifier.width(10.dp))
                        Text("Pasta", fontWeight = FontWeight.Bold)
                    }
                }
            }
        }
'''
if fab_old not in main:
    raise SystemExit('Library FAB anchor missing')
main = main.replace(fab_old, fab_new, 1)

settings_sig_old = '''    onAdvanced: () -> Unit,
    onControls: () -> Unit,
    onGameFolders: () -> Unit,'''
settings_sig_new = '''    onAdvanced: () -> Unit,
    onControls: () -> Unit,
    onProfile: () -> Unit,
    onGameFolders: () -> Unit,'''
if settings_sig_old not in main:
    raise SystemExit('Settings signature anchor missing')
main = main.replace(settings_sig_old, settings_sig_new, 1)

controls_entry = '''        SettingsEntry(
            WIcon.Controller,
            "Controles",
            "GamePad, Pro Controller e controles na tela",
            onControls
        )
'''
profile_entry = controls_entry + '''        SettingsEntry(
            WIcon.App,
            "Perfil",
            "Nome do jogador e nome da hospedagem local",
            onProfile
        )
'''
if controls_entry not in main:
    raise SystemExit('Settings controls entry anchor missing')
main = main.replace(controls_entry, profile_entry, 1)

start = main.find('@Composable\nprivate fun ControlsScreen(')
end = main.find('\n@Composable\nprivate fun GameFoldersScreen(', start)
if start < 0 or end < 0:
    raise SystemExit('ControlsScreen region missing')

new_controls = r'''@Composable
private fun ControlsScreen(
    onBack: () -> Unit,
    onPlayer: (Int) -> Unit,
) {
    ScreenScaffold("Controles", onBack) {
        Text(
            "Multiplayer local no mesmo aparelho",
            color = WBlue,
            fontWeight = FontWeight.Bold,
            fontSize = 14.sp
        )
        Text(
            "Configure até 8 jogadores. O Jogador 1 pode usar o GamePad; os demais ficam como controles adicionais.",
            color = WMuted,
            fontSize = 13.sp,
            lineHeight = 18.sp
        )
        Spacer(Modifier.height(8.dp))

        repeat(8) { index ->
            val disabled = safeBool { NativeInput.isControllerDisabled(index) }
            val type = if (disabled) {
                NativeInput.EmulatedControllerType.DISABLED
            } else {
                safeInt { NativeInput.getControllerType(index) }
            }
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .combinedClickable(onClick = { onPlayer(index) }, onLongClick = {}),
                colors = CardDefaults.cardColors(containerColor = WBg),
                shape = RoundedCornerShape(10.dp)
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 17.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    WudroidIcon(
                        WIcon.Controller,
                        Modifier.size(25.dp),
                        if (disabled) WMuted else WText
                    )
                    Spacer(Modifier.width(18.dp))
                    Column(Modifier.weight(1f)) {
                        Text("Jogador ${index + 1}", fontSize = 18.sp)
                        if (!disabled) {
                            Text(controllerTypeLabel(type), color = WMuted, fontSize = 12.sp)
                        }
                    }
                    Text(
                        if (disabled) "Desativado" else "Ativo",
                        color = if (disabled) WMuted else WGreen,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            }
        }
    }
}

@Composable
private fun ControllerPlayerScreen(
    controllerIndex: Int,
    onBack: () -> Unit,
) {
    var overlaySettings by remember { mutableStateOf(getOverlaySettings()) }
    var controllerType by remember(controllerIndex) {
        mutableIntStateOf(
            safeInt {
                if (NativeInput.isControllerDisabled(controllerIndex))
                    NativeInput.EmulatedControllerType.DISABLED
                else NativeInput.getControllerType(controllerIndex)
            }
        )
    }
    var alpha by remember { mutableFloatStateOf(overlaySettings.alpha.toFloat()) }
    val connected = controllerType != NativeInput.EmulatedControllerType.DISABLED

    ScreenScaffold("Jogador ${controllerIndex + 1}", onBack) {
        ToggleEntry(
            WIcon.Controller,
            "Conectado",
            if (connected) "Slot ativo para multiplayer local" else "Slot desativado",
            connected
        ) { enabled ->
            val newType = if (enabled) {
                if (controllerIndex == 0) NativeInput.EmulatedControllerType.VPAD
                else NativeInput.EmulatedControllerType.PRO
            } else NativeInput.EmulatedControllerType.DISABLED
            controllerType = newType
            safeRun {
                NativeInput.setControllerType(controllerIndex, newType)
                NativeInput.saveInputs()
                NativeSettings.saveSettings()
            }
        }

        if (controllerType != NativeInput.EmulatedControllerType.DISABLED) {
            SectionLabel("Tipo de controle")
            val choices = if (controllerIndex == 0) {
                listOf(
                    NativeInput.EmulatedControllerType.VPAD to "GamePad",
                    NativeInput.EmulatedControllerType.PRO to "Pro Controller",
                    NativeInput.EmulatedControllerType.CLASSIC to "Classic",
                    NativeInput.EmulatedControllerType.WIIMOTE to "Wiimote"
                )
            } else {
                listOf(
                    NativeInput.EmulatedControllerType.PRO to "Pro Controller",
                    NativeInput.EmulatedControllerType.CLASSIC to "Classic",
                    NativeInput.EmulatedControllerType.WIIMOTE to "Wiimote"
                )
            }
            ChoiceButtons(choices = choices, selected = controllerType) {
                controllerType = it
                safeRun {
                    NativeInput.setControllerType(controllerIndex, it)
                    NativeInput.saveInputs()
                    NativeSettings.saveSettings()
                }
            }

            SectionLabel("Mapeamento")
            InfoRow(
                "Controle físico",
                "Conecte controles Bluetooth ou USB. Este Test1 prepara os 8 slots; o refinamento do mapeamento automático por dispositivo continua na próxima etapa."
            )
            InfoRow("Perfil", "Indefinido")
            InfoRow("A / B / X / Y", "Mapeamento do backend Cemu preservado")
            InfoRow("Direcional e analógicos", "Mapeamento do backend Cemu preservado")
            InfoRow("L / R / ZL / ZR", "Mapeamento do backend Cemu preservado")

            if (controllerIndex == 0) {
                SectionLabel("Controles na tela")
                ToggleEntry(
                    WIcon.Gamepad,
                    "Controles na tela",
                    "Mostra os botões touch durante o jogo",
                    overlaySettings.isOverlayEnabled
                ) {
                    overlaySettings = updateOverlaySettings { current ->
                        current.copy(
                            isOverlayEnabled = it,
                            controllerIndex = 0,
                            alpha = maxOf(current.alpha, 150)
                        )
                    }
                }
                ToggleEntry(
                    WIcon.Controller,
                    "Vibrar ao tocar",
                    "Feedback tátil nos botões virtuais",
                    overlaySettings.isVibrateOnTouchEnabled
                ) {
                    overlaySettings = updateOverlaySettings { current ->
                        current.copy(isVibrateOnTouchEnabled = it)
                    }
                }
                SectionLabel("Transparência dos botões")
                Slider(
                    value = alpha,
                    onValueChange = { alpha = it },
                    onValueChangeFinished = {
                        overlaySettings = updateOverlaySettings { current ->
                            current.copy(alpha = alpha.roundToInt().coerceIn(0, 255))
                        }
                    },
                    valueRange = 30f..255f
                )
                Text("${alpha.roundToInt()}/255", color = WMuted, fontSize = 12.sp)
            }
        }
    }
}

private fun controllerTypeLabel(type: Int): String = when (type) {
    NativeInput.EmulatedControllerType.VPAD -> "GamePad"
    NativeInput.EmulatedControllerType.PRO -> "Pro Controller"
    NativeInput.EmulatedControllerType.CLASSIC -> "Classic"
    NativeInput.EmulatedControllerType.WIIMOTE -> "Wiimote"
    else -> "Desativado"
}

@Composable
private fun ProfileScreen(onBack: () -> Unit) {
    val context = LocalContext.current
    var profile by remember { mutableStateOf(WudroidProfileStore.load(context)) }
    var nickname by remember(profile.localId) { mutableStateOf(TextFieldValue(profile.nickname)) }
    var roomName by remember(profile.localId) { mutableStateOf(TextFieldValue(profile.roomName)) }
    var savedMessage by remember { mutableStateOf<String?>(null) }

    ScreenScaffold("Perfil", onBack) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(
                modifier = Modifier.size(64.dp).background(WBlue.copy(alpha = .16f), CircleShape),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    profile.nickname.take(1).uppercase().ifBlank { "W" },
                    color = WBlue,
                    fontSize = 28.sp,
                    fontWeight = FontWeight.Bold
                )
            }
            Spacer(Modifier.width(16.dp))
            Column {
                Text(profile.nickname, fontSize = 21.sp, fontWeight = FontWeight.Bold)
                Text("Perfil local • sem conta online", color = WMuted, fontSize = 12.sp)
            }
        }
        Spacer(Modifier.height(12.dp))
        OutlinedTextField(
            modifier = Modifier.fillMaxWidth(),
            value = nickname,
            onValueChange = { nickname = TextFieldValue(it.text.take(24)); savedMessage = null },
            label = { Text("Nome do jogador") },
            singleLine = true,
            shape = RoundedCornerShape(16.dp)
        )
        OutlinedTextField(
            modifier = Modifier.fillMaxWidth(),
            value = roomName,
            onValueChange = { roomName = TextFieldValue(it.text.take(36)); savedMessage = null },
            label = { Text("Nome da hospedagem") },
            singleLine = true,
            shape = RoundedCornerShape(16.dp)
        )
        Button(
            modifier = Modifier.fillMaxWidth(),
            onClick = {
                profile = WudroidProfileStore.save(context, nickname.text, roomName.text)
                nickname = TextFieldValue(profile.nickname)
                roomName = TextFieldValue(profile.roomName)
                savedMessage = "Perfil salvo"
            }
        ) { Text("Salvar perfil", color = Color.Black) }
        if (savedMessage != null) Text(savedMessage!!, color = WGreen, fontSize = 13.sp)
        InfoRow("ID local", profile.localId)
        InfoRow(
            "Uso no multiplayer",
            "Seu nome e o nome da sala aparecem para outros Wudroids conectados à mesma rede local."
        )
    }
}

@Composable
private fun MultiplayerScreen(onBack: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var hosts by remember { mutableStateOf(emptyList<WudroidLanHost>()) }
    var status by remember { mutableStateOf("Procurando salas na rede local…") }

    LaunchedEffect(Unit) {
        while (true) {
            val found = withContext(Dispatchers.IO) { WudroidLanMultiplayer.scanHosts(850) }
            hosts = found
            if (found.isEmpty() && !status.startsWith("Conectado")) {
                status = "Nenhuma sala encontrada ainda"
            }
            delay(1300)
        }
    }

    ScreenScaffold("Multiplayer local", onBack) {
        val profile = WudroidProfileStore.load(context)
        Text(profile.nickname, color = WBlue, fontWeight = FontWeight.Bold)
        Text(status, color = WMuted, fontSize = 13.sp)
        Spacer(Modifier.height(8.dp))
        InfoRow(
            "Rede local",
            "Funciona no mesmo Wi‑Fi ou com o Jogador 1 criando um hotspot. Internet não é necessária."
        )
        if (hosts.isEmpty()) {
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = WCard),
                shape = RoundedCornerShape(16.dp)
            ) {
                Column(Modifier.padding(18.dp)) {
                    Text("Procurando hospedagens…", fontWeight = FontWeight.Bold)
                    Spacer(Modifier.height(4.dp))
                    Text(
                        "Abra um jogo no outro Wudroid e escolha ‘Hospedar multiplayer local’.",
                        color = WMuted,
                        fontSize = 13.sp
                    )
                }
            }
        } else {
            hosts.forEach { host ->
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(containerColor = WCard),
                    shape = RoundedCornerShape(16.dp)
                ) {
                    Column(Modifier.padding(16.dp)) {
                        Text(host.roomName, fontSize = 17.sp, fontWeight = FontWeight.Bold)
                        Text(
                            "Host: ${host.hostName} • ${host.players} jogador(es)",
                            color = WMuted,
                            fontSize = 12.sp
                        )
                        Text(host.address, color = WMuted, fontSize = 11.sp)
                        Spacer(Modifier.height(10.dp))
                        Button(
                            modifier = Modifier.fillMaxWidth(),
                            onClick = {
                                scope.launch {
                                    status = "Conectando a ${host.hostName}…"
                                    val joined = withContext(Dispatchers.IO) {
                                        WudroidLanMultiplayer.joinHost(context, host)
                                    }
                                    status = if (joined) {
                                        "Conectado à sala de ${host.hostName}"
                                    } else "Não foi possível entrar na sala"
                                }
                            }
                        ) { Text("Conectar", color = Color.Black) }
                    }
                }
            }
        }
        Spacer(Modifier.height(10.dp))
        Text(
            "Test1: perfil, descoberta e entrada na sala LAN. Streaming da tela e envio dos controles do segundo aparelho serão ligados na próxima etapa.",
            color = WMuted,
            fontSize = 12.sp,
            lineHeight = 17.sp
        )
    }
}

'''
main = main[:start] + new_controls + main[end:]

main = main.replace('"Wudroid 0.0.8 • frontend independente"', '"Wudroid 0.1.2 • multiplayer local Test1"')
main = main.replace('InfoRow("Wudroid", "0.0.8")', 'InfoRow("Wudroid", "0.1.2")')
main = main.replace('Text("0.0.8", color = WBlue, fontWeight = FontWeight.Bold)', 'Text("0.1.2", color = WBlue, fontWeight = FontWeight.Bold)')

# Emulation host UI + save UI disabled.
screen = ensure_import(screen, 'import info.cemu.cemu.WudroidLanMultiplayer')
context_anchor = '    val wudroidQuickStateContext = LocalContext.current // WUDROID_QUICKSTATE_ENGINE_TEST10\n'
if context_anchor not in screen:
    raise SystemExit('Emulation context anchor missing')
screen = screen.replace(
    context_anchor,
    context_anchor + f'''    // {marker}\n    DisposableEffect(Unit) {{\n        onDispose {{ WudroidLanMultiplayer.stopHost() }}\n    }}\n\n''',
    1,
)

call_anchor = '''                        onQuickSettings = {
                            openQuickDrawer()
                        },
'''
if call_anchor not in screen:
    raise SystemExit('Quick settings call anchor missing')
lan_callback = call_anchor + '''                        onToggleLanHost = {
                            scope.launch {
                                if (WudroidLanMultiplayer.isHosting()) {
                                    WudroidLanMultiplayer.stopHost()
                                    snackbarHostState.showSnackbar("Hospedagem local encerrada")
                                } else {
                                    val started = withContext(Dispatchers.IO) {
                                        WudroidLanMultiplayer.startHost(wudroidQuickStateContext)
                                    }
                                    snackbarHostState.showSnackbar(
                                        if (started) "Hospedagem local aberta na rede"
                                        else "Não foi possível abrir a hospedagem local"
                                    )
                                }
                            }
                        },
'''
screen = screen.replace(call_anchor, lan_callback, 1)

param_anchor = '''    onPauseToggle: () -> Unit,
    onQuickSettings: () -> Unit,
    onQuickSave: () -> Unit,
'''
if param_anchor not in screen:
    raise SystemExit('Side menu param anchor missing')
screen = screen.replace(
    param_anchor,
    '''    onPauseToggle: () -> Unit,
    onQuickSettings: () -> Unit,
    onToggleLanHost: () -> Unit,
    onQuickSave: () -> Unit,
''',
    1,
)

menu_anchor = '''    TextButtonItem(
        label = "Configurações rápidas",
        onClick = onQuickSettings,
    )
'''
if menu_anchor not in screen:
    raise SystemExit('Quick settings menu anchor missing')
screen = screen.replace(
    menu_anchor,
    menu_anchor + '''    TextButtonItem(
        label = "Hospedar / encerrar multiplayer local",
        onClick = onToggleLanHost,
    )
''',
    1,
)

save_start = screen.find('    Text(\n        text = "Save State",')
save_end_marker = '''    TextButtonItem(
        label = "Save Game • 6 slots",
        onClick = onSaveGame,
    )
'''
if save_start < 0:
    raise SystemExit('Save State visible menu block missing')
save_end = screen.find(save_end_marker, save_start)
if save_end < 0:
    raise SystemExit('Save menu end anchor missing')
save_end += len(save_end_marker)
screen = screen[:save_start] + '    // WUDROID_012: save-state UI temporarily disabled while stability work is paused.\n' + screen[save_end:]

permission = '<uses-permission android:name="android.permission.INTERNET" />'
if permission not in manifest:
    first_gt = manifest.find('>')
    if first_gt < 0:
        raise SystemExit('Manifest opening tag malformed')
    manifest = manifest[:first_gt + 1] + '\n    ' + permission + manifest[first_gt + 1:]

main_path.write_text(main)
screen_path.write_text(screen)
manifest_path.write_text(manifest)

checks = {
    main_path: [
        marker,
        'Screen.ControllerPlayer',
        'Screen.Profile',
        'Screen.Multiplayer',
        'Text("Multiplayer"',
        'private fun ProfileScreen(',
        'private fun MultiplayerScreen(',
        'repeat(8) { index ->',
        'WudroidLanMultiplayer.scanHosts',
        'WudroidProfileStore.save',
        '"0.1.2"',
    ],
    screen_path: [
        marker,
        'label = "Hospedar / encerrar multiplayer local"',
        'WudroidLanMultiplayer.startHost',
        'WudroidLanMultiplayer.stopHost',
        'save-state UI temporarily disabled',
    ],
    manifest_path: ['android.permission.INTERNET'],
}
for p, needles in checks.items():
    text = p.read_text()
    missing = [n for n in needles if n not in text]
    if missing:
        raise SystemExit(f'0.1.2 Test1 verification failed for {p}: {missing}')

for forbidden in (
    'label = "Salvar rápido"',
    'label = "Carregar rápido"',
    'label = "Save Game • 6 slots"',
):
    if forbidden in screen:
        raise SystemExit(f'Save UI still visible: {forbidden}')

print('Wudroid 0.1.2 Local Multiplayer Test1 applied')
print('- save-state menu disabled')
print('- Eden-style Players 1..8 menu')
print('- local profile')
print('- LAN host discovery + join handshake')
print('- Multiplayer button in library')
print('- in-game LAN hosting action')
