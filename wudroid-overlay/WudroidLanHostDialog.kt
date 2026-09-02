package info.cemu.cemu.emulation

import android.content.Context
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

private val WudroidLanBlue = Color(0xFF00B8F5)
private val WudroidLanCard = Color(0xFF171B20)
private val WudroidLanMuted = Color(0xFF9DA8B4)
private val WudroidLanGreen = Color(0xFF36D17C)

@Composable
fun WudroidLanHostDialog(
    context: Context,
    onClose: () -> Unit,
) {
    val profile = remember { WudroidProfileStore.load(context) }
    val initialRoom = remember { WudroidLanMultiplayer.hostRoom() }
    var roomName by remember { mutableStateOf(initialRoom?.roomName.orEmpty()) }
    var isPrivate by remember { mutableStateOf(initialRoom?.isPrivate ?: false) }
    var password by remember { mutableStateOf("") }
    var hosting by remember { mutableStateOf(WudroidLanMultiplayer.isHosting()) }
    var error by remember { mutableStateOf<String?>(null) }
    var participants by remember { mutableStateOf(WudroidLanMultiplayer.participants()) }

    LaunchedEffect(hosting) {
        while (hosting) {
            participants = WudroidLanMultiplayer.participants()
            delay(400L)
        }
    }

    AlertDialog(
        onDismissRequest = { if (!hosting) onClose() },
        title = {
            Text(if (hosting) "Multiplayer" else "Criar multiplayer", fontWeight = FontWeight.Bold)
        },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                if (!hosting) {
                    Text("Host: ${profile.nickname}", color = WudroidLanMuted, fontSize = 13.sp)
                    OutlinedTextField(
                        modifier = Modifier.fillMaxWidth(),
                        value = roomName,
                        onValueChange = { roomName = it.take(40); error = null },
                        label = { Text("Nome da partida") },
                        placeholder = { Text("Inserir") },
                        singleLine = true,
                    )
                    Text("Visibilidade", fontWeight = FontWeight.Bold, fontSize = 13.sp)
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Button(
                            modifier = Modifier.weight(1f),
                            onClick = { isPrivate = false; password = "" },
                            colors = ButtonDefaults.buttonColors(containerColor = if (!isPrivate) WudroidLanBlue else WudroidLanCard),
                        ) {
                            Text("Público", color = if (!isPrivate) Color.Black else Color.White)
                        }
                        Button(
                            modifier = Modifier.weight(1f),
                            onClick = { isPrivate = true },
                            colors = ButtonDefaults.buttonColors(containerColor = if (isPrivate) WudroidLanBlue else WudroidLanCard),
                        ) {
                            Text("Privado", color = if (isPrivate) Color.Black else Color.White)
                        }
                    }
                    if (isPrivate) {
                        OutlinedTextField(
                            modifier = Modifier.fillMaxWidth(),
                            value = password,
                            onValueChange = { password = it.take(32); error = null },
                            label = { Text("Senha") },
                            placeholder = { Text("Inserir senha") },
                            visualTransformation = PasswordVisualTransformation(),
                            singleLine = true,
                        )
                    }
                    if (error != null) Text(error!!, color = Color(0xFFFF5A63), fontSize = 12.sp)
                } else {
                    val room: WudroidRoomConfig? = WudroidLanMultiplayer.hostRoom()
                    Text(room?.roomName ?: roomName, fontSize = 18.sp, fontWeight = FontWeight.Bold)
                    Text(
                        if (room?.isPrivate == true) "Privado • com senha" else "Público • sem senha",
                        color = WudroidLanMuted,
                        fontSize = 12.sp,
                    )
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        CircularProgressIndicator(modifier = Modifier.size(22.dp), strokeWidth = 2.dp, color = WudroidLanBlue)
                        Spacer(Modifier.width(10.dp))
                        Text("Aguardando jogador na rede local…", fontSize = 13.sp)
                    }
                    Spacer(Modifier.height(2.dp))
                    Text("Jogadores conectados", fontWeight = FontWeight.Bold)
                    if (participants.isEmpty()) {
                        Text("Nenhum jogador conectado", color = WudroidLanMuted, fontSize = 13.sp)
                    } else {
                        participants.forEach { player ->
                            Row(
                                modifier = Modifier.fillMaxWidth().background(WudroidLanCard, RoundedCornerShape(12.dp)).padding(12.dp),
                                verticalAlignment = Alignment.CenterVertically,
                            ) {
                                Column(Modifier.weight(1f)) {
                                    Text(player.nickname, fontWeight = FontWeight.Bold)
                                    Text(
                                        "Jogador ${player.playerNumber} • " +
                                            if (player.controllerKind == "WIIMOTE") "Wii Remote" else "Pro Controller",
                                        color = WudroidLanMuted,
                                        fontSize = 11.sp
                                    )
                                }
                                Text("Conectado", color = WudroidLanGreen, fontSize = 12.sp)
                            }
                        }
                    }
                }
            }
        },
        confirmButton = {
            if (!hosting) {
                Button(
                    onClick = {
                        if (roomName.isBlank()) {
                            error = "Insira um nome para a partida"
                        } else if (isPrivate && password.isBlank()) {
                            error = "Insira uma senha para a partida privada"
                        } else {
                            val started = WudroidLanMultiplayer.startHost(context, roomName, isPrivate, password)
                            if (started) {
                                hosting = true
                                participants = emptyList()
                                error = null
                            } else {
                                error = "Não foi possível abrir a sala na rede local"
                            }
                        }
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = WudroidLanBlue),
                ) {
                    Text("Hospedar", color = Color.Black, fontWeight = FontWeight.Bold)
                }
            } else {
                Button(
                    enabled = participants.isNotEmpty(),
                    onClick = onClose,
                    colors = ButtonDefaults.buttonColors(containerColor = WudroidLanBlue),
                ) {
                    Text("OK", color = Color.Black, fontWeight = FontWeight.Bold)
                }
            }
        },
        dismissButton = {
            Button(
                onClick = {
                    if (hosting) WudroidLanMultiplayer.stopHost()
                    onClose()
                },
                colors = ButtonDefaults.buttonColors(containerColor = WudroidLanCard),
            ) {
                Text(if (hosting) "Cancelar host" else "Cancelar")
            }
        },
    )
}
