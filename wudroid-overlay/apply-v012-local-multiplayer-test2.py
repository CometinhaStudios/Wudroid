#!/usr/bin/env python3
from pathlib import Path

main_path = Path('cemu-engine/src/android/app/src/main/java/info/cemu/cemu/MainActivity.kt')
screen_path = Path('cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationScreen.kt')
for p in (main_path, screen_path):
    if not p.exists():
        raise SystemExit(f'Required source missing: {p}')

main = main_path.read_text()
screen = screen_path.read_text()
marker = 'WUDROID_012_LOCAL_MULTIPLAYER_TEST2'
if marker in main:
    print('Wudroid 0.1.2 Local Multiplayer Test2 already applied')
    raise SystemExit(0)


def ensure_import(source: str, imp: str) -> str:
    if imp in source:
        return source
    lines = source.splitlines(keepends=True)
    idx = [i for i, line in enumerate(lines) if line.startswith('import ')]
    if not idx:
        raise SystemExit('Import block missing')
    lines.insert(idx[-1] + 1, imp + '\n')
    return ''.join(lines)

main = ensure_import(main, 'import androidx.compose.ui.text.input.PasswordVisualTransformation')

profile_start = main.find('@Composable\nprivate fun ProfileScreen(')
profile_end = main.find('\n@Composable\nprivate fun MultiplayerScreen(', profile_start)
if profile_start < 0 or profile_end < 0:
    raise SystemExit('ProfileScreen region missing')

new_profile = r'''@Composable
private fun ProfileScreen(onBack: () -> Unit) {
    // WUDROID_012_LOCAL_MULTIPLAYER_TEST2
    val context = LocalContext.current
    var profile by remember { mutableStateOf(WudroidProfileStore.load(context)) }
    var nickname by remember(profile.localId) {
        mutableStateOf(if (profile.nickname == "Jogador") "" else profile.nickname)
    }
    var savedMessage by remember { mutableStateOf<String?>(null) }

    ScreenScaffold("Perfil", onBack) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(
                modifier = Modifier.size(64.dp).background(WBlue.copy(alpha = .16f), CircleShape),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    nickname.ifBlank { profile.nickname }.take(1).uppercase().ifBlank { "W" },
                    color = WBlue,
                    fontSize = 28.sp,
                    fontWeight = FontWeight.Bold
                )
            }
            Spacer(Modifier.width(16.dp))
            Column {
                Text(
                    nickname.ifBlank { profile.nickname },
                    fontSize = 21.sp,
                    fontWeight = FontWeight.Bold
                )
                Text("Perfil local • sem conta online", color = WMuted, fontSize = 12.sp)
            }
        }

        Spacer(Modifier.height(12.dp))
        OutlinedTextField(
            modifier = Modifier.fillMaxWidth(),
            value = nickname,
            onValueChange = {
                nickname = it.take(24)
                savedMessage = null
            },
            label = { Text("Nome do jogador") },
            placeholder = { Text("Inserir") },
            singleLine = true,
            shape = RoundedCornerShape(16.dp)
        )

        Button(
            modifier = Modifier.fillMaxWidth(),
            onClick = {
                profile = WudroidProfileStore.save(context, nickname)
                nickname = if (profile.nickname == "Jogador") "" else profile.nickname
                savedMessage = "Perfil salvo"
            }
        ) {
            Text("Salvar perfil", color = Color.Black)
        }

        if (savedMessage != null) {
            Text(savedMessage!!, color = WGreen, fontSize = 13.sp)
        }

        InfoRow("ID local", profile.localId)
        InfoRow(
            "Multiplayer",
            "Esse nome aparece para quem encontrar ou entrar na sua sala pela rede local."
        )
    }
}
'''
main = main[:profile_start] + new_profile + main[profile_end:]

mp_start = main.find('@Composable\nprivate fun MultiplayerScreen(')
mp_end = main.find('\n@Composable\nprivate fun GameFoldersScreen(', mp_start)
if mp_start < 0 or mp_end < 0:
    raise SystemExit('MultiplayerScreen region missing')

