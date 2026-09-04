package info.cemu.cemu.emulation

import android.content.Context
import android.content.SharedPreferences
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxScope
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import info.cemu.cemu.nativeinterface.NativeInput
import kotlin.math.roundToInt

private val LocalPadCyan = Color(0xFF00B8F5)
private val LocalPadLight = Color(0xBFE7EDF2)
private val LocalPadDark = Color(0xA91B2026)
private val LocalPadInk = Color(0xFF1A1D21)
private val LocalPadWhite = Color(0xFFF7FAFC)
private const val LOCAL_OVERLAY_PREFS = "wudroid_local_controller_overlay_v2"

@Composable
fun WudroidLocalControllerOverlay(
    isVisible: Boolean,
    controllerType: Int,
    controllerIndex: Int,
    editing: Boolean,
) {
    if (!isVisible) return
    val context = LocalContext.current
    val prefs = remember {
        context.getSharedPreferences(LOCAL_OVERLAY_PREFS, Context.MODE_PRIVATE)
    }
    Box(Modifier.fillMaxSize()) {
        if (controllerType == NativeInput.EmulatedControllerType.WIIMOTE) {
            LocalWiiRemoteLayout(prefs, controllerIndex, editing)
        } else {
            LocalGamePadLayout(prefs, controllerIndex, editing)
        }
    }
}

@Composable
private fun BoxScope.LocalWiiRemoteLayout(
    prefs: SharedPreferences,
    controllerIndex: Int,
    editing: Boolean,
) {
    LocalEditableSlot(prefs, "wii_nunchuk", Alignment.BottomStart, editing) {
        LocalNunchukStick(controllerIndex, editing)
    }

    LocalEditableSlot(prefs, "wii_face", Alignment.CenterEnd, editing) {
        Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(8.dp)) {
            LocalButton("Z", NativeInput.WiimoteButton.NUNCHUCK_Z, controllerIndex, editing, Modifier.size(58.dp), true, true)
            LocalButton("B", NativeInput.WiimoteButton.B, controllerIndex, editing, Modifier.size(width = 64.dp, height = 46.dp), false, true)
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                LocalButton("C", NativeInput.WiimoteButton.NUNCHUCK_C, controllerIndex, editing, Modifier.size(58.dp), true, true)
                LocalButton("A", NativeInput.WiimoteButton.A, controllerIndex, editing, Modifier.size(66.dp), true, true)
            }
        }
    }

    LocalEditableSlot(prefs, "wii_dpad", Alignment.Center, editing) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            LocalButton("↑", NativeInput.WiimoteButton.UP, controllerIndex, editing, Modifier.size(42.dp), false, true)
            Row(horizontalArrangement = Arrangement.spacedBy(3.dp)) {
                LocalButton("←", NativeInput.WiimoteButton.LEFT, controllerIndex, editing, Modifier.size(42.dp), false, true)
                Spacer(Modifier.size(42.dp))
                LocalButton("→", NativeInput.WiimoteButton.RIGHT, controllerIndex, editing, Modifier.size(42.dp), false, true)
            }
            LocalButton("↓", NativeInput.WiimoteButton.DOWN, controllerIndex, editing, Modifier.size(42.dp), false, true)
        }
    }

    LocalEditableSlot(prefs, "wii_system", Alignment.BottomCenter, editing) {
        Row(horizontalArrangement = Arrangement.spacedBy(10.dp), verticalAlignment = Alignment.CenterVertically) {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                LocalButton("−", NativeInput.WiimoteButton.MINUS, controllerIndex, editing, Modifier.size(42.dp), true, true)
                LocalButton("+", NativeInput.WiimoteButton.PLUS, controllerIndex, editing, Modifier.size(42.dp), true, true)
            }
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                LocalButton("1", NativeInput.WiimoteButton.ONE, controllerIndex, editing, Modifier.size(48.dp), true, true)
                LocalButton("2", NativeInput.WiimoteButton.TWO, controllerIndex, editing, Modifier.size(48.dp), true, true)
            }
            LocalButton("HOME", NativeInput.WiimoteButton.HOME, controllerIndex, editing, Modifier.size(width = 68.dp, height = 38.dp), false, true)
        }
    }
}

