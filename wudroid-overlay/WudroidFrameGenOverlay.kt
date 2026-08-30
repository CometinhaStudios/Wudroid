package info.cemu.cemu.framegen

import android.app.Activity
import android.view.Gravity
import android.view.ViewGroup
import android.widget.FrameLayout
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectHorizontalDragGestures
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.weight
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Slider
import androidx.compose.material3.Surface
import androidx.compose.material3.Switch
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
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.ComposeView
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.delay

object WudroidFrameGenOverlay {
    private fun dp(activity: Activity, value: Int): Int =
        (value * activity.resources.displayMetrics.density).toInt()

    fun attach(activity: Activity, onOpenChanged: (Boolean) -> Unit = {}) {
        val root = activity.findViewById<FrameLayout>(android.R.id.content) ?: return
        if (root.findViewWithTag<ComposeView>("wudroid-framegen-overlay") != null) return

        val compose = ComposeView(activity).apply {
            tag = "wudroid-framegen-overlay"
        }
        val closedWidth = dp(activity, 34)
        val params = FrameLayout.LayoutParams(closedWidth, ViewGroup.LayoutParams.MATCH_PARENT).apply {
            gravity = Gravity.END
        }
        root.addView(compose, params)

        compose.setContent {
            MaterialTheme {
                WudroidFrameGenPanel(activity) { open ->
                    val lp = compose.layoutParams as FrameLayout.LayoutParams
                    lp.width = if (open) ViewGroup.LayoutParams.MATCH_PARENT else closedWidth
                    lp.gravity = Gravity.END
                    compose.layoutParams = lp
                    onOpenChanged(open)
                }
            }
        }
    }
}

