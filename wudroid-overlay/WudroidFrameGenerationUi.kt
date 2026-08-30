package info.cemu.cemu

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
    var nativeState by remember {
        mutableStateOf(WudroidFrameGenerationManager.nativeState())
    }

    fun save(next: WudroidFrameGenerationManager.Config) {
        config = next
        WudroidFrameGenerationManager.saveGameConfig(context, titleId, next)
        nativeState = WudroidFrameGenerationManager.nativeState()
    }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Frame generation") },
        text = {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .heightIn(max = 560.dp)
                    .verticalScroll(scrollState),
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Column(Modifier.weight(1f)) {
                        Text("Frame generation", fontWeight = FontWeight.Bold, fontSize = 18.sp)
                        Text(
                            "Gera quadros intermediários direto no Present Vulkan do Wudroid. " +
                                "Não usa captura de tela nem arquivo .dll.",
                            color = FrameGenMuted,
                            fontSize = 12.sp,
                        )
                    }
                    Switch(
                        checked = config.enabled,
                        onCheckedChange = { save(config.copy(enabled = it, useGlobal = false)) },
                    )
                }

                Spacer(Modifier.height(8.dp))
                TextButton(
                    onClick = {
                        WudroidFrameGenerationManager.useGlobalForGame(context, titleId)
                        config = WudroidFrameGenerationManager.gameConfig(context, titleId)
                        nativeState = WudroidFrameGenerationManager.nativeState()
                    }
                ) { Text("Usar configuração global") }

                HorizontalDivider(Modifier.padding(vertical = 8.dp))
                FrameGenSection("Backend Vulkan")
                Text(
                    WudroidFrameGenerationManager.backendStatusText(config),
                    color = if (nativeState.presentHookActive) FrameGenBlue else FrameGenMuted,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Medium,
                )
                Text(nativeState.engine, color = FrameGenMuted, fontSize = 11.sp)
                Text(
                    if (nativeState.opticalFlowAdvertised) {
                        "VK_NV_optical_flow: detectado"
                    } else {
                        "VK_NV_optical_flow: não anunciado pelo driver"
                    },
                    color = FrameGenMuted,
                    fontSize = 11.sp,
                )
                Text(
                    "Quadros sintéticos apresentados: ${nativeState.generatedFrames}",
                    color = FrameGenMuted,
                    fontSize = 11.sp,
                )
                TextButton(onClick = { nativeState = WudroidFrameGenerationManager.nativeState() }) {
                    Text("Atualizar status")
                }

                FrameGenSection("Frame multiplier")
                listOf(2, 3, 4).forEach { multiplier ->
                    FrameGenRadio(
                        label = "${multiplier}x",
                        selected = config.multiplier == multiplier,
                    ) {
                        save(config.copy(multiplier = multiplier, useGlobal = false))
                    }
                }

                FrameGenSection("Perfil")
                val presets = listOf(
                    WudroidFrameGenerationManager.PRESET_ECO,
                    WudroidFrameGenerationManager.PRESET_FLOW,
                    WudroidFrameGenerationManager.PRESET_BALANCED,
                    WudroidFrameGenerationManager.PRESET_BOOST,
                    WudroidFrameGenerationManager.PRESET_CLEAR,
                    WudroidFrameGenerationManager.PRESET_MAX,
                )
                presets.forEach { preset ->
                    FrameGenRadio(
                        label = WudroidFrameGenerationManager.presetName(preset),
                        selected = config.preset == preset,
                    ) {
                        save(
                            config.copy(
                                preset = preset,
                                flowScale = WudroidFrameGenerationManager.defaultScaleForPreset(preset),
                                useGlobal = false,
                            )
                        )
                    }
                }

                Spacer(Modifier.height(8.dp))
                Text(
                    "Test9 usa a arquitetura direta no swapchain inspirada no GameHub. " +
                        "A interpolação desta build é temporal por compute shader; a extensão " +
                        "Optical Flow é detectada para a próxima etapa de compensação de movimento.",
                    color = FrameGenMuted,
                    fontSize = 11.sp,
                )
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) { Text("Pronto") }
        },
    )
}

@Composable
private fun FrameGenSection(title: String) {
    Spacer(Modifier.height(10.dp))
    Text(title, color = FrameGenBlue, fontWeight = FontWeight.Bold, fontSize = 14.sp)
    Spacer(Modifier.height(4.dp))
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
            .clickable(enabled = enabled, onClick = onClick),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        RadioButton(selected = selected, enabled = enabled, onClick = onClick)
        Text(label, color = if (enabled) Color.Unspecified else FrameGenMuted)
    }
}