new_mp = r'''@Composable
private fun MultiplayerScreen(onBack: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var hosts by remember { mutableStateOf(emptyList<WudroidLanHost>()) }
    var status by remember { mutableStateOf("Buscando partidas na rede") }
    var joinedHostName by remember { mutableStateOf<String?>(null) }
    var joinedPlayerNumber by remember { mutableIntStateOf(0) }
    var privateHost by remember { mutableStateOf<WudroidLanHost?>(null) }
    var privatePassword by remember { mutableStateOf("") }

    fun joinRoom(host: WudroidLanHost, password: String) {
        scope.launch {
            status = "Conectando a ${host.roomName}…"
            val result = withContext(Dispatchers.IO) {
                WudroidLanMultiplayer.joinHost(context, host, password)
            }
            when (result.status) {
                WudroidJoinStatus.SUCCESS -> {
                    joinedHostName = host.hostName
                    joinedPlayerNumber = result.playerNumber.coerceAtLeast(2)
                    status = "Conectado como Jogador ${joinedPlayerNumber}"
                    privateHost = null
                    privatePassword = ""
                }
                WudroidJoinStatus.WRONG_PASSWORD -> status = "Senha incorreta"
                WudroidJoinStatus.FULL -> status = "Essa partida já tem um Jogador 2"
                WudroidJoinStatus.FAILED -> status = "Não foi possível entrar na partida"
            }
        }
    }

    LaunchedEffect(joinedHostName) {
        if (joinedHostName == null) {
            while (true) {
                val found = withContext(Dispatchers.IO) {
                    WudroidLanMultiplayer.scanHosts(1100)
                }
                hosts = found
                if (found.isEmpty()) status = "Buscando partidas na rede"
                delay(1600L)
            }
        }
    }

    ScreenScaffold("Multiplayer", onBack) {
        val profile = WudroidProfileStore.load(context)
        Text(profile.nickname, color = WBlue, fontWeight = FontWeight.Bold)

        Row(verticalAlignment = Alignment.CenterVertically) {
            if (joinedHostName == null) {
                CircularProgressIndicator(
                    modifier = Modifier.size(22.dp),
                    strokeWidth = 2.dp,
                    color = WBlue
                )
                Spacer(Modifier.width(10.dp))
            }
            Text(status, color = if (joinedHostName == null) WMuted else WGreen, fontSize = 13.sp)
        }

        Spacer(Modifier.height(6.dp))
        Text(
            "Mesma rede Wi‑Fi ou hotspot do Host • Internet não é necessária",
            color = WMuted,
            fontSize = 12.sp
        )

        if (joinedHostName != null) {
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = WCard),
                shape = RoundedCornerShape(16.dp)
            ) {
                Column(Modifier.padding(18.dp)) {
                    Text("Conectado", color = WGreen, fontWeight = FontWeight.Bold)
                    Text(
                        "Host: $joinedHostName • Você é o Jogador $joinedPlayerNumber",
                        color = WMuted,
                        fontSize = 13.sp
                    )
                    Spacer(Modifier.height(8.dp))
                    Text(
                        "Player 2 reservado no Host. O envio dos controles e a imagem entram na próxima etapa.",
                        color = WMuted,
                        fontSize = 12.sp,
                        lineHeight = 17.sp
                    )
                }
            }
        } else if (hosts.isEmpty()) {
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = WCard),
                shape = RoundedCornerShape(16.dp)
            ) {
                Column(Modifier.padding(18.dp)) {
                    Text("Buscando partidas na rede…", fontWeight = FontWeight.Bold)
                    Spacer(Modifier.height(5.dp))
                    Text(
                        "No outro aparelho, abra um jogo e escolha Multiplayer para criar a sala.",
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
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Column(Modifier.weight(1f)) {
                                Text(host.roomName, fontSize = 18.sp, fontWeight = FontWeight.Bold)
                                Text(
                                    if (host.isPrivate) "Privado • senha necessária" else "Público • sem senha",
                                    color = WMuted,
                                    fontSize = 11.sp
                                )
                            }
                            Text(host.hostName, color = WBlue, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                        }
                        Spacer(Modifier.height(10.dp))
                        Button(
                            modifier = Modifier.fillMaxWidth(),
                            onClick = {
                                if (host.isPrivate) {
                                    privateHost = host
                                    privatePassword = ""
                                } else {
                                    joinRoom(host, "")
                                }
                            }
                        ) {
                            Text("Entrar", color = Color.Black)
                        }
                    }
                }
            }
        }
    }

    val protectedRoom = privateHost
    if (protectedRoom != null) {
        AlertDialog(
            onDismissRequest = {
                privateHost = null
                privatePassword = ""
            },
            title = { Text(protectedRoom.roomName, fontWeight = FontWeight.Bold) },
            text = {
                Column {
                    Text("Partida privada de ${protectedRoom.hostName}", color = WMuted, fontSize = 12.sp)
                    Spacer(Modifier.height(10.dp))
                    OutlinedTextField(
                        modifier = Modifier.fillMaxWidth(),
                        value = privatePassword,
                        onValueChange = { privatePassword = it.take(32) },
                        label = { Text("Senha") },
                        placeholder = { Text("Inserir senha") },
                        visualTransformation = PasswordVisualTransformation(),
                        singleLine = true
                    )
                }
            },
            confirmButton = {
                Button(onClick = { joinRoom(protectedRoom, privatePassword) }) {
                    Text("Entrar", color = Color.Black)
                }
            },
            dismissButton = {
                Button(onClick = {
                    privateHost = null
                    privatePassword = ""
                }) {
                    Text("Cancelar", color = Color.Black)
                }
            }
        )
    }
}
'''
main = main[:mp_start] + new_mp + main[mp_end:]