@Composable
private fun BoxScope.LocalGamePadLayout(
    prefs: SharedPreferences,
    controllerIndex: Int,
    editing: Boolean,
) {
    LocalEditableSlot(prefs, "gp_dpad", Alignment.BottomStart, editing) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            LocalButton("↑", NativeInput.VPADButton.UP, controllerIndex, editing, Modifier.size(48.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(3.dp)) {
                LocalButton("←", NativeInput.VPADButton.LEFT, controllerIndex, editing, Modifier.size(48.dp))
                Spacer(Modifier.size(48.dp))
                LocalButton("→", NativeInput.VPADButton.RIGHT, controllerIndex, editing, Modifier.size(48.dp))
            }
            LocalButton("↓", NativeInput.VPADButton.DOWN, controllerIndex, editing, Modifier.size(48.dp))
        }
    }

    LocalEditableSlot(prefs, "gp_abxy", Alignment.BottomEnd, editing) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            LocalButton("X", NativeInput.VPADButton.X, controllerIndex, editing, Modifier.size(54.dp), true)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                LocalButton("Y", NativeInput.VPADButton.Y, controllerIndex, editing, Modifier.size(54.dp), true)
                Spacer(Modifier.size(54.dp))
                LocalButton("A", NativeInput.VPADButton.A, controllerIndex, editing, Modifier.size(54.dp), true)
            }
            LocalButton("B", NativeInput.VPADButton.B, controllerIndex, editing, Modifier.size(54.dp), true)
        }
    }

    LocalEditableSlot(prefs, "gp_left_stick", Alignment.CenterStart, editing) {
        LocalStick(editing, "L") { x, y ->
            sendVpadStick(controllerIndex, true, x, y)
        }
    }
    LocalEditableSlot(prefs, "gp_right_stick", Alignment.CenterEnd, editing) {
        LocalStick(editing, "R") { x, y ->
            sendVpadStick(controllerIndex, false, x, y)
        }
    }

    LocalEditableSlot(prefs, "gp_shoulders", Alignment.TopCenter, editing) {
        Row(horizontalArrangement = Arrangement.spacedBy(7.dp)) {
            LocalButton("ZL", NativeInput.VPADButton.ZL, controllerIndex, editing, Modifier.size(width = 58.dp, height = 38.dp))
            LocalButton("L", NativeInput.VPADButton.L, controllerIndex, editing, Modifier.size(width = 52.dp, height = 38.dp))
            LocalButton("R", NativeInput.VPADButton.R, controllerIndex, editing, Modifier.size(width = 52.dp, height = 38.dp))
            LocalButton("ZR", NativeInput.VPADButton.ZR, controllerIndex, editing, Modifier.size(width = 58.dp, height = 38.dp))
        }
    }

    LocalEditableSlot(prefs, "gp_system", Alignment.BottomCenter, editing) {
        Row(horizontalArrangement = Arrangement.spacedBy(9.dp)) {
            LocalButton("−", NativeInput.VPADButton.MINUS, controllerIndex, editing, Modifier.size(42.dp), true)
            LocalButton("+", NativeInput.VPADButton.PLUS, controllerIndex, editing, Modifier.size(42.dp), true)
        }
    }
}

private fun sendVpadStick(controllerIndex: Int, left: Boolean, x: Float, y: Float) {
    val l = (-x).coerceAtLeast(0f)
    val r = x.coerceAtLeast(0f)
    val u = (-y).coerceAtLeast(0f)
    val d = y.coerceAtLeast(0f)
    if (left) {
        NativeInput.onOverlayAxis(controllerIndex, NativeInput.VPADButton.STICKL_LEFT, l)
        NativeInput.onOverlayAxis(controllerIndex, NativeInput.VPADButton.STICKL_RIGHT, r)
        NativeInput.onOverlayAxis(controllerIndex, NativeInput.VPADButton.STICKL_UP, u)
        NativeInput.onOverlayAxis(controllerIndex, NativeInput.VPADButton.STICKL_DOWN, d)
    } else {
        NativeInput.onOverlayAxis(controllerIndex, NativeInput.VPADButton.STICKR_LEFT, l)
        NativeInput.onOverlayAxis(controllerIndex, NativeInput.VPADButton.STICKR_RIGHT, r)
        NativeInput.onOverlayAxis(controllerIndex, NativeInput.VPADButton.STICKR_UP, u)
        NativeInput.onOverlayAxis(controllerIndex, NativeInput.VPADButton.STICKR_DOWN, d)
    }
}

@Composable
private fun BoxScope.LocalEditableSlot(
    prefs: SharedPreferences,
    key: String,
    alignment: Alignment,
    editing: Boolean,
    content: @Composable () -> Unit,
) {
    var offsetX by remember(key) { mutableFloatStateOf(prefs.getFloat("${key}_x", 0f)) }
    var offsetY by remember(key) { mutableFloatStateOf(prefs.getFloat("${key}_y", 0f)) }
    val drag = if (editing) Modifier.pointerInput(key) {
        detectDragGestures(
            onDrag = { _, delta -> offsetX += delta.x; offsetY += delta.y },
            onDragEnd = { prefs.edit().putFloat("${key}_x", offsetX).putFloat("${key}_y", offsetY).apply() },
            onDragCancel = { prefs.edit().putFloat("${key}_x", offsetX).putFloat("${key}_y", offsetY).apply() },
        )
    } else Modifier
    val chrome = if (editing) Modifier
        .border(1.dp, LocalPadCyan, RoundedCornerShape(14.dp))
        .background(Color(0x3300B8F5), RoundedCornerShape(14.dp))
        .padding(5.dp) else Modifier

    Box(
        modifier = Modifier
            .align(alignment)
            .padding(18.dp)
            .offset { IntOffset(offsetX.roundToInt(), offsetY.roundToInt()) }
            .then(chrome)
            .then(drag),
        contentAlignment = Alignment.Center,
    ) { content() }
}

