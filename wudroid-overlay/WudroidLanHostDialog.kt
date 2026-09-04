package info.cemu.cemu.emulation

import android.content.Context
import android.os.Build
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import info.cemu.cemu.WudroidLanMultiplayer
import info.cemu.cemu.WudroidProfileStore
import info.cemu.cemu.WudroidRoomConfig
import kotlinx.coroutines.delay
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import info.cemu.cemu.WudroidLocalHotspot

private val WudroidLanBlue = Color(0xFF00B8F5)
private val WudroidLanCard = Color(0xFF171B20)
private val WudroidLanMuted = Color(0xFF9DA8B4)
private val WudroidLanGreen = Color(0xFF36D17C)

@Composable
// WUDROID_012H_HOST_MENU_TEST2
fun WudroidLanHostDialog(
    context: Context,
    onClose: () -> Unit,
) {
    val profile = remember { WudroidProfileStore.load(context) }
    val initialRoom = remember { WudroidLanMultiplayer.hostRoom() }

    var roomName by remember { mutableStateOf(initialRoom?.roomName.orEmpty()) }
    var isPrivate by remember { mutableStateOf(initialRoom?.isPrivate ?: false) }
    var password by remember { mutableStateOf("") }

    var useHostWifi by remember {
        mutableStateOf(WudroidLocalHotspot.state().active)
    }

    var hostMode by remember {
        mutableStateOf<String?>(
            if (initialRoom != null) {
                if (WudroidLocalHotspot.state().active) "LOCAL_HOST" else "LAN"
            } else {
                null
            }
        )
    }

    var hosting by remember { mutableStateOf(WudroidLanMultiplayer.isHosting()) }
    var startingHostWifi by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var participants by remember { mutableStateOf(WudroidLanMultiplayer.participants()) }
    var hotspotState by remember { mutableStateOf(WudroidLocalHotspot.state()) }
    var pendingStartUsesHostWifi by remember { mutableStateOf(false) }

    fun finishLanHostStart() {
        val started = WudroidLanMultiplayer.startHost(
            context,
            roomName.trim(),
            isPrivate,
            password,
        )

        if (started) {
            hosting = true
            startingHostWifi = false
            participants = emptyList()
            error = null
        } else {
            startingHostWifi = false
            WudroidLocalHotspot.stop()
            error = "Não foi possível abrir a sala na rede local"
        }
    }

    fun startHostWifiThenRoom() {
        error = null
        startingHostWifi = true

        val requested = WudroidLocalHotspot.start(
            context = context,
            requestedSsid = roomName.trim(),
            isPrivate = isPrivate,
            roomPassword = password,
        ) { ready ->
            hotspotState = WudroidLocalHotspot.state()
            if (ready) {
                finishLanHostStart()
            } else {
                startingHostWifi = false
                error =
                    WudroidLocalHotspot.state().error
                        ?: "Não foi possível criar o Wi-Fi do Host"
            }
        }

        if (!requested) {
            startingHostWifi = false
            error =
                WudroidLocalHotspot.state().error
                    ?: "Não foi possível criar o Wi-Fi do Host"
        }
    }

    val hotspotPermissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        if (granted) {
            if (pendingStartUsesHostWifi) {
                startHostWifiThenRoom()
            } else {
                finishLanHostStart()
            }
        } else {
            startingHostWifi = false
            error = "Permissão de Dispositivos próximos necessária para o multiplayer local"
        }
    }

    LaunchedEffect(hosting) {
        while (hosting) {
            participants = WudroidLanMultiplayer.participants()
            hotspotState = WudroidLocalHotspot.state()
            delay(400L)
        }
    }

    LaunchedEffect(Unit) {
        while (true) {
            hotspotState = WudroidLocalHotspot.state()
            delay(350L)
        }
    }

    AlertDialog(
        onDismissRequest = {
            // Do not destroy an active Host session just because the dialog closes.
            // While hosting, use OK to return to the game or Cancel Host to end it.
            if (!hosting && !startingHostWifi) {
                onClose()
            }
        },
        title = {
            Text(
                when {
                    hosting -> "Multiplayer"
                    hostMode == null -> "Escolha seu Multiplayer"
                    hostMode == "LAN" -> "LAN"
                    else -> "Local Host"
                },
                fontWeight = FontWeight.Bold,
                fontSize = if (!hosting && hostMode == null) 30.sp else 20.sp
            )
        },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                if (!hosting) {
                    if (hostMode == null) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(18.dp),
                        ) {
                            Button(
                                modifier = Modifier
                                    .weight(1f)
                                    .height(132.dp),
                                onClick = {
                                    useHostWifi = false
                                    hostMode = "LAN"
                                    error = null
                                },
                                colors = ButtonDefaults.buttonColors(
                                    containerColor = WudroidLanCard
                                ),
                                shape = RoundedCornerShape(20.dp),
                            ) {
                                Text(
                                    "LAN",
                                    color = WudroidLanBlue,
                                    fontSize = 30.sp,
                                    fontWeight = FontWeight.Bold,
                                )
                            }

                            Button(
                                modifier = Modifier
                                    .weight(1f)
                                    .height(132.dp),
                                onClick = {
                                    useHostWifi = true
                                    hostMode = "LOCAL_HOST"
                                    error = null
                                },
                                colors = ButtonDefaults.buttonColors(
                                    containerColor = WudroidLanCard
                                ),
                                shape = RoundedCornerShape(20.dp),
                            ) {
                                Text(
                                    "Local Host",
                                    color = WudroidLanGreen,
                                    fontSize = 28.sp,
                                    fontWeight = FontWeight.Bold,
                                )
                            }
                        }
} else {
                    Text(
                        "Host: ${profile.nickname}",
                        color = WudroidLanMuted,
                        fontSize = 13.sp
                    )

                    OutlinedTextField(
                        modifier = Modifier.fillMaxWidth(),
                        value = roomName,
                        onValueChange = {
                            roomName = it.take(40)
                            error = null
                        },
                        label = { Text("Nome da partida") },
                        placeholder = { Text("Inserir") },
                        enabled = !startingHostWifi,
                        singleLine = true,
                    )

                    Text(
                        "Visibilidade",
                        fontWeight = FontWeight.Bold,
                        fontSize = 13.sp
                    )

                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Button(
                            modifier = Modifier.weight(1f),
                            enabled = !startingHostWifi,
                            onClick = {
                                isPrivate = false
                                password = ""
                                error = null
                            },
                            colors = ButtonDefaults.buttonColors(
                                containerColor =
                                    if (!isPrivate) WudroidLanBlue else WudroidLanCard
                            ),
                        ) {
                            Text(
                                "Público",
                                color = if (!isPrivate) Color.Black else Color.White
                            )
                        }

                        Button(
                            modifier = Modifier.weight(1f),
                            enabled = !startingHostWifi,
                            onClick = {
                                isPrivate = true
                                error = null
                            },
                            colors = ButtonDefaults.buttonColors(
                                containerColor =
                                    if (isPrivate) WudroidLanBlue else WudroidLanCard
                            ),
                        ) {
                            Text(
                                "Privado",
                                color = if (isPrivate) Color.Black else Color.White
                            )
                        }
                    }

                    if (isPrivate) {
                        OutlinedTextField(
                            modifier = Modifier.fillMaxWidth(),
                            value = password,
                            onValueChange = {
                                password = it.take(63)
                                error = null
                            },
                            label = { Text("Senha") },
                            placeholder = {
                                Text(
                                    if (useHostWifi && Build.VERSION.SDK_INT >= 36)
                                        "8 a 63 caracteres"
                                    else
                                        "Inserir senha"
                                )
                            },
                            enabled = !startingHostWifi,
                            visualTransformation = PasswordVisualTransformation(),
                            singleLine = true,
                        )
                    }

                    Text(
                        "Modo",
                        fontWeight = FontWeight.Bold,
                        fontSize = 13.sp
                    )

                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .background(WudroidLanCard, RoundedCornerShape(12.dp))
                            .padding(12.dp),
                        verticalArrangement = Arrangement.spacedBy(4.dp),
                    ) {
                        Text(
                            if (useHostWifi) "Local Host" else "LAN",
                            color = if (useHostWifi) WudroidLanGreen else WudroidLanBlue,
                            fontWeight = FontWeight.Bold,
                            fontSize = 14.sp,
                        )
                        Text(
                            if (useHostWifi)
                                "O Wudroid cria a rede local para o Player 2 conectar."
                            else
                                "Usa a rede Wi‑Fi em que os dois aparelhos já estão conectados.",
                            color = WudroidLanMuted,
                            fontSize = 11.sp,
                        )
                    }

                    if (useHostWifi) {
                        Column(
                            modifier = Modifier
                                .fillMaxWidth()
                                .background(
                                    WudroidLanCard,
                                    RoundedCornerShape(12.dp)
                                )
                                .padding(12.dp),
                            verticalArrangement = Arrangement.spacedBy(5.dp),
                        ) {
                            if (Build.VERSION.SDK_INT >= 36) {
                                Text(
                                    "Android 16 • configuração direta",
                                    color = WudroidLanGreen,
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 12.sp
                                )
                                Text(
                                    "Rede: ${roomName.trim().ifBlank { "mesmo nome da partida" }}",
                                    fontSize = 12.sp
                                )
                                Text(
                                    if (isPrivate)
                                        "Privado: a senha da rede será a mesma da partida"
                                    else
                                        "Público: a rede será aberta, sem senha",
                                    color = WudroidLanMuted,
                                    fontSize = 11.sp,
                                )
                            } else {
                                Text(
                                    "Android 15 ou anterior",
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 12.sp
                                )
                                Text(
                                    "Nessa versão do Android, o sistema escolhe o nome/senha do hotspot. O Wudroid mostra os dados quando a rede abrir.",
                                    color = WudroidLanMuted,
                                    fontSize = 11.sp,
                                )
                            }
                        }
                    } else {
                        Text(
                            "Os dois aparelhos precisam estar no mesmo Wi-Fi ou hotspot externo.",
                            color = WudroidLanMuted,
                            fontSize = 11.sp,
                        )
                    }

                    if (startingHostWifi) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(20.dp),
                                strokeWidth = 2.dp,
                                color = WudroidLanBlue
                            )
                            Spacer(Modifier.width(9.dp))
                            Text(
                                "Criando Wi-Fi do Host…",
                                color = WudroidLanMuted,
                                fontSize = 12.sp
                            )
                        }
                    }

                    if (error != null) {
                        Text(
                            error!!,
                            color = Color(0xFFFF5A63),
                            fontSize = 12.sp
                        )
                    }
                    }
                } else {
                    val room: WudroidRoomConfig? =
                        WudroidLanMultiplayer.hostRoom()

                    Text(
                        room?.roomName ?: roomName,
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Bold
                    )

                    Text(
                        if (room?.isPrivate == true)
                            "Privado • com senha"
                        else
                            "Público • sem senha",
                        color = WudroidLanMuted,
                        fontSize = 12.sp,
                    )

                    if (hotspotState.active) {
                        Column(
                            modifier = Modifier
                                .fillMaxWidth()
                                .background(
                                    WudroidLanCard,
                                    RoundedCornerShape(12.dp)
                                )
                                .padding(12.dp),
                            verticalArrangement = Arrangement.spacedBy(4.dp),
                        ) {
                            Text(
                                "Wi-Fi do Host ativo",
                                color = WudroidLanGreen,
                                fontWeight = FontWeight.Bold
                            )
                            Text(
                                "Rede: ${hotspotState.ssid}",
                                fontSize = 13.sp
                            )

                            if (hotspotState.password.isBlank()) {
                                Text(
                                    "Rede aberta • sem senha",
                                    fontSize = 13.sp
                                )
                            } else {
                                Text(
                                    "Senha: ${hotspotState.password}",
                                    fontSize = 13.sp
                                )
                            }

                            Text(
                                "Essa rede continua ligada quando você toca OK e volta ao jogo.",
                                color = WudroidLanMuted,
                                fontSize = 11.sp,
                            )
                        }
                    }

                    Row(verticalAlignment = Alignment.CenterVertically) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(22.dp),
                            strokeWidth = 2.dp,
                            color = WudroidLanBlue
                        )
                        Spacer(Modifier.width(10.dp))
                        Text(
                            "Aguardando jogador na rede local…",
                            fontSize = 13.sp
                        )
                    }

                    Spacer(Modifier.height(2.dp))
                    Text(
                        "Jogadores conectados",
                        fontWeight = FontWeight.Bold
                    )

                    if (participants.isEmpty()) {
                        Text(
                            "Nenhum jogador conectado",
                            color = WudroidLanMuted,
                            fontSize = 13.sp
                        )
                    } else {
                        participants.forEach { player ->
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .background(
                                        WudroidLanCard,
                                        RoundedCornerShape(12.dp)
                                    )
                                    .padding(12.dp),
                                verticalAlignment = Alignment.CenterVertically,
                            ) {
                                Column(Modifier.weight(1f)) {
                                    Text(
                                        player.nickname,
                                        fontWeight = FontWeight.Bold
                                    )
                                    Text(
                                        "Jogador ${player.playerNumber} • " +
                                            if (player.controllerKind == "WIIMOTE")
                                                "Wii Remote"
                                            else
                                                "Pro Controller",
                                        color = WudroidLanMuted,
                                        fontSize = 11.sp
                                    )
                                }

                                Text(
                                    "Conectado",
                                    color = WudroidLanGreen,
                                    fontSize = 12.sp
                                )
                            }
                        }
                    }
                }
            }
        },
        confirmButton = {
            if (!hosting) {
                if (hostMode != null) {
                Button(
                    enabled = !startingHostWifi,
                    onClick = {
                        error = null

                        val cleanRoom = roomName.trim()
                        val roomBytes =
                            cleanRoom.toByteArray(Charsets.UTF_8).size
                        val passBytes =
                            password.toByteArray(Charsets.UTF_8).size

                        when {
                            cleanRoom.isBlank() -> {
                                error = "Insira um nome para a partida"
                            }

                            isPrivate && password.isBlank() -> {
                                error = "Insira uma senha para a partida privada"
                            }

                            useHostWifi &&
                                Build.VERSION.SDK_INT >= 36 &&
                                roomBytes !in 1..32 -> {
                                error =
                                    "Para usar Wi-Fi do Host, o nome precisa ter até 32 bytes"
                            }

                            useHostWifi &&
                                Build.VERSION.SDK_INT >= 36 &&
                                isPrivate &&
                                passBytes !in 8..63 -> {
                                error =
                                    "No Host privado, a senha precisa ter de 8 a 63 bytes"
                            }

                            useHostWifi -> {
                                pendingStartUsesHostWifi = true
                                if (
                                    WudroidLocalHotspot
                                        .hasRuntimePermission(context)
                                ) {
                                    startHostWifiThenRoom()
                                } else {
                                    startingHostWifi = true
                                    hotspotPermissionLauncher.launch(
                                        WudroidLocalHotspot
                                            .requiredRuntimePermission()
                                    )
                                }
                            }

                            else -> {
                                pendingStartUsesHostWifi = false
                                if (
                                    Build.VERSION.SDK_INT >= 36 &&
                                    !WudroidLocalHotspot
                                        .hasRuntimePermission(context)
                                ) {
                                    hotspotPermissionLauncher.launch(
                                        WudroidLocalHotspot
                                            .requiredRuntimePermission()
                                    )
                                } else {
                                    finishLanHostStart()
                                }
                            }
                        }
                    },
                    colors = ButtonDefaults.buttonColors(
                        containerColor = WudroidLanBlue
                    ),
                ) {
                    Text(
                        if (startingHostWifi)
                            "Criando…"
                        else
                            "Hospedar",
                        color = Color.Black,
                        fontWeight = FontWeight.Bold
                    )
                }
                }
            } else {
                Button(
                    enabled = participants.isNotEmpty(),
                    onClick = onClose,
                    colors = ButtonDefaults.buttonColors(
                        containerColor = WudroidLanBlue
                    ),
                ) {
                    Text(
                        "OK",
                        color = Color.Black,
                        fontWeight = FontWeight.Bold
                    )
                }
            }
        },
        dismissButton = {
            Button(
                onClick = {
                    when {
                        hosting -> {
                            // Explicit end of Host session = stop room + hotspot.
                            WudroidLanMultiplayer.stopHost()
                            onClose()
                        }
                        startingHostWifi -> {
                            // Cancels a pending AP request via generation token.
                            WudroidLocalHotspot.stop()
                            startingHostWifi = false
                            onClose()
                        }
                        hostMode != null -> {
                            hostMode = null
                            useHostWifi = false
                            error = null
                        }
                        else -> onClose()
                    }
                },
                colors = ButtonDefaults.buttonColors(
                    containerColor = WudroidLanCard
                ),
            ) {
                Text(
                    when {
                        hosting -> "Cancelar host"
                        hostMode != null && !startingHostWifi -> "Voltar"
                        else -> "Cancelar"
                    }
                )
            }
        },
    )
}
