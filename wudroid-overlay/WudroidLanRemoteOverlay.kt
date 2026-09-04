package info.cemu.cemu

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
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
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

private val LanPadCyan = Color(0xFF00B8F5)
private val LanPadLight = Color(0xBFE7EDF2)
private val LanPadDark = Color(0xA91B2026)
private val LanPadInk = Color(0xFF1A1D21)
private val LanPadWhite = Color(0xFFF7FAFC)
private const val LAN_OVERLAY_PREFS = "wudroid_lan_player2_overlay"

@Composable
fun WudroidLanRemoteControllerOverlay(
    controllerKind: String,
    editing: Boolean,
) {
    val context = LocalContext.current
    val prefs = remember {
        context.getSharedPreferences(LAN_OVERLAY_PREFS, Context.MODE_PRIVATE)
    }

    Box(Modifier.fillMaxSize()) {
        if (controllerKind == "WIIMOTE") {
            WiiRemoteDolphinLayout(prefs, editing)
        } else {
            GamePadRemoteLayout(prefs, editing)
        }
    }
}

@Composable
private fun BoxScope.WiiRemoteDolphinLayout(
    prefs: SharedPreferences,
    editing: Boolean,
) {
    LanEditableSlot(prefs, "wii_nunchuk", Alignment.BottomStart, editing) {
        WiiNunchukStick(editing)
    }

    LanEditableSlot(prefs, "wii_face", Alignment.CenterEnd, editing) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            LanRemoteButton("Z", WudroidWiimoteMapping.NUNCHUK_Z, editing, Modifier.size(58.dp), true, true)
            LanRemoteButton("B", WudroidWiimoteMapping.B, editing, Modifier.size(width = 64.dp, height = 46.dp), false, true)
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                LanRemoteButton("C", WudroidWiimoteMapping.NUNCHUK_C, editing, Modifier.size(58.dp), true, true)
                LanRemoteButton("A", WudroidWiimoteMapping.A, editing, Modifier.size(66.dp), true, true)
            }
        }
    }

    LanEditableSlot(prefs, "wii_dpad", Alignment.Center, editing) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            LanRemoteButton("↑", NativeInput.WiimoteButton.UP, editing, Modifier.size(42.dp), false, true)
            Row(horizontalArrangement = Arrangement.spacedBy(3.dp)) {
                LanRemoteButton("←", NativeInput.WiimoteButton.LEFT, editing, Modifier.size(42.dp), false, true)
                Spacer(Modifier.size(42.dp))
                LanRemoteButton("→", NativeInput.WiimoteButton.RIGHT, editing, Modifier.size(42.dp), false, true)
            }
            LanRemoteButton("↓", NativeInput.WiimoteButton.DOWN, editing, Modifier.size(42.dp), false, true)
        }
    }

    LanEditableSlot(prefs, "wii_system", Alignment.BottomCenter, editing) {
        Row(
            horizontalArrangement = Arrangement.spacedBy(10.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                LanRemoteButton("−", WudroidWiimoteMapping.MINUS, editing, Modifier.size(42.dp), true, true)
                LanRemoteButton("+", WudroidWiimoteMapping.PLUS, editing, Modifier.size(42.dp), true, true)
            }
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                LanRemoteButton("1", WudroidWiimoteMapping.ONE, editing, Modifier.size(48.dp), true, true)
                LanRemoteButton("2", WudroidWiimoteMapping.TWO, editing, Modifier.size(48.dp), true, true)
            }
            LanRemoteButton("HOME", WudroidWiimoteMapping.HOME, editing, Modifier.size(width = 68.dp, height = 38.dp), false, true)
        }
    }
}