@Composable
private fun LocalButton(
    label: String,
    mappingId: Int,
    controllerIndex: Int,
    editing: Boolean,
    modifier: Modifier,
    circular: Boolean = false,
    light: Boolean = false,
) {
    var pressed by remember(mappingId, controllerIndex) { mutableStateOf(false) }
    DisposableEffect(mappingId, controllerIndex) {
        onDispose {
            if (pressed) NativeInput.onOverlayButton(controllerIndex, mappingId, false)
        }
    }
    val input = if (!editing) Modifier.pointerInput(mappingId, controllerIndex) {
        detectTapGestures(onPress = {
            pressed = true
            NativeInput.onOverlayButton(controllerIndex, mappingId, true)
            try { tryAwaitRelease() } finally {
                pressed = false
                NativeInput.onOverlayButton(controllerIndex, mappingId, false)
            }
        })
    } else Modifier
    val bg = when {
        pressed -> LocalPadCyan.copy(alpha = .85f)
        light -> LocalPadLight
        else -> LocalPadDark
    }
    val ink = if (light && !pressed) LocalPadInk else LocalPadWhite
    Box(
        modifier = modifier
            .background(bg, if (circular) CircleShape else RoundedCornerShape(14.dp))
            .border(1.dp, if (editing) LocalPadCyan else Color.White.copy(alpha=.22f), if (circular) CircleShape else RoundedCornerShape(14.dp))
            .then(input),
        contentAlignment = Alignment.Center,
    ) {
        Text(label, color=ink, fontWeight=FontWeight.Bold, fontSize=12.sp)
    }
}

@Composable
private fun LocalStick(
    editing: Boolean,
    label: String,
    onChanged: (Float, Float) -> Unit,
) {
    var x by remember { mutableFloatStateOf(0f) }
    var y by remember { mutableFloatStateOf(0f) }
    val density = LocalDensity.current
    val travel = with(density) { 25.dp.toPx() }
    DisposableEffect(Unit) { onDispose { onChanged(0f, 0f) } }
    val input = if (!editing) Modifier.pointerInput(label) {
        fun update(px: Float, py: Float) {
            val cx=size.width/2f; val cy=size.height/2f
            x=((px-cx)/cx).coerceIn(-1f,1f); y=((py-cy)/cy).coerceIn(-1f,1f)
            onChanged(x,y)
        }
        detectDragGestures(
            onDragStart={p->update(p.x,p.y)},
            onDrag={c,_->update(c.position.x,c.position.y)},
            onDragEnd={x=0f;y=0f;onChanged(0f,0f)},
            onDragCancel={x=0f;y=0f;onChanged(0f,0f)},
        )
    } else Modifier
    Box(
        modifier=Modifier.size(108.dp).background(Color(0x661B2026),CircleShape).border(2.dp,Color.White.copy(alpha=.45f),CircleShape).then(input),
        contentAlignment=Alignment.Center,
    ) {
        Box(
            modifier=Modifier.offset{IntOffset((x*travel).roundToInt(),(y*travel).roundToInt())}.size(50.dp).background(LocalPadLight,CircleShape).border(1.dp,Color.White.copy(alpha=.65f),CircleShape),
            contentAlignment=Alignment.Center,
        ){Text(label,color=LocalPadInk,fontWeight=FontWeight.Black)}
    }
}

@Composable
private fun LocalNunchukStick(controllerIndex: Int, editing: Boolean) {
    LocalStick(editing, "") { x, y ->
        NativeInput.onOverlayAxis(controllerIndex, NativeInput.WiimoteButton.NUNCHUCK_LEFT, (-x).coerceAtLeast(0f))
        NativeInput.onOverlayAxis(controllerIndex, NativeInput.WiimoteButton.NUNCHUCK_RIGHT, x.coerceAtLeast(0f))
        NativeInput.onOverlayAxis(controllerIndex, NativeInput.WiimoteButton.NUNCHUCK_UP, (-y).coerceAtLeast(0f))
        NativeInput.onOverlayAxis(controllerIndex, NativeInput.WiimoteButton.NUNCHUCK_DOWN, y.coerceAtLeast(0f))
    }
}
