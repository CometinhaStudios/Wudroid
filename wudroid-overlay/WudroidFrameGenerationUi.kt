package info.cemu.cemu

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import info.cemu.cemu.nativeinterface.NativeGameTitles

private val FrameGenMuted = Color(0xFF9DA8B4)
private val FrameGenBlue = Color(0xFF00B8F5)

@Composable
fun WudroidFrameGenerationDialog(game: NativeGameTitles.Game, onDismiss: () -> Unit) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Frame generation") },
        text = {
            Column(Modifier.fillMaxWidth()) {
                Row(Modifier.fillMaxWidth()) {
                    Column(Modifier.weight(1f)) {
                        Text("Frame generation", fontWeight = FontWeight.Bold, fontSize = 18.sp)
                        Text("Mantido no Wudroid, mas desativado nesta build.", color = FrameGenMuted, fontSize = 12.sp)
                    }
                    Switch(checked = false, onCheckedChange = null, enabled = false)
                }
                Spacer(Modifier.height(16.dp))
                Text("Backend", color = FrameGenBlue, fontWeight = FontWeight.Bold)
                Text("Desativado temporariamente", fontWeight = FontWeight.Medium)
                Text(
                    "LSFG, Lossless.dll, MediaProjection e captura externa foram removidos. " +
                        "O menu fica reservado para o Frame Generation nativo futuro do Wudroid.",
                    color = FrameGenMuted,
                    fontSize = 12.sp,
                )
            }
        },
        confirmButton = { TextButton(onClick = onDismiss) { Text("Pronto") } },
    )
}
