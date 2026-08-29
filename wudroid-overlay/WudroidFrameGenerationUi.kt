package info.cemu.cemu

import android.widget.Toast
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import info.cemu.cemu.nativeinterface.NativeGameTitles

private val FrameGenBlue = Color(0xFF00B8F5)
private val FrameGenMuted = Color(0xFF9DA8B4)

@Composable
fun WudroidFrameGenerationDialog(
    game: NativeGameTitles.Game,
    onDismiss: () -> Unit,
) {
    val context = LocalContext.current
    val titleId = game.titleId
    val scrollState = rememberScrollState()

    var config by remember {
        mutableStateOf(WudroidFrameGenerationManager.gameConfig(context, titleId))
    }
    var dllStatus by remember {
        mutableStateOf(WudroidFrameGenerationManager.losslessDllInfo(context))
    }
    var nativeState by remember {
        mutableStateOf(WudroidFrameGenerationManager.nativeState())
    }

    val dllPicker = rememberLauncherForActivityResult(
        ActivityResultContracts.OpenDocument()
    ) { uri ->
        if (uri == null) return@rememberLauncherForActivityResult
        val result = WudroidFrameGenerationManager.importLosslessDll(context, uri)
        result.onSuccess {
            dllStatus = it
            nativeState = WudroidFrameGenerationManager.nativeState()
            Toast.makeText(context, "Lossless.dll importado", Toast.LENGTH_SHORT).show()
        }.onFailure {
            Toast.makeText(
                context,
                "Falha: ${it.message ?: "DLL inválida"}",
                Toast.LENGTH_LONG,
            ).show()
        }
    }

    fun save(next: WudroidFrameGenerationManager.Config) {
        config = next
        WudroidFrameGenerationManager.saveGameConfig(context, titleId, next)
    }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Frame generation") },
        text = {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(max = 520.dp)
                    .verticalScroll(scrollState),
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Column(Modifier.weight(1f)) {
                        Text(
                            "Frame generation",
                            fontWeight = FontWeight.Bold,
                            fontSize = 18.sp,
                        )
                        Text(
                            "Insere frames interpolados entre os frames renderizados. " +
                                "Quando ativado, o Wudroid usa apresentação FIFO.",
                            color = FrameGenMuted,
                            fontSize = 12.sp,
                        )
                    }
                    Switch(
                        checked = config.enabled,
                        onCheckedChange = { save(config.copy(enabled = it, useGlobal = false)) }
                    )
                }

                Spacer(Modifier.height(8.dp))

                TextButton(
                    onClick = {
                        WudroidFrameGenerationManager.useGlobalForGame(context, titleId)
                        config = WudroidFrameGenerationManager.gameConfig(context, titleId)
                    }
                ) {
                    Text("Usar configuração global")
                }

                HorizontalDivider(Modifier.padding(vertical = 8.dp))

                FrameGenSection("Status")
                Text(
                    WudroidFrameGenerationManager.backendStatusText(context, config),
                    color = if (nativeState.readyForRendererIntegration) FrameGenBlue else FrameGenMuted,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Medium,
                )
                Text(nativeState.engine, color = FrameGenMuted, fontSize = 11.sp)
                Text(
                    if (nativeState.ahbSupported) {
                        "AHardwareBuffer GPU: disponível"
                    } else {
                        "AHardwareBuffer GPU: indisponível"
                    },
                    color = FrameGenMuted,
                    fontSize = 11.sp,
                )

                FrameGenSection("Lossless Scaling")
                Text(dllStatus, color = FrameGenMuted, fontSize = 12.sp)
                Row(modifier = Modifier.fillMaxWidth()) {
                    TextButton(
                        onClick = {
                            dllPicker.launch(
                                arrayOf(
                                    "application/octet-stream",
                                    "application/x-msdownload",
                                    "*/*",
                                )
                            )
                        }
                    ) {
                        Text("Importar Lossless.dll")
                    }
                    if (WudroidFrameGenerationManager.hasLosslessDll(context)) {
                        TextButton(
                            onClick = {
                                WudroidFrameGenerationManager.removeLosslessDll(context)
                                dllStatus = WudroidFrameGenerationManager.losslessDllInfo(context)
                            }
                        ) {
                            Text("Remover")
                        }
                    }
                }
                Text(
                    "O Wudroid não inclui nem baixa Lossless.dll. Use apenas sua própria " +
                        "cópia. O arquivo original escolhido não é apagado.",
                    color = FrameGenMuted,
                    fontSize = 11.sp,
                )

                FrameGenSection("Target frame rate")
                FrameGenRadio(
                    label = "Usar multiplicador fixo",
                    selected =
                        config.targetFps == WudroidFrameGenerationManager.TARGET_FIXED_MULTIPLIER,
                ) {
                    save(
                        config.copy(
                            targetFps = WudroidFrameGenerationManager.TARGET_FIXED_MULTIPLIER,
                            useGlobal = false,
                        )
                    )
                }
                listOf(60, 90, 120, 144, 165).forEach { fps ->
                    FrameGenRadio(
                        label = "$fps FPS",
                        selected = config.targetFps == fps,
                    ) {
                        save(config.copy(targetFps = fps, useGlobal = false))
                    }
                }

                FrameGenSection("Frame multiplier")
                val multiplierEditable =
                    config.targetFps == WudroidFrameGenerationManager.TARGET_FIXED_MULTIPLIER
                if (!multiplierEditable) {
                    Text(
                        "O Target FPS controla o multiplicador automaticamente.",
                        color = FrameGenMuted,
                        fontSize = 11.sp,
                    )
                }
                listOf(2, 3, 4).forEach { multiplier ->
                    FrameGenRadio(
                        label = "${multiplier}x",
                        selected = config.multiplier == multiplier,
                        enabled = multiplierEditable,
                    ) {
                        save(config.copy(multiplier = multiplier, useGlobal = false))
                    }
                }

                FrameGenSection("Frame queue target")
                FrameGenRadio(
                    "Menor latência (sem buffer)",
                    config.queueTarget == WudroidFrameGenerationManager.QUEUE_LOWEST_LATENCY,
                ) {
                    save(
                        config.copy(
                            queueTarget = WudroidFrameGenerationManager.QUEUE_LOWEST_LATENCY,
                            useGlobal = false,
                        )
                    )
                }
                FrameGenRadio(
                    "Balanceado (1 frame)",
                    config.queueTarget == WudroidFrameGenerationManager.QUEUE_BALANCED,
                ) {
                    save(
                        config.copy(
                            queueTarget = WudroidFrameGenerationManager.QUEUE_BALANCED,
                            useGlobal = false,
                        )
                    )
                }
                FrameGenRadio(
                    "Mais suave (2 frames)",
                    config.queueTarget == WudroidFrameGenerationManager.QUEUE_SMOOTHEST,
                ) {
                    save(
                        config.copy(
                            queueTarget = WudroidFrameGenerationManager.QUEUE_SMOOTHEST,
                            useGlobal = false,
                        )
                    )
                }

                FrameGenSwitch(
                    title = "Combinar estimativa de movimento com o jogo",
                    subtitle =
                        "Calcula o movimento na resolução real renderizada pelo jogo, " +
                            "antes de qualquer upscaling.",
                    checked = config.matchMotionToGame,
                ) {
                    save(config.copy(matchMotionToGame = it, useGlobal = false))
                }

                FrameGenSwitch(
                    title = "Shaders de meia precisão",
                    subtitle = "Prefere FP16 quando o driver e o modelo suportarem.",
                    checked = config.halfPrecisionShaders,
                ) {
                    save(config.copy(halfPrecisionShaders = it, useGlobal = false))
                }

                Spacer(Modifier.height(12.dp))
                Text(
                    "Teste 1b: o popup agora rola corretamente e o motor LSFG-VK é " +
                        "linkado ao APK. O status não marca frames como gerados até o " +
                        "hook de apresentação Vulkan do Cemu estar ativo.",
                    color = FrameGenMuted,
                    fontSize = 11.sp,
                )
                Spacer(Modifier.height(6.dp))
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) { Text("Pronto") }
        },
    )
}

@Composable
private fun FrameGenSection(title: String) {
    Spacer(Modifier.height(12.dp))
    Text(
        title,
        color = FrameGenBlue,
        fontWeight = FontWeight.Bold,
        fontSize = 14.sp,
    )
}

@Composable
private fun FrameGenRadio(
    label: String,
    selected: Boolean,
    enabled: Boolean = true,
    onClick: () -> Unit,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(enabled = enabled, onClick = onClick)
            .padding(vertical = 2.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        RadioButton(
            selected = selected,
            onClick = null,
            enabled = enabled,
        )
        Text(
            label,
            color = if (enabled) Color.Unspecified else FrameGenMuted,
        )
    }
}

@Composable
private fun FrameGenSwitch(
    title: String,
    subtitle: String,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(Modifier.weight(1f)) {
            Text(title, fontWeight = FontWeight.Medium)
            Text(subtitle, color = FrameGenMuted, fontSize = 11.sp)
        }
        Switch(
            checked = checked,
            onCheckedChange = onCheckedChange,
        )
    }
}
