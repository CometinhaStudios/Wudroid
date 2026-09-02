package info.cemu.cemu.emulation

import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import info.cemu.cemu.WudroidWiimoteMapping
import info.cemu.cemu.nativeinterface.NativeInput

private val WiiButton = Color(0xFFCCD0D5)
private val WiiPressed = Color(0xFF16B9E8)
private val WiiInk = Color(0xFF25282C)

@Composable
fun WudroidSoloWiimoteOverlay(
    isVisible: Boolean,
    controllerIndex: Int = 0,
) {
    if (!isVisible) return

    Box(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 12.dp, vertical = 10.dp),
        contentAlignment = Alignment.BottomCenter,
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 14.dp, vertical = 10.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            WiiDpad(controllerIndex)

            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                WiiButton("A", WudroidWiimoteMapping.A, controllerIndex, Modifier.size(58.dp), true)
                Spacer(Modifier.size(5.dp))
                WiiButton("B", WudroidWiimoteMapping.B, controllerIndex, Modifier.size(width = 64.dp, height = 34.dp))
            }

            Row(horizontalArrangement = Arrangement.spacedBy(6.dp), verticalAlignment = Alignment.CenterVertically) {
                WiiButton("−", WudroidWiimoteMapping.MINUS, controllerIndex, Modifier.size(38.dp), true)
                WiiButton("HOME", WudroidWiimoteMapping.HOME, controllerIndex, Modifier.size(width = 58.dp, height = 34.dp))
                WiiButton("+", WudroidWiimoteMapping.PLUS, controllerIndex, Modifier.size(38.dp), true)
            }

            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                WiiButton("1", WudroidWiimoteMapping.ONE, controllerIndex, Modifier.size(48.dp), true)
                Spacer(Modifier.size(6.dp))
                WiiButton("2", WudroidWiimoteMapping.TWO, controllerIndex, Modifier.size(48.dp), true)
            }

            Text("Wii", color = WiiInk, fontWeight = FontWeight.Black, fontSize = 18.sp)
        }
    }
}

@Composable
private fun WiiDpad(controllerIndex: Int) {
    // Wii Remote deitado: os eixos físicos do D-pad ficam rotacionados 90°.
    // Mapeamos pela direção VISUAL que o jogador vê na tela.
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        WiiButton("↑", WudroidWiimoteMapping.RIGHT, controllerIndex, Modifier.size(38.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(3.dp)) {
            WiiButton("←", WudroidWiimoteMapping.UP, controllerIndex, Modifier.size(38.dp))
            Spacer(Modifier.size(38.dp))
            WiiButton("→", WudroidWiimoteMapping.DOWN, controllerIndex, Modifier.size(38.dp))
        }
        WiiButton("↓", WudroidWiimoteMapping.LEFT, controllerIndex, Modifier.size(38.dp))
    }
}

@Composable
private fun WiiButton(
    label: String,
    mappingId: Int,
    controllerIndex: Int,
    modifier: Modifier,
    circular: Boolean = false,
) {
    var pressed by remember(mappingId, controllerIndex) { mutableStateOf(false) }
    Box(
        modifier = modifier
            .background(
                if (pressed) WiiPressed else WiiButton,
                if (circular) CircleShape else RoundedCornerShape(8.dp),
            )
            .pointerInput(mappingId, controllerIndex) {
                detectTapGestures(
                    onPress = {
                        pressed = true
                        NativeInput.onOverlayButton(controllerIndex, mappingId, true)
                        try {
                            tryAwaitRelease()
                        } finally {
                            pressed = false
                            NativeInput.onOverlayButton(controllerIndex, mappingId, false)
                        }
                    }
                )
            },
        contentAlignment = Alignment.Center,
    ) {
        Text(label, color = WiiInk, fontWeight = FontWeight.Bold, fontSize = 12.sp)
    }
}
