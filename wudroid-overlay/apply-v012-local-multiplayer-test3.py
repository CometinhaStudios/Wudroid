#!/usr/bin/env python3
from pathlib import Path

main_path = Path('cemu-engine/src/android/app/src/main/java/info/cemu/cemu/MainActivity.kt')
if not main_path.exists():
    raise SystemExit('MainActivity.kt not found')

main = main_path.read_text()
marker = 'WUDROID_012_LOCAL_MULTIPLAYER_TEST3'

if marker in main:
    print('Wudroid 0.1.2 Local Multiplayer Test3 already applied')
    raise SystemExit(0)

def ensure_import(source: str, imp: str) -> str:
    if imp in source:
        return source
    lines = source.splitlines(keepends=True)
    indexes = [i for i, line in enumerate(lines) if line.startswith('import ')]
    if not indexes:
        raise SystemExit('MainActivity import block missing')
    lines.insert(indexes[-1] + 1, imp + '\n')
    return ''.join(lines)

for imp in (
    'import androidx.compose.foundation.gestures.detectDragGestures',
    'import androidx.compose.foundation.gestures.detectTapGestures',
    'import androidx.compose.runtime.DisposableEffect',
    'import androidx.compose.ui.input.pointer.pointerInput',
    'import kotlin.math.sqrt',
):
    main = ensure_import(main, imp)

start = main.find('@Composable\nprivate fun MultiplayerScreen(')
end = main.find('\n@Composable\nprivate fun GameFoldersScreen(', start)
if start < 0 or end < 0:
    raise SystemExit('MultiplayerScreen region missing')

