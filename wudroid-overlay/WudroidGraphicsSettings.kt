package info.cemu.cemu

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import info.cemu.cemu.nativeinterface.NativeSettings

private val GraphicsCard = Color(0xFF15181D)
private val GraphicsBlue = Color(0xFF00B8F5)
private val GraphicsMuted = Color(0xFF9DA8B4)

private data class GraphicsOption(val value: Int, val label: String)

@Composable
fun WudroidGraphicsSettingsPanel() {
    var vsync by remember { mutableIntStateOf(readInt { NativeSettings.getVsyncMode() }) }
    var upscaling by remember { mutableIntStateOf(readInt { NativeSettings.getUpscalingFilter() }) }
    var downscaling by remember { mutableIntStateOf(readInt { NativeSettings.getDownscalingFilter() }) }
    var fullscreenScaling by remember { mutableIntStateOf(readInt { NativeSettings.getFullscreenScaling() }) }

    Text("Gráficos", color = GraphicsBlue, fontWeight = FontWeight.Bold, fontSize = 13.sp)
    Spacer(Modifier.height(6.dp))

    GraphicsInfoRow(
        title = "Resolução interna",
        value = "1X (nativa do jogo)",
        detail = "Resoluções maiores continuam sendo aplicadas por Graphic Packs específicos de cada jogo."
    )

    GraphicsSelectorRow(
        title = "Modo de VSync",
        value = vsyncLabel(vsync),
        selectedValue = vsync,
        detail = "Usa os modos que o backend Cemu Android realmente expõe.",
        options = listOf(
            GraphicsOption(NativeSettings.VSyncMode.OFF, "Imediato (Desligado)"),
            GraphicsOption(NativeSettings.VSyncMode.DOUBLE_BUFFERING, "VSync duplo"),
            GraphicsOption(NativeSettings.VSyncMode.TRIPLE_BUFFERING, "VSync triplo")
        ),
        onSelected = {
            vsync = it
            writeSetting { NativeSettings.setVsyncMode(it) }
        }
    )

    GraphicsSelectorRow(
        title = "Filtro de adaptação da janela",
        value = scalingFilterLabel(upscaling),
        selectedValue = upscaling,
        detail = "Filtro usado quando a imagem precisa ser ampliada.",
        options = scalingFilterOptions(),
        onSelected = {
            upscaling = it
            writeSetting { NativeSettings.setUpscalingFilter(it) }
        }
    )

    GraphicsSelectorRow(
        title = "Filtro de redução",
        value = scalingFilterLabel(downscaling),
        selectedValue = downscaling,
        detail = "Filtro usado quando a imagem precisa ser reduzida.",
        options = scalingFilterOptions(),
        onSelected = {
            downscaling = it
            writeSetting { NativeSettings.setDownscalingFilter(it) }
        }
    )

    GraphicsSelectorRow(
        title = "Escala da tela",
        value = if (fullscreenScaling == NativeSettings.FullscreenScaling.STRETCH) "Esticar" else "Manter proporção",
        selectedValue = fullscreenScaling,
        detail = "Controla como a imagem ocupa a tela do aparelho.",
        options = listOf(
            GraphicsOption(NativeSettings.FullscreenScaling.KEEP_ASPECT_RATIO, "Manter proporção"),
            GraphicsOption(NativeSettings.FullscreenScaling.STRETCH, "Esticar")
        ),
        onSelected = {
            fullscreenScaling = it
            writeSetting { NativeSettings.setFullscreenScaling(it) }
        }
    )

    GraphicsInfoRow(
        title = "Método de Anti-aliasing",
        value = "Padrão do jogo",
        detail = "O core Android atual não expõe anti-aliasing global. Quando houver opção por jogo, ela será ligada aos Graphic Packs."
    )

    GraphicsInfoRow(
        title = "Filtros avançados",
        value = "Vulkan X — em desenvolvimento",
        detail = "FSR, Lanczos, MMPX, Mitchell e outros só entram quando houver implementação real; não foram criados botões falsos."
    )

    Spacer(Modifier.height(8.dp))
}

@Composable
private fun GraphicsSelectorRow(
    title: String,
    value: String,
    selectedValue: Int,
    detail: String,
    options: List<GraphicsOption>,
    onSelected: (Int) -> Unit
) {
    var showDialog by remember { mutableStateOf(false) }

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(bottom = 8.dp)
            .clickable { showDialog = true },
        colors = CardDefaults.cardColors(containerColor = GraphicsCard),
        shape = RoundedCornerShape(15.dp)
    ) {
        Column(Modifier.padding(15.dp)) {
            Text(title, fontSize = 16.sp)
            Spacer(Modifier.height(3.dp))
            Text(value, color = GraphicsBlue, fontWeight = FontWeight.Bold, fontSize = 14.sp)
            Spacer(Modifier.height(3.dp))
            Text(detail, color = GraphicsMuted, fontSize = 11.sp)
        }
    }

    if (showDialog) {
        AlertDialog(
            onDismissRequest = { showDialog = false },
            title = { Text(title) },
            text = {
                Column {
                    options.forEach { option ->
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clickable {
                                    onSelected(option.value)
                                    showDialog = false
                                }
                                .padding(vertical = 5.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            RadioButton(
                                selected = option.value == selectedValue,
                                onClick = null
                            )
                            Text(option.label)
                        }
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = { showDialog = false }) { Text("Cancelar") }
            }
        )
    }
}

@Composable
private fun GraphicsInfoRow(title: String, value: String, detail: String) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(bottom = 8.dp),
        colors = CardDefaults.cardColors(containerColor = GraphicsCard),
        shape = RoundedCornerShape(15.dp)
    ) {
        Column(Modifier.padding(15.dp)) {
            Text(title, fontSize = 16.sp)
            Spacer(Modifier.height(3.dp))
            Text(value, color = GraphicsBlue, fontWeight = FontWeight.Bold, fontSize = 14.sp)
            Spacer(Modifier.height(3.dp))
            Text(detail, color = GraphicsMuted, fontSize = 11.sp)
        }
    }
}

private fun scalingFilterOptions() = listOf(
    GraphicsOption(NativeSettings.ScalingFilter.NEAREST_NEIGHBOR_FILTER, "Nearest Neighbor"),
    GraphicsOption(NativeSettings.ScalingFilter.BILINEAR_FILTER, "Bilinear"),
    GraphicsOption(NativeSettings.ScalingFilter.BICUBIC_FILTER, "Bicubic"),
    GraphicsOption(NativeSettings.ScalingFilter.BICUBIC_HERMITE_FILTER, "Bicubic Hermite")
)

private fun scalingFilterLabel(value: Int): String = when (value) {
    NativeSettings.ScalingFilter.NEAREST_NEIGHBOR_FILTER -> "Nearest Neighbor"
    NativeSettings.ScalingFilter.BICUBIC_FILTER -> "Bicubic"
    NativeSettings.ScalingFilter.BICUBIC_HERMITE_FILTER -> "Bicubic Hermite"
    else -> "Bilinear"
}

private fun vsyncLabel(value: Int): String = when (value) {
    NativeSettings.VSyncMode.OFF -> "Imediato (Desligado)"
    NativeSettings.VSyncMode.TRIPLE_BUFFERING -> "VSync triplo"
    else -> "VSync duplo"
}

private inline fun readInt(block: () -> Int): Int =
    try { block() } catch (_: Throwable) { 0 }

private inline fun writeSetting(block: () -> Unit) {
    try {
        block()
        NativeSettings.saveSettings()
    } catch (_: Throwable) {}
}