@Composable
private fun BoxScope.GamePadRemoteLayout(
    prefs: SharedPreferences,
    editing: Boolean,
) {
    var leftX by remember { mutableFloatStateOf(0f) }
    var leftY by remember { mutableFloatStateOf(0f) }
    var rightX by remember { mutableFloatStateOf(0f) }
    var rightY by remember { mutableFloatStateOf(0f) }

    fun sendSticks() {
        WudroidLanMultiplayer.sendRemoteSticks(leftX, leftY, rightX, rightY)
    }

    DisposableEffect(Unit) {
        onDispose { WudroidLanMultiplayer.sendRemoteSticks(0f, 0f, 0f, 0f) }
    }

    LanEditableSlot(prefs, "gp_dpad", Alignment.BottomStart, editing) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            LanRemoteButton("↑", NativeInput.ProButton.UP, editing, Modifier.size(48.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(3.dp)) {
                LanRemoteButton("←", NativeInput.ProButton.LEFT, editing, Modifier.size(48.dp))
                Spacer(Modifier.size(48.dp))
                LanRemoteButton("→", NativeInput.ProButton.RIGHT, editing, Modifier.size(48.dp))
            }
            LanRemoteButton("↓", NativeInput.ProButton.DOWN, editing, Modifier.size(48.dp))
        }
    }

    LanEditableSlot(prefs, "gp_abxy", Alignment.BottomEnd, editing) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            LanRemoteButton("X", NativeInput.ProButton.X, editing, Modifier.size(54.dp), true)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                LanRemoteButton("Y", NativeInput.ProButton.Y, editing, Modifier.size(54.dp), true)
                Spacer(Modifier.size(54.dp))
                LanRemoteButton("A", NativeInput.ProButton.A, editing, Modifier.size(54.dp), true)
            }
            LanRemoteButton("B", NativeInput.ProButton.B, editing, Modifier.size(54.dp), true)
        }
    }

    LanEditableSlot(prefs, "gp_left_stick", Alignment.CenterStart, editing) {
        LanVirtualStick(
            editing = editing,
            label = "L",
            onChanged = { x, y -> leftX = x; leftY = y; sendSticks() },
        )
    }

    LanEditableSlot(prefs, "gp_right_stick", Alignment.CenterEnd, editing) {
        LanVirtualStick(
            editing = editing,
            label = "R",
            onChanged = { x, y -> rightX = x; rightY = y; sendSticks() },
        )
    }

    LanEditableSlot(prefs, "gp_shoulders", Alignment.TopCenter, editing) {
        Row(horizontalArrangement = Arrangement.spacedBy(7.dp)) {
            LanRemoteButton("ZL", NativeInput.ProButton.ZL, editing, Modifier.size(width = 58.dp, height = 38.dp))
            LanRemoteButton("L", NativeInput.ProButton.L, editing, Modifier.size(width = 52.dp, height = 38.dp))
            LanRemoteButton("R", NativeInput.ProButton.R, editing, Modifier.size(width = 52.dp, height = 38.dp))
            LanRemoteButton("ZR", NativeInput.ProButton.ZR, editing, Modifier.size(width = 58.dp, height = 38.dp))
        }
    }

    LanEditableSlot(prefs, "gp_system", Alignment.BottomCenter, editing) {
        Row(horizontalArrangement = Arrangement.spacedBy(9.dp)) {
            LanRemoteButton("−", NativeInput.ProButton.MINUS, editing, Modifier.size(42.dp), true)
            LanRemoteButton("+", NativeInput.ProButton.PLUS, editing, Modifier.size(42.dp), true)
        }
    }
}

@Composable
private fun BoxScope.LanEditableSlot(
    prefs: SharedPreferences,
    key: String,
    alignment: Alignment,
    editing: Boolean,
    content: @Composable () -> Unit,
) {
    var offsetX by remember(key) { mutableFloatStateOf(prefs.getFloat("${key}_x", 0f)) }
    var offsetY by remember(key) { mutableFloatStateOf(prefs.getFloat("${key}_y", 0f)) }

    val dragModifier = if (editing) {
        Modifier.pointerInput(key) {
            detectDragGestures(
                onDrag = { _, drag ->
                    offsetX += drag.x
                    offsetY += drag.y
                },
                onDragEnd = {
                    prefs.edit().putFloat("${key}_x", offsetX).putFloat("${key}_y", offsetY).apply()
                },
                onDragCancel = {
                    prefs.edit().putFloat("${key}_x", offsetX).putFloat("${key}_y", offsetY).apply()
                },
            )
        }
    } else Modifier

    val editChrome = if (editing) {
        Modifier
            .border(1.dp, LanPadCyan, RoundedCornerShape(14.dp))
            .background(Color(0x3300B8F5), RoundedCornerShape(14.dp))
            .padding(5.dp)
    } else Modifier

    Box(
        modifier = Modifier
            .align(alignment)
            .padding(18.dp)
            .offset { IntOffset(offsetX.roundToInt(), offsetY.roundToInt()) }
            .then(editChrome)
            .then(dragModifier),
        contentAlignment = Alignment.Center,
    ) {
        content()
    }
}

@Composable
private fun LanRemoteButton(
    label: String,
    mappingId: Int,
    editing: Boolean,
    modifier: Modifier,
    circular: Boolean = false,
    dolphinLight: Boolean = false,
) {
    var pressed by remember(mappingId) { mutableStateOf(false) }

    DisposableEffect(mappingId) {
        onDispose {
            if (pressed) WudroidLanMultiplayer.sendRemoteButton(mappingId, false)
        }
    }

    val input = if (!editing) {
        Modifier.pointerInput(mappingId) {
            detectTapGestures(
                onPress = {
                    pressed = true
                    WudroidLanMultiplayer.sendRemoteButton(mappingId, true)
                    try {
                        tryAwaitRelease()
                    } finally {
                        pressed = false
                        WudroidLanMultiplayer.sendRemoteButton(mappingId, false)
                    }
                }
            )
        }
    } else Modifier

    val bg = when {
        pressed -> LanPadCyan.copy(alpha = .85f)
        dolphinLight -> LanPadLight
        else -> LanPadDark
    }
    val ink = if (dolphinLight && !pressed) LanPadInk else LanPadWhite
    val shape = if (circular) CircleShape else RoundedCornerShape(14.dp)

    Box(
        modifier = modifier
            .background(bg, shape)
            .border(1.dp, if (editing) LanPadCyan else Color.White.copy(alpha = .22f), shape)
            .then(input),
        contentAlignment = Alignment.Center,
    ) {
        Text(label, color = ink, fontWeight = FontWeight.Bold, fontSize = 12.sp)
    }
}

