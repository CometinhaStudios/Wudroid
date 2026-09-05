package info.cemu.cemu.emulation

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
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
import info.cemu.cemu.nativeinterface.NativeInput

private val MotionRemoteBody = Color(0xEAF4F4F4)
private val MotionRemoteButton = Color(0xFFE2E2E2)
private val MotionRemoteInk = Color(0xFF2C2C2C)
private val MotionRemoteBlue = Color(0xFF53B8E8)

// WUDROID_TV_MODE_TEST1
// Portrait Wii Remote layout. Unlike the sideways gameplay overlay, the D-pad
// mapping here is literal: visual UP sends Wiimote UP, LEFT sends LEFT, etc.
@Composable
fun WudroidMotionWiimoteOverlay(
    controllerIndex: Int = 0,
    alpha: Float = 0.96f,
) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF101317)),
        contentAlignment = Alignment.Center,
    ) {
        Column(
            modifier = Modifier
                .width(214.dp)
                .height(620.dp)
                .background(MotionRemoteBody.copy(alpha = alpha.coerceIn(0.55f, 1f)), RoundedCornerShape(38.dp))
                .border(2.dp, Color(0xFFCCCCCC), RoundedCornerShape(38.dp))
                .padding(horizontal = 20.dp, vertical = 26.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Text("Wii", color = Color(0xFF8B8B8B), fontSize = 24.sp, fontWeight = FontWeight.Bold)
            Spacer(Modifier.height(24.dp))
            MotionDpad(controllerIndex)
            Spacer(Modifier.height(22.dp))
            MotionRoundButton("A", NativeInput.WiimoteButton.A, controllerIndex, 68)
            Spacer(Modifier.height(20.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                MotionRoundButton("−", NativeInput.WiimoteButton.MINUS, controllerIndex, 42)
                Spacer(Modifier.width(14.dp))
                MotionRoundButton("HOME", NativeInput.WiimoteButton.HOME, controllerIndex, 46, smallText = true)
                Spacer(Modifier.width(14.dp))
                MotionRoundButton("+", NativeInput.WiimoteButton.PLUS, controllerIndex, 42)
            }
            Spacer(Modifier.height(30.dp))
            MotionRoundButton("1", NativeInput.WiimoteButton.ONE, controllerIndex, 58)
            Spacer(Modifier.height(14.dp))
            MotionRoundButton("2", NativeInput.WiimoteButton.TWO, controllerIndex, 58)
            Spacer(Modifier.height(18.dp))
            MotionRoundButton("B", NativeInput.WiimoteButton.B, controllerIndex, 54)
            Spacer(Modifier.height(12.dp))
            Row {
                repeat(4) {
                    Box(Modifier.padding(5.dp).size(9.dp).background(MotionRemoteBlue, CircleShape))
                }
            }
        }
    }
}

@Composable
private fun MotionDpad(controllerIndex: Int) {
    Box(Modifier.size(152.dp)) {
        MotionRectButton("▲", NativeInput.WiimoteButton.UP, controllerIndex, Modifier.align(Alignment.TopCenter))
        MotionRectButton("◀", NativeInput.WiimoteButton.LEFT, controllerIndex, Modifier.align(Alignment.CenterStart))
        MotionRectButton("▶", NativeInput.WiimoteButton.RIGHT, controllerIndex, Modifier.align(Alignment.CenterEnd))
        MotionRectButton("▼", NativeInput.WiimoteButton.DOWN, controllerIndex, Modifier.align(Alignment.BottomCenter))
    }
}

@Composable
private fun MotionRectButton(
    label: String,
    mappingId: Int,
    controllerIndex: Int,
    modifier: Modifier,
) {
    MotionButtonCore(label, mappingId, controllerIndex, modifier.size(56.dp), RoundedCornerShape(13.dp), false)
}

@Composable
private fun MotionRoundButton(
    label: String,
    mappingId: Int,
    controllerIndex: Int,
    sizeDp: Int,
    smallText: Boolean = false,
) {
    MotionButtonCore(label, mappingId, controllerIndex, Modifier.size(sizeDp.dp), CircleShape, smallText)
}

@Composable
private fun MotionButtonCore(
    label: String,
    mappingId: Int,
    controllerIndex: Int,
    modifier: Modifier,
    shape: androidx.compose.ui.graphics.Shape,
    smallText: Boolean,
) {
    var pressed by remember(mappingId) { mutableStateOf(false) }
    Box(
        modifier = modifier
            .background(if (pressed) Color.White else MotionRemoteButton, shape)
            .border(1.dp, Color(0xFFBDBDBD), shape)
            .pointerInput(mappingId, controllerIndex) {
                awaitPointerEventScope {
                    while (true) {
                        val event = awaitPointerEvent()
                        val down = event.changes.any { it.pressed }
                        if (down != pressed) {
                            pressed = down
                            NativeInput.onOverlayButton(controllerIndex, mappingId, down)
                        }
                        event.changes.forEach { it.consume() }
                    }
                }
            },
        contentAlignment = Alignment.Center,
    ) {
        Text(
            label,
            color = MotionRemoteInk,
            fontSize = if (smallText) 9.sp else 22.sp,
            fontWeight = FontWeight.Bold,
        )
    }
}
