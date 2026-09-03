#!/usr/bin/env python3
from pathlib import Path

main_path = Path("cemu-engine/src/android/app/src/main/java/info/cemu/cemu/MainActivity.kt")
if not main_path.exists():
    raise SystemExit("MainActivity.kt not found")

main = main_path.read_text()
marker = "WUDROID_012_LOCAL_MULTIPLAYER_TEST4"
# WUDROID_012_LOCAL_MULTIPLAYER_TEST5_BUILDFIX3
if marker in main:
    print("Wudroid 0.1.2 Local Multiplayer Test4 already applied")
    raise SystemExit(0)

start = main.find("@Composable\nprivate fun MultiplayerScreen(")
end = main.find("\n@Composable\nprivate fun GameFoldersScreen(", start)
if start < 0 or end < 0:
    raise SystemExit("Test4 MultiplayerScreen region missing")

new_region = r'''@Composable
private fun MultiplayerScreen(onBack: () -> Unit) {
    // WUDROID_012_LOCAL_MULTIPLAYER_TEST4
    // WUDROID_012_LOCAL_MULTIPLAYER_TEST7_BUILDFIX1
    // WUDROID_012_LOCAL_MULTIPLAYER_TEST8
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var hosts by remember { mutableStateOf(emptyList<WudroidLanHost>()) }
    var status by remember { mutableStateOf("Buscando partidas na rede") }
    var joinedHost by remember { mutableStateOf<WudroidLanHost?>(null) }
    var joinedPlayerNumber by remember { mutableIntStateOf(0) }
    var joinedControllerKind by remember { mutableStateOf("PRO") }
    var joinDialogHost by remember { mutableStateOf<WudroidLanHost?>(null) }
    var joinPassword by remember { mutableStateOf("") }
    var joinControllerKind by remember { mutableStateOf("PRO") }

    var lanPermissionGranted by remember {
        mutableStateOf(
            Build.VERSION.SDK_INT < 36 ||
                WudroidLocalHotspot.hasRuntimePermission(context)
        )
    }

    val lanPermissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        lanPermissionGranted = granted
        status =
            if (granted)
                "Buscando partidas na rede"
            else
                "Permita Dispositivos próximos para encontrar partidas locais"
    }

    LaunchedEffect(Unit) {
        if (
            Build.VERSION.SDK_INT >= 36 &&
            !WudroidLocalHotspot.hasRuntimePermission(context)
        ) {
            status = "Permissão de rede local necessária"
            lanPermissionLauncher.launch(
                WudroidLocalHotspot.requiredRuntimePermission()
            )
        }
    }

    DisposableEffect(Unit) {
        onDispose { WudroidLanMultiplayer.leaveHost() }
    }

    fun leaveMultiplayer() {
        WudroidLanMultiplayer.leaveHost()
        joinedHost = null
        joinedPlayerNumber = 0
        onBack()
    }

    fun joinRoom(host: WudroidLanHost, password: String, controllerKind: String) {
        scope.launch {
            val controllerLabel = if (controllerKind == "WIIMOTE") "Wii Remote" else "Pro Controller"
            status = "Conectando a ${host.roomName} como $controllerLabel…"
            val result = withContext(Dispatchers.IO) {
                WudroidLanMultiplayer.joinHost(
                    context = context,
                    host = host,
                    password = password,
                    controllerKind = controllerKind,
                )
            }
            when (result.status) {
                WudroidJoinStatus.SUCCESS -> {
                    joinedHost = host
                    joinedPlayerNumber = result.playerNumber.coerceAtLeast(2)
                    joinedControllerKind = controllerKind
                    status = "Controle remoto conectado • Jogador $joinedPlayerNumber"
                    joinDialogHost = null
                    joinPassword = ""
                }
                WudroidJoinStatus.WRONG_PASSWORD -> status = "Senha incorreta"
                WudroidJoinStatus.FULL -> status = "Essa partida já tem um Jogador 2"
                WudroidJoinStatus.FAILED -> status = "Não foi possível entrar na partida"
            }
        }
    }

    LaunchedEffect(joinedHost, lanPermissionGranted) {
        if (joinedHost == null && lanPermissionGranted) {
            while (true) {
                val found = withContext(Dispatchers.IO) {
                    WudroidLanMultiplayer.scanHosts(1400)
                }
                hosts = found
                status =
                    if (found.isEmpty())
                        "Buscando partidas na rede"
                    else
                        "${found.size} partida(s) encontrada(s)"
                delay(1600L)
            }
        }
    }

    ScreenScaffold("Multiplayer", ::leaveMultiplayer) {
        val profile = WudroidProfileStore.load(context)
        val currentHost = joinedHost

        if (currentHost != null) {
            val controllerLabel = if (joinedControllerKind == "WIIMOTE") "Wii Remote" else "Pro Controller"
            Text("Conectado a ${currentHost.roomName}", color = WGreen, fontWeight = FontWeight.Bold, fontSize = 17.sp)
            Text("${currentHost.hostName} • Jogador $joinedPlayerNumber • $controllerLabel", color = WMuted, fontSize = 12.sp)
            Spacer(Modifier.height(6.dp))

            WudroidLanVideoPreview()

            Text(
                "Streaming LAN experimental • vídeo apenas neste Test8",
                color = WMuted,
                fontSize = 11.sp,
            )

            Spacer(Modifier.height(4.dp))

            if (joinedControllerKind == "WIIMOTE") {
                Text(
                    "Wii Remote remoto ativo. Movimento/giroscópio fica reservado para uma etapa futura.",
                    color = WMuted, fontSize = 12.sp, lineHeight = 17.sp,
                )
                Spacer(Modifier.height(6.dp))
                RemoteLanWiimotePad()
            } else {
                Text(
                    "Pro Controller remoto ativo. A imagem do Host aparece acima dos controles.",
                    color = WMuted, fontSize = 12.sp, lineHeight = 17.sp,
                )
                Spacer(Modifier.height(6.dp))
                RemoteLanControllerPad()
            }

            Spacer(Modifier.height(10.dp))
            Button(
                modifier = Modifier.fillMaxWidth(),
                onClick = {
                    WudroidLanMultiplayer.leaveHost()
                    joinedHost = null
                    joinedPlayerNumber = 0
                    joinedControllerKind = "PRO"
                    status = "Buscando partidas na rede"
                },
                colors = ButtonDefaults.buttonColors(containerColor = WCard2),
            ) { Text("Sair da partida", color = WText) }
        } else {
            Text(profile.nickname, color = WBlue, fontWeight = FontWeight.Bold)

            if (!lanPermissionGranted) {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(containerColor = WCard),
                    shape = RoundedCornerShape(16.dp),
                ) {
                    Column(
                        Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        Text("Acesso à rede local", fontWeight = FontWeight.Bold)
                        Text(
                            "Permita Dispositivos próximos para o Player 2 procurar o Host nesta rede.",
                            color = WMuted,
                            fontSize = 12.sp,
                        )
                        Button(
                            modifier = Modifier.fillMaxWidth(),
                            onClick = {
                                lanPermissionLauncher.launch(
                                    WudroidLocalHotspot.requiredRuntimePermission()
                                )
                            },
                        ) {
                            Text("Permitir", color = Color.Black)
                        }
                    }
                }
            }

            Row(verticalAlignment = Alignment.CenterVertically) {
                if (lanPermissionGranted) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(22.dp),
                        strokeWidth = 2.dp,
                        color = WBlue
                    )
                    Spacer(Modifier.width(10.dp))
                }
                Text(status, color = WMuted, fontSize = 13.sp)
            }
            Spacer(Modifier.height(6.dp))
            Text("Mesma rede Wi‑Fi ou hotspot do Host • Internet não é necessária", color = WMuted, fontSize = 12.sp)

            if (hosts.isEmpty() && lanPermissionGranted) {
                Card(modifier = Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = WCard), shape = RoundedCornerShape(16.dp)) {
                    Column(Modifier.padding(18.dp)) {
                        Text("Buscando partidas na rede…", fontWeight = FontWeight.Bold)
                        Spacer(Modifier.height(5.dp))
                        Text("No outro aparelho, abra um jogo e escolha Multiplayer para criar a sala.", color = WMuted, fontSize = 13.sp)
                    }
                }
            } else if (hosts.isNotEmpty()) {
                hosts.forEach { host ->
                    Card(modifier = Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = WCard), shape = RoundedCornerShape(16.dp)) {
                        Column(Modifier.padding(16.dp)) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Column(Modifier.weight(1f)) {
                                    Text(host.roomName, fontSize = 18.sp, fontWeight = FontWeight.Bold)
                                    Text(if (host.isPrivate) "Privado • senha necessária" else "Público • sem senha", color = WMuted, fontSize = 11.sp)
                                }
                                Text(host.hostName, color = WBlue, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                            }
                            Spacer(Modifier.height(10.dp))
                            Button(
                                modifier = Modifier.fillMaxWidth(),
                                onClick = {
                                    joinDialogHost = host
                                    joinPassword = ""
                                    joinControllerKind = "PRO"
                                }
                            ) { Text("Entrar", color = Color.Black) }
                        }
                    }
                }
            }
        }
    }

    val targetRoom = joinDialogHost
    if (targetRoom != null) {
        AlertDialog(
            onDismissRequest = {
                joinDialogHost = null
                joinPassword = ""
                joinControllerKind = "PRO"
            },
            title = { Text("Escolher controle", fontWeight = FontWeight.Bold) },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Text("${targetRoom.roomName} • Host: ${targetRoom.hostName}", color = WMuted, fontSize = 12.sp)
                    Text("Tipo do Jogador 2", fontWeight = FontWeight.Bold)
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Button(
                            modifier = Modifier.weight(1f),
                            onClick = { joinControllerKind = "PRO" },
                            colors = ButtonDefaults.buttonColors(containerColor = if (joinControllerKind == "PRO") WBlue else WCard2)
                        ) { Text("Pro Controller", color = if (joinControllerKind == "PRO") Color.Black else WText) }
                        Button(
                            modifier = Modifier.weight(1f),
                            onClick = { joinControllerKind = "WIIMOTE" },
                            colors = ButtonDefaults.buttonColors(containerColor = if (joinControllerKind == "WIIMOTE") WBlue else WCard2)
                        ) { Text("Wii Remote", color = if (joinControllerKind == "WIIMOTE") Color.Black else WText) }
                    }
                    Text(
                        if (joinControllerKind == "WIIMOTE")
                            "A, B, 1, 2, +, −, Home e direcional. Sensor de movimento virá depois."
                        else
                            "Controle completo com botões, gatilhos e dois analógicos.",
                        color = WMuted, fontSize = 12.sp, lineHeight = 17.sp,
                    )
                    if (targetRoom.isPrivate) {
                        OutlinedTextField(
                            modifier = Modifier.fillMaxWidth(), value = joinPassword,
                            onValueChange = { joinPassword = it.take(32) },
                            label = { Text("Senha") }, placeholder = { Text("Inserir senha") },
                            visualTransformation = PasswordVisualTransformation(), singleLine = true
                        )
                    }
                }
            },
            confirmButton = {
                Button(onClick = { joinRoom(targetRoom, joinPassword, joinControllerKind) }) {
                    Text("Entrar", color = Color.Black)
                }
            },
            dismissButton = {
                Button(
                    onClick = {
                        joinDialogHost = null
                        joinPassword = ""
                        joinControllerKind = "PRO"
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = WCard2)
                ) { Text("Cancelar", color = WText) }
            }
        )
    }
}

@Composable
private fun RemoteLanWiimotePad() {
    // Test6: sem carcaça branca; somente os botões do Wii Remote.
    Column(
        modifier = Modifier.fillMaxWidth().padding(horizontal = 6.dp, vertical = 8.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                // Wii Remote deitado: direção visual corrigida.
                RemoteLanButton("↑", WudroidWiimoteMapping.RIGHT, Modifier.size(38.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(3.dp)) {
                    RemoteLanButton("←", WudroidWiimoteMapping.UP, Modifier.size(38.dp))
                    Spacer(Modifier.size(38.dp))
                    RemoteLanButton("→", WudroidWiimoteMapping.DOWN, Modifier.size(38.dp))
                }
                RemoteLanButton("↓", WudroidWiimoteMapping.LEFT, Modifier.size(38.dp))
            }

            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                RemoteLanButton("A", WudroidWiimoteMapping.A, Modifier.size(58.dp))
                Spacer(Modifier.height(5.dp))
                RemoteLanButton("B", WudroidWiimoteMapping.B, Modifier.size(width = 62.dp, height = 34.dp))
            }

            Row(horizontalArrangement = Arrangement.spacedBy(5.dp), verticalAlignment = Alignment.CenterVertically) {
                RemoteLanButton("−", WudroidWiimoteMapping.MINUS, Modifier.size(38.dp))
                RemoteLanButton("HOME", WudroidWiimoteMapping.HOME, Modifier.size(width = 64.dp, height = 34.dp))
                RemoteLanButton("+", WudroidWiimoteMapping.PLUS, Modifier.size(38.dp))
            }

            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                RemoteLanButton("1", WudroidWiimoteMapping.ONE, Modifier.size(48.dp))
                Spacer(Modifier.height(6.dp))
                RemoteLanButton("2", WudroidWiimoteMapping.TWO, Modifier.size(48.dp))
            }
        }

        Text(
            "Wii Remote deitado • movimento/IR ficam para a etapa de sensores.",
            color = WMuted,
            fontSize = 11.sp,
            lineHeight = 15.sp,
        )
    }
}

@Composable
private fun RemoteLanControllerPad() {
    var leftX by remember { mutableFloatStateOf(0f) }
    var leftY by remember { mutableFloatStateOf(0f) }
    var rightX by remember { mutableFloatStateOf(0f) }
    var rightY by remember { mutableFloatStateOf(0f) }
    fun sendSticks() { WudroidLanMultiplayer.sendRemoteSticks(leftX, leftY, rightX, rightY) }

    Card(modifier = Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = WCard), shape = RoundedCornerShape(20.dp)) {
        Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(7.dp)) {
                RemoteLanButton("ZL", NativeInput.ProButton.ZL, Modifier.weight(1f))
                RemoteLanButton("L", NativeInput.ProButton.L, Modifier.weight(1f))
                RemoteLanButton("−", NativeInput.ProButton.MINUS, Modifier.weight(1f))
                RemoteLanButton("+", NativeInput.ProButton.PLUS, Modifier.weight(1f))
                RemoteLanButton("R", NativeInput.ProButton.R, Modifier.weight(1f))
                RemoteLanButton("ZR", NativeInput.ProButton.ZR, Modifier.weight(1f))
            }
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
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
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceAround, verticalAlignment = Alignment.CenterVertically) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    RemoteLanStick(label = "L", onChanged = { x, y -> leftX = x; leftY = y; sendSticks() })
                    RemoteLanButton("L3", NativeInput.ProButton.STICKL, Modifier.size(width = 72.dp, height = 42.dp))
                }
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    RemoteLanStick(label = "R", onChanged = { x, y -> rightX = x; rightY = y; sendSticks() })
                    RemoteLanButton("R3", NativeInput.ProButton.STICKR, Modifier.size(width = 72.dp, height = 42.dp))
                }
            }
        }
    }
}

@Composable
private fun RemoteLanButton(label: String, mappingId: Int, modifier: Modifier = Modifier) {
    var pressed by remember(mappingId) { mutableStateOf(false) }
    Box(
        modifier = modifier
            .background(if (pressed) WBlue.copy(alpha = .75f) else WCard2, RoundedCornerShape(15.dp))
            .pointerInput(mappingId) {
                detectTapGestures(onPress = {
                    pressed = true
                    WudroidLanMultiplayer.sendRemoteButton(mappingId, true)
                    try { tryAwaitRelease() } finally {
                        pressed = false
                        WudroidLanMultiplayer.sendRemoteButton(mappingId, false)
                    }
                })
            },
        contentAlignment = Alignment.Center,
    ) {
        Text(label, color = if (pressed) Color.Black else WText, fontWeight = FontWeight.Bold, fontSize = 15.sp)
    }
}

@Composable
private fun RemoteLanStick(label: String, onChanged: (Float, Float) -> Unit) {
    var knob by remember { mutableStateOf(Offset.Zero) }
    Box(
        modifier = Modifier.size(126.dp).pointerInput(label) {
            fun update(position: Offset) {
                val halfW = size.width / 2f
                val halfH = size.height / 2f
                if (halfW <= 0f || halfH <= 0f) return
                var x = ((position.x - halfW) / halfW).coerceIn(-1f, 1f)
                var y = ((position.y - halfH) / halfH).coerceIn(-1f, 1f)
                val magnitude = sqrt(x * x + y * y)
                if (magnitude > 1f) { x /= magnitude; y /= magnitude }
                knob = Offset(x, y)
                onChanged(x, y)
            }
            detectDragGestures(
                onDragStart = { update(it) },
                onDrag = { change, _ -> update(change.position) },
                onDragEnd = { knob = Offset.Zero; onChanged(0f, 0f) },
                onDragCancel = { knob = Offset.Zero; onChanged(0f, 0f) },
            )
        },
        contentAlignment = Alignment.Center,
    ) {
        Canvas(Modifier.fillMaxSize()) {
            val radius = size.minDimension / 2f
            drawCircle(WCard2, radius = radius)
            drawCircle(WLine, radius = radius * .72f, style = Stroke(width = 2.dp.toPx()))
            drawCircle(WBlue, radius = radius * .29f, center = center + Offset(knob.x * radius * .58f, knob.y * radius * .58f))
        }
        Text(label, color = WMuted, fontSize = 11.sp, fontWeight = FontWeight.Bold)
    }
}
'''

main = main[:start] + new_region + main[end:]
main = main.replace("Wudroid 0.1.2 • multiplayer local Test3", "Wudroid 0.1.2 • multiplayer local Test4")
main = main.replace("multiplayer local Test3", "multiplayer local Test4")

required = [
    marker,
    'joinControllerKind = "WIIMOTE"',
    'controllerKind = controllerKind',
    'RemoteLanWiimotePad()',
    'WudroidWiimoteMapping.HOME',
    'WudroidWiimoteMapping.ONE',
]
missing = [x for x in required if x not in main]
if missing:
    raise SystemExit("Test4 verification failed: " + ", ".join(missing))

main_path.write_text(main)
print("Wudroid 0.1.2 Local Multiplayer Test4 applied")
print("- Pro Controller / Wii Remote selector")
print("- Host sets Player 2 controller type from JOIN")
print("- Wii Remote virtual buttons enabled")