@Composable
private fun LanVirtualStick(
    editing: Boolean,
    label: String,
    onChanged: (Float, Float) -> Unit,
) {
    var x by remember { mutableFloatStateOf(0f) }
    var y by remember { mutableFloatStateOf(0f) }
    val density = LocalDensity.current
    val travel = with(density) { 25.dp.toPx() }

    val input = if (!editing) {
        Modifier.pointerInput(label) {
            fun update(px: Float, py: Float) {
                val cx = size.width / 2f
                val cy = size.height / 2f
                val nx = ((px - cx) / cx).coerceIn(-1f, 1f)
                val ny = ((py - cy) / cy).coerceIn(-1f, 1f)
                x = nx
                y = ny
                onChanged(nx, ny)
            }
            fun release() {
                x = 0f
                y = 0f
                onChanged(0f, 0f)
            }
            detectDragGestures(
                onDragStart = { p -> update(p.x, p.y) },
                onDrag = { change, _ -> update(change.position.x, change.position.y) },
                onDragEnd = ::release,
                onDragCancel = ::release,
            )
        }
    } else Modifier

    Box(
        modifier = Modifier
            .size(108.dp)
            .background(Color(0x661B2026), CircleShape)
            .border(2.dp, Color.White.copy(alpha = .45f), CircleShape)
            .then(input),
        contentAlignment = Alignment.Center,
    ) {
        Box(
            modifier = Modifier
                .offset { IntOffset((x * travel).roundToInt(), (y * travel).roundToInt()) }
                .size(50.dp)
                .background(LanPadLight, CircleShape)
                .border(1.dp, Color.White.copy(alpha = .65f), CircleShape),
            contentAlignment = Alignment.Center,
        ) {
            Text(label, color = LanPadInk, fontWeight = FontWeight.Black)
        }
    }
}

@Composable
private fun WiiNunchukStick(editing: Boolean) {
    var x by remember { mutableFloatStateOf(0f) }
    var y by remember { mutableFloatStateOf(0f) }
    val density = LocalDensity.current
    val travel = with(density) { 30.dp.toPx() }

    fun emitAxes(nx: Float, ny: Float) {
        WudroidLanMultiplayer.sendRemoteAxis(
            NativeInput.WiimoteButton.NUNCHUCK_LEFT,
            (-nx).coerceAtLeast(0f),
        )
        WudroidLanMultiplayer.sendRemoteAxis(
            NativeInput.WiimoteButton.NUNCHUCK_RIGHT,
            nx.coerceAtLeast(0f),
        )
        WudroidLanMultiplayer.sendRemoteAxis(
            NativeInput.WiimoteButton.NUNCHUCK_UP,
            (-ny).coerceAtLeast(0f),
        )
        WudroidLanMultiplayer.sendRemoteAxis(
            NativeInput.WiimoteButton.NUNCHUCK_DOWN,
            ny.coerceAtLeast(0f),
        )
    }

    fun releaseAll() {
        x = 0f
        y = 0f
        emitAxes(0f, 0f)
    }

    DisposableEffect(Unit) { onDispose { releaseAll() } }

    val input = if (!editing) {
        Modifier.pointerInput(Unit) {
            fun update(px: Float, py: Float) {
                val cx = size.width / 2f
                val cy = size.height / 2f
                x = ((px - cx) / cx).coerceIn(-1f, 1f)
                y = ((py - cy) / cy).coerceIn(-1f, 1f)
                emitAxes(x, y)
            }
            detectDragGestures(
                onDragStart = { p -> update(p.x, p.y) },
                onDrag = { change, _ -> update(change.position.x, change.position.y) },
                onDragEnd = ::releaseAll,
                onDragCancel = ::releaseAll,
            )
        }
    } else Modifier

    Box(
        modifier = Modifier
            .size(132.dp)
            .background(Color(0x5515191E), CircleShape)
            .border(2.dp, Color.White.copy(alpha = .5f), CircleShape)
            .then(input),
        contentAlignment = Alignment.Center,
    ) {
        Box(
            modifier = Modifier
                .offset { IntOffset((x * travel).roundToInt(), (y * travel).roundToInt()) }
                .size(58.dp)
                .background(LanPadLight, CircleShape)
                .border(1.dp, Color.White.copy(alpha = .75f), CircleShape),
        )
    }
}