new_multiplayer = r'''@Composable
private fun MultiplayerScreen(onBack: () -> Unit) {
    // WUDROID_012_LOCAL_MULTIPLAYER_TEST3
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var hosts by remember { mutableStateOf(emptyList<WudroidLanHost>()) }
    var status by remember { mutableStateOf("Buscando partidas na rede") }
    var joinedHost by remember { mutableStateOf<WudroidLanHost?>(null) }
    var joinedPlayerNumber by remember { mutableIntStateOf(0) }
    var privateHost by remember { mutableStateOf<WudroidLanHost?>(null) }
    var privatePassword by remember { mutableStateOf("") }

    DisposableEffect(Unit) {
        onDispose {
            WudroidLanMultiplayer.leaveHost()
        }
    }

    fun leaveMultiplayer() {
        WudroidLanMultiplayer.leaveHost()
        joinedHost = null
        joinedPlayerNumber = 0
        onBack()
    }

    fun joinRoom(host: WudroidLanHost, password: String) {
        scope.launch {
            status = "Conectando a ${host.roomName}…"
            val result = withContext(Dispatchers.IO) {
                WudroidLanMultiplayer.joinHost(context, host, password)
            }
            when (result.status) {
                WudroidJoinStatus.SUCCESS -> {
                    joinedHost = host
                    joinedPlayerNumber = result.playerNumber.coerceAtLeast(2)
                    status = "Controle remoto conectado • Jogador $joinedPlayerNumber"
                    privateHost = null
                    privatePassword = ""
                }
                WudroidJoinStatus.WRONG_PASSWORD -> status = "Senha incorreta"
                WudroidJoinStatus.FULL -> status = "Essa partida já tem um Jogador 2"
                WudroidJoinStatus.FAILED -> status = "Não foi possível entrar na partida"
            }
        }
    }

    LaunchedEffect(joinedHost) {
        if (joinedHost == null) {
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

    ScreenScaffold("Multiplayer", ::leaveMultiplayer) {
        val profile = WudroidProfileStore.load(context)
        val currentHost = joinedHost

        if (currentHost != null) {
            Text(
                "Conectado a ${currentHost.roomName}",
                color = WGreen,
                fontWeight = FontWeight.Bold,
                fontSize = 17.sp,
            )
            Text(
                "${currentHost.hostName} • Você é o Jogador $joinedPlayerNumber",
                color = WMuted,
                fontSize = 12.sp,
            )
            Spacer(Modifier.height(4.dp))
            Text(
                "Controle remoto LAN ativo. Olhe a tela do Host enquanto o streaming ainda não está disponível.",
                color = WMuted,
                fontSize = 12.sp,
                lineHeight = 17.sp,
            )
            Spacer(Modifier.height(6.dp))

            RemoteLanControllerPad()

            Spacer(Modifier.height(10.dp))
            Button(
                modifier = Modifier.fillMaxWidth(),
                onClick = {
                    WudroidLanMultiplayer.leaveHost()
                    joinedHost = null
                    joinedPlayerNumber = 0
                    status = "Buscando partidas na rede"
                },
                colors = ButtonDefaults.buttonColors(containerColor = WCard2),
            ) {
                Text("Sair da partida", color = WText)
            }
        } else {
            Text(profile.nickname, color = WBlue, fontWeight = FontWeight.Bold)

            Row(verticalAlignment = Alignment.CenterVertically) {
                CircularProgressIndicator(
                    modifier = Modifier.size(22.dp),
                    strokeWidth = 2.dp,
                    color = WBlue
                )
                Spacer(Modifier.width(10.dp))
                Text(status, color = WMuted, fontSize = 13.sp)
            }

            Spacer(Modifier.height(6.dp))
            Text(
                "Mesma rede Wi‑Fi ou hotspot do Host • Internet não é necessária",
                color = WMuted,
                fontSize = 12.sp
            )

            if (hosts.isEmpty()) {
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
                                        if (host.isPrivate)
                                            "Privado • senha necessária"
                                        else
                                            "Público • sem senha",
                                        color = WMuted,
                                        fontSize = 11.sp
                                    )
                                }
                                Text(
                                    host.hostName,
                                    color = WBlue,
                                    fontSize = 12.sp,
                                    fontWeight = FontWeight.Bold
                                )
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
                    Text(
                        "Partida privada de ${protectedRoom.hostName}",
                        color = WMuted,
                        fontSize = 12.sp
                    )
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

@Composable
private fun RemoteLanControllerPad() {
    var leftX by remember { mutableFloatStateOf(0f) }
    var leftY by remember { mutableFloatStateOf(0f) }
    var rightX by remember { mutableFloatStateOf(0f) }
    var rightY by remember { mutableFloatStateOf(0f) }

    fun sendSticks() {
        WudroidLanMultiplayer.sendRemoteSticks(leftX, leftY, rightX, rightY)
    }

    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = WCard),
        shape = RoundedCornerShape(20.dp),
    ) {
        Column(
            modifier = Modifier.padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(7.dp),
            ) {
                RemoteLanButton("ZL", NativeInput.ProButton.ZL, Modifier.weight(1f))
                RemoteLanButton("L", NativeInput.ProButton.L, Modifier.weight(1f))
                RemoteLanButton("−", NativeInput.ProButton.MINUS, Modifier.weight(1f))
                RemoteLanButton("+", NativeInput.ProButton.PLUS, Modifier.weight(1f))
                RemoteLanButton("R", NativeInput.ProButton.R, Modifier.weight(1f))
                RemoteLanButton("ZR", NativeInput.ProButton.ZR, Modifier.weight(1f))
            }

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    RemoteLanButton("↑", NativeInput.ProButton.UP, Modifier.size(56.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                        RemoteLanButton("←", NativeInput.ProButton.LEFT, Modifier.size(56.dp))
                        Spacer(Modifier.size(56.dp))
                        RemoteLanButton("→", NativeInput.ProButton.RIGHT, Modifier.size(56.dp))
                    }
                    RemoteLanButton("↓", NativeInput.ProButton.DOWN, Modifier.size(56.dp))
                }

                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    RemoteLanButton("X", NativeInput.ProButton.X, Modifier.size(58.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        RemoteLanButton("Y", NativeInput.ProButton.Y, Modifier.size(58.dp))
                        Spacer(Modifier.size(58.dp))
                        RemoteLanButton("A", NativeInput.ProButton.A, Modifier.size(58.dp))
                    }
                    RemoteLanButton("B", NativeInput.ProButton.B, Modifier.size(58.dp))
                }
            }

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceAround,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    RemoteLanStick(
                        label = "L",
                        onChanged = { x, y ->
                            leftX = x
                            leftY = y
                            sendSticks()
                        },
                    )
                    RemoteLanButton(
                        "L3",
                        NativeInput.ProButton.STICKL,
                        Modifier.size(width = 72.dp, height = 42.dp),
                    )
                }

                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    RemoteLanStick(
                        label = "R",
                        onChanged = { x, y ->
                            rightX = x
                            rightY = y
                            sendSticks()
                        },
                    )
                    RemoteLanButton(
                        "R3",
                        NativeInput.ProButton.STICKR,
                        Modifier.size(width = 72.dp, height = 42.dp),
                    )
                }
            }
        }
    }
}

@Composable
private fun RemoteLanButton(
    label: String,
    mappingId: Int,
    modifier: Modifier = Modifier,
) {
    var pressed by remember(mappingId) { mutableStateOf(false) }

    Box(
        modifier = modifier
            .background(
                if (pressed) WBlue.copy(alpha = .75f) else WCard2,
                RoundedCornerShape(15.dp),
            )
            .pointerInput(mappingId) {
                detectTapGestures(
                    onPress = {
                        pressed = true
                        WudroidLanMultiplayer.sendRemoteButton(mappingId, true)
                        try {
                            tryAwaitRelease()
                        } finally {
                            pressed = false
                            WudroidLanMultiplayer.sendRemoteButton(mappingId, false)
                        }
                    }
                )
            },
        contentAlignment = Alignment.Center,
    ) {
        Text(
            label,
            color = if (pressed) Color.Black else WText,
            fontWeight = FontWeight.Bold,
            fontSize = 15.sp,
        )
    }
}

@Composable
private fun RemoteLanStick(
    label: String,
    onChanged: (Float, Float) -> Unit,
) {
    var knob by remember { mutableStateOf(Offset.Zero) }

    Box(
        modifier = Modifier
            .size(126.dp)
            .pointerInput(label) {
                fun update(position: Offset) {
                    val halfW = size.width / 2f
                    val halfH = size.height / 2f
                    if (halfW <= 0f || halfH <= 0f) return

                    var x = ((position.x - halfW) / halfW).coerceIn(-1f, 1f)
                    var y = ((position.y - halfH) / halfH).coerceIn(-1f, 1f)

                    val magnitude = sqrt(x * x + y * y)
                    if (magnitude > 1f) {
                        x /= magnitude
                        y /= magnitude
                    }

                    knob = Offset(x, y)
                    onChanged(x, y)
                }

                detectDragGestures(
                    onDragStart = { update(it) },
                    onDrag = { change, _ -> update(change.position) },
                    onDragEnd = {
                        knob = Offset.Zero
                        onChanged(0f, 0f)
                    },
                    onDragCancel = {
                        knob = Offset.Zero
                        onChanged(0f, 0f)
                    },
                )
            },
        contentAlignment = Alignment.Center,
    ) {
        Canvas(Modifier.fillMaxSize()) {
            val radius = size.minDimension / 2f
            drawCircle(WCard2, radius = radius)
            drawCircle(
                WLine,
                radius = radius * .72f,
                style = Stroke(width = 2.dp.toPx()),
            )
            drawCircle(
                WBlue,
                radius = radius * .29f,
                center = center + Offset(
                    knob.x * radius * .58f,
                    knob.y * radius * .58f,
                ),
            )
        }
        Text(label, color = WMuted, fontSize = 11.sp, fontWeight = FontWeight.Bold)
    }
}
'''

main = main[:start] + new_multiplayer + main[end:]
main = main.replace('Wudroid 0.1.2 • multiplayer local Test2', 'Wudroid 0.1.2 • multiplayer local Test3')
main = main.replace('multiplayer local Test2', 'multiplayer local Test3')

for needle in (
    marker,
    'RemoteLanControllerPad()',
    'WudroidLanMultiplayer.sendRemoteButton',
    'WudroidLanMultiplayer.sendRemoteSticks',
    'NativeInput.ProButton.A',
    'NativeInput.ProButton.STICKL',
    'Controle remoto LAN ativo',
):
    if needle not in main:
        raise SystemExit(f'Test3 verification failed: {needle}')

main_path.write_text(main)
print('Wudroid 0.1.2 Local Multiplayer Test3 applied')
print('- Player 2 remote controller UI')
print('- A/B/X/Y, D-pad, shoulders, +/- and two analog sticks')
print('- remote commands sent through LAN to Host')