@Composable
private fun WudroidFrameGenPanel(activity: Activity, onOpenChanged: (Boolean) -> Unit) {
    var open by remember { mutableStateOf(false) }
    var config by remember { mutableStateOf(WudroidNativeFrameGen.load(activity)) }
    var status by remember { mutableStateOf(0) }
    var fps by remember { mutableStateOf(intArrayOf(0, 0, 0)) }
    var nvFlow by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf("") }

    fun setOpen(next: Boolean) {
        open = next
        onOpenChanged(next)
    }
    fun save(next: WudroidNativeFrameGen.Config) {
        config = next
        WudroidNativeFrameGen.saveAndApply(activity, next)
    }

    LaunchedEffect(open) {
        while (true) {
            status = WudroidNativeFrameGenBridge.statusCode()
            fps = WudroidNativeFrameGenBridge.fps()
            nvFlow = WudroidNativeFrameGenBridge.hasNvOpticalFlow()
            error = WudroidNativeFrameGenBridge.lastError()
            delay(if (open) 350 else 1000)
        }
    }

    if (!open) {
        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.CenterEnd) {
            Box(
                Modifier
                    .width(22.dp)
                    .height(92.dp)
                    .background(Color(0xCC111820), RoundedCornerShape(topStart = 14.dp, bottomStart = 14.dp))
                    .clickable { setOpen(true) }
                    .pointerInput(Unit) {
                        var drag = 0f
                        detectHorizontalDragGestures(
                            onHorizontalDrag = { _, amount -> drag += amount },
                            onDragEnd = { if (drag < -18f) setOpen(true); drag = 0f }
                        )
                    },
                contentAlignment = Alignment.Center,
            ) {
                Text("‹", color = Color.White, fontSize = 24.sp, fontWeight = FontWeight.Bold)
            }
        }
        return
    }

    Box(Modifier.fillMaxSize()) {
        Box(
            Modifier.fillMaxSize().background(Color(0x55000000)).clickable { setOpen(false) }
        )
        Surface(
            modifier = Modifier.align(Alignment.CenterEnd).width(318.dp).fillMaxHeight(),
            color = Color(0xF2182029),
            tonalElevation = 4.dp,
        ) {
            Column(Modifier.fillMaxSize().padding(horizontal = 18.dp, vertical = 22.dp)) {
                Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f)) {
                        Text("Wudroid Frame Generation", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 18.sp)
                        Text("Nativo no Vulkan X • 2×", color = Color(0xFF9EADB9), fontSize = 12.sp)
                    }
                    Switch(checked = config.enabled, onCheckedChange = { save(config.copy(enabled = it)) })
                }

                Spacer(Modifier.height(16.dp))
                val statusText = when (status) {
                    0 -> if (config.enabled) "Aguardando renderer Vulkan" else "Desativado"
                    1 -> "Aquecendo histórico: 1º frame real"
                    2 -> "Ativo: quadro intermediário nativo"
                    3 -> "Driver/swapchain sem TRANSFER_SRC"
                    4 -> "Backend parou por segurança"
                    else -> "Estado $status"
                }
                Text(statusText, color = if (status == 2) Color(0xFF63E6BE) else Color(0xFFB9C5CE), fontSize = 13.sp)
                if (status == 4 && error.isNotBlank()) {
                    Text(error, color = Color(0xFFFFB4AB), fontSize = 11.sp)
                }
                Text(
                    if (nvFlow) "VK_NV_optical_flow detectado; reservado para backend futuro." else "Backend atual: Wudroid Motion Compute v0.1.",
                    color = Color(0xFF7F91A0), fontSize = 11.sp,
                )

                Spacer(Modifier.height(18.dp))
                Text("Qualidade", color = Color.White, fontWeight = FontWeight.SemiBold)
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(7.dp)) {
                    listOf("Desempenho", "Balanceado", "Qualidade").forEachIndexed { index, label ->
                        Button(
                            onClick = { save(config.copy(quality = index)) },
                            modifier = Modifier.weight(1f),
                            colors = ButtonDefaults.buttonColors(
                                containerColor = if (config.quality == index) Color(0xFF0077A8) else Color(0xFF2A333D)
                            ),
                            contentPadding = ButtonDefaults.ContentPadding,
                        ) { Text(label, fontSize = 10.sp, maxLines = 1) }
                    }
                }
                Text(
                    when (config.quality) {
                        0 -> "Busca de movimento ±1 px: menor custo."
                        2 -> "Busca de movimento ±4 px: melhor movimento, mais GPU."
                        else -> "Busca de movimento ±2 px: equilíbrio."
                    },
                    color = Color(0xFF8796A3), fontSize = 11.sp,
                )

                Spacer(Modifier.height(16.dp))
                Text("Força do vetor ${(config.strength * 100).toInt()}%", color = Color.White, fontWeight = FontWeight.SemiBold)
                Slider(
                    value = config.strength,
                    onValueChange = { config = config.copy(strength = it) },
                    onValueChangeFinished = { WudroidNativeFrameGen.saveAndApply(activity, config) },
                    valueRange = 0.5f..1.0f,
                )

                Spacer(Modifier.height(16.dp))
                Surface(color = Color(0xFF11171E), shape = RoundedCornerShape(12.dp)) {
                    Column(Modifier.fillMaxWidth().padding(12.dp)) {
                        Text("FPS em tempo real", color = Color.White, fontWeight = FontWeight.SemiBold)
                        Spacer(Modifier.height(6.dp))
                        Text("Reais: ${fps.getOrElse(0) { 0 }}", color = Color(0xFFB9C5CE))
                        Text("Gerados: ${fps.getOrElse(1) { 0 }}", color = Color(0xFFB9C5CE))
                        Text("Saída: ${fps.getOrElse(2) { 0 }}", color = Color(0xFF63E6BE), fontWeight = FontWeight.Bold)
                    }
                }

                Spacer(Modifier.weight(1f))
                Text(
                    "Sem Lossless.dll, MediaProjection, root ou overlay de outro aplicativo. O quadro é sintetizado antes do vkQueuePresentKHR do Cemu.",
                    color = Color(0xFF71808C), fontSize = 10.sp,
                )
                Spacer(Modifier.height(10.dp))
                Button(onClick = { setOpen(false) }, modifier = Modifier.fillMaxWidth()) { Text("Voltar ao jogo") }
            }
        }
    }
}