main = main.replace('Wudroid 0.1.2 • multiplayer local Test1', 'Wudroid 0.1.2 • multiplayer local Test2')
main = main.replace('multiplayer local Test1', 'multiplayer local Test2')

state_anchor = '    // WUDROID_012_LOCAL_MULTIPLAYER_TEST1\n'
state_pos = screen.find(state_anchor)
if state_pos < 0:
    raise SystemExit('Test1 emulation marker missing')
insert_at = state_pos + len(state_anchor)
if 'showWudroidLanHostDialog' not in screen:
    screen = screen[:insert_at] + '    var showWudroidLanHostDialog by remember { mutableStateOf(false) } // WUDROID_012_LOCAL_MULTIPLAYER_TEST2\n' + screen[insert_at:]


def replace_named_lambda(source: str, token: str, replacement: str) -> str:
    start = source.find(token)
    if start < 0:
        raise SystemExit(f'Callback missing: {token}')
    brace = source.find('{', start)
    if brace < 0:
        raise SystemExit(f'Callback opening brace missing: {token}')
    depth = 0
    in_string = False
    escaped = False
    close = -1
    for i in range(brace, len(source)):
        ch = source[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == '\\':
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                close = i + 1
                break
    if close < 0:
        raise SystemExit(f'Callback closing brace missing: {token}')
    return source[:start] + replacement + source[close:]

screen = replace_named_lambda(
    screen,
    'onToggleLanHost = {',
    '''onToggleLanHost = {
                            showWudroidLanHostDialog = true
                            closeDrawer()
                        }'''
)

screen = screen.replace(
    'label = "Hospedar / encerrar multiplayer local"',
    'label = "Multiplayer"',
    1,
)
if 'label = "Multiplayer"' not in screen:
    raise SystemExit('Multiplayer side menu label replacement failed')

dialog_anchor = '    EmulationTextInputDialog()\n'
if dialog_anchor not in screen:
    raise SystemExit('EmulationTextInputDialog anchor missing')
if 'WudroidLanHostDialog(' not in screen:
    dialog_call = '''    if (showWudroidLanHostDialog) {
        WudroidLanHostDialog(
            context = wudroidQuickStateContext,
            onClose = { showWudroidLanHostDialog = false },
        )
    }

'''
    screen = screen.replace(dialog_anchor, dialog_call + dialog_anchor, 1)

for needle in (
    marker,
    'placeholder = { Text("Inserir") }',
    'Buscando partidas na rede',
    'Privado • senha necessária',
    'WudroidLanMultiplayer.joinHost(context, host, password)',
):
    if needle not in main:
        raise SystemExit(f'Test2 MainActivity verification failed: {needle}')

for needle in (
    'showWudroidLanHostDialog',
    'label = "Multiplayer"',
    'WudroidLanHostDialog(',
):
    if needle not in screen:
        raise SystemExit(f'Test2 EmulationScreen verification failed: {needle}')

main_path.write_text(main)
screen_path.write_text(screen)
print('Wudroid 0.1.2 Local Multiplayer Test2 applied')
print('- Perfil: campo Inserir corrigido')
print('- Cliente: busca com spinner, público/privado, host e senha')
print('- Host: lobby persistente, lista de conectados e OK condicionado ao Player 2')
