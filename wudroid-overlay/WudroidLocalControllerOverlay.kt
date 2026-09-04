package info.cemu.cemu.emulation

import android.content.Context
import android.content.SharedPreferences
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxScope
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import info.cemu.cemu.nativeinterface.NativeInput
import kotlin.math.roundToInt

// WUDROID_LAYOUT14_RUNTIMEFIX1
// This is the real VPAD/WIIMOTE overlay used by Local Multiplayer Test19.
// Layout14 must live here; InputOverlaySurfaceView is bypassed for these types.

private val LocalPadCyan = Color(0xFF00B8F5)
private val LocalPadLight = Color(0xBFD8D8D8)
private val LocalPadDark = Color(0xA91B2026)
private val LocalPadInk = Color(0xFF1A1D21)
private val LocalPadWhite = Color(0xFFF7FAFC)
private const val LOCAL_OVERLAY_PREFS = "wudroid_local_controller_overlay_v3_layout14"

@Composable
fun WudroidLocalControllerOverlay(
    isVisible: Boolean,
    controllerType: Int,
    controllerIndex: Int,
    editing: Boolean,
    editorSizePercent: Float = 100f,
    separated: Boolean = false,
    resetToken: Int = 0,
    overlayAlpha: Float = 1f,
    onSelectionChanged: (Boolean) -> Unit = {},
) {
    if (!isVisible) return

    val context = LocalContext.current
    val prefs = remember {
        context.getSharedPreferences(LOCAL_OVERLAY_PREFS, Context.MODE_PRIVATE)
    }

    var selectedKey by remember(controllerType, controllerIndex) { mutableStateOf<String?>(null) }
    var selectedBaseScale by remember(controllerType, controllerIndex) { mutableFloatStateOf(1f) }
    var layoutEpoch by remember(controllerType, controllerIndex) { mutableStateOf(0) }

    fun select(key: String, currentScale: Float) {
        if (!editing) return
        selectedKey = key
        selectedBaseScale = currentScale.coerceIn(0.25f, 2f)
        onSelectionChanged(true)
    }

    LaunchedEffect(editing) {
        if (!editing) {
            selectedKey = null
            onSelectionChanged(false)
        }
    }

    LaunchedEffect(resetToken, controllerType) {
        if (resetToken > 0) {
            val prefix = if (controllerType == NativeInput.EmulatedControllerType.WIIMOTE) "wii_" else "gp_"
            val editor = prefs.edit()
            prefs.all.keys.filter { it.startsWith(prefix) }.forEach { editor.remove(it) }
            editor.apply()
            selectedKey = null
            layoutEpoch += 1
            onSelectionChanged(false)
        }
    }

    Box(
        Modifier
            .fillMaxSize()
            .graphicsLayer(alpha = overlayAlpha.coerceIn(0f, 1f)),
    ) {
        if (controllerType == NativeInput.EmulatedControllerType.WIIMOTE) {
            LocalWiiRemoteLayout(
                prefs = prefs,
                controllerIndex = controllerIndex,
                editing = editing,
                separated = separated,
                selectedKey = selectedKey,
                selectedBaseScale = selectedBaseScale,
                editorSizePercent = editorSizePercent,
                resetToken = layoutEpoch,
                onSelect = ::select,
            )
        } else {
            LocalGamePadLayout(
                prefs = prefs,
                controllerIndex = controllerIndex,
                editing = editing,
                selectedKey = selectedKey,
                selectedBaseScale = selectedBaseScale,
                editorSizePercent = editorSizePercent,
                resetToken = layoutEpoch,
                onSelect = ::select,
            )
        }
    }
}

@Composable
private fun BoxScope.LocalWiiRemoteLayout(
    prefs: SharedPreferences,
    controllerIndex: Int,
    editing: Boolean,
    separated: Boolean,
    selectedKey: String?,
    selectedBaseScale: Float,
    editorSizePercent: Float,
    resetToken: Int,
    onSelect: (String, Float) -> Unit,
) {
    // Exact requested base: D-pad left, + / - bottom-center, B/1/A/2 diamond right.
    // Nunchuk stick/C/Z/HOME are intentionally not part of this layout.
    if (separated) {
        LocalStaticTransform(
            prefs = prefs,
            key = "wii_dpad_group",
            alignment = Alignment.BottomStart,
            padding = 30.dp,
            baseY = (-62).dp,
            resetToken = resetToken,
            modifier = Modifier.size(188.dp),
        ) {
            LocalEditableItem(
                prefs, "wii_dpad_up", Alignment.TopCenter, editing,
                selectedKey, selectedBaseScale, editorSizePercent, resetToken, onSelect,
            ) { LocalButton("▲", NativeInput.WiimoteButton.UP, controllerIndex, editing, Modifier.size(62.dp), light = true) }
            LocalEditableItem(
                prefs, "wii_dpad_left", Alignment.CenterStart, editing,
                selectedKey, selectedBaseScale, editorSizePercent, resetToken, onSelect,
            ) { LocalButton("◀", NativeInput.WiimoteButton.LEFT, controllerIndex, editing, Modifier.size(62.dp), light = true) }
            LocalEditableItem(
                prefs, "wii_dpad_right", Alignment.CenterEnd, editing,
                selectedKey, selectedBaseScale, editorSizePercent, resetToken, onSelect,
            ) { LocalButton("▶", NativeInput.WiimoteButton.RIGHT, controllerIndex, editing, Modifier.size(62.dp), light = true) }
            LocalEditableItem(
                prefs, "wii_dpad_down", Alignment.BottomCenter, editing,
                selectedKey, selectedBaseScale, editorSizePercent, resetToken, onSelect,
            ) { LocalButton("▼", NativeInput.WiimoteButton.DOWN, controllerIndex, editing, Modifier.size(62.dp), light = true) }
        }
    } else {
        LocalEditableItem(
            prefs = prefs,
            key = "wii_dpad_group",
            alignment = Alignment.BottomStart,
            editing = editing,
            selectedKey = selectedKey,
            selectedBaseScale = selectedBaseScale,
            editorSizePercent = editorSizePercent,
            resetToken = resetToken,
            onSelect = onSelect,
            padding = 30.dp,
            baseY = (-62).dp,
        ) {
            WiiDpadCluster(controllerIndex, editing)
        }
    }

    if (separated) {
        LocalStaticTransform(
            prefs = prefs,
            key = "wii_face_group",
            alignment = Alignment.BottomEnd,
            padding = 30.dp,
            baseY = (-44).dp,
            resetToken = resetToken,
            modifier = Modifier.size(206.dp),
        ) {
            LocalEditableItem(
                prefs, "wii_face_b", Alignment.TopCenter, editing,
                selectedKey, selectedBaseScale, editorSizePercent, resetToken, onSelect,
            ) { LocalButton("B", NativeInput.WiimoteButton.B, controllerIndex, editing, Modifier.size(66.dp), circular = true, light = true) }
            LocalEditableItem(
                prefs, "wii_face_1", Alignment.CenterStart, editing,
                selectedKey, selectedBaseScale, editorSizePercent, resetToken, onSelect,
            ) { LocalButton("1", NativeInput.WiimoteButton.ONE, controllerIndex, editing, Modifier.size(66.dp), circular = true, light = true) }
            LocalEditableItem(
                prefs, "wii_face_a", Alignment.CenterEnd, editing,
                selectedKey, selectedBaseScale, editorSizePercent, resetToken, onSelect,
            ) { LocalButton("A", NativeInput.WiimoteButton.A, controllerIndex, editing, Modifier.size(66.dp), circular = true, light = true) }
            LocalEditableItem(
                prefs, "wii_face_2", Alignment.BottomCenter, editing,
                selectedKey, selectedBaseScale, editorSizePercent, resetToken, onSelect,
            ) { LocalButton("2", NativeInput.WiimoteButton.TWO, controllerIndex, editing, Modifier.size(66.dp), circular = true, light = true) }
        }
    } else {
        LocalEditableItem(
            prefs = prefs,
            key = "wii_face_group",
            alignment = Alignment.BottomEnd,
            editing = editing,
            selectedKey = selectedKey,
            selectedBaseScale = selectedBaseScale,
            editorSizePercent = editorSizePercent,
            resetToken = resetToken,
            onSelect = onSelect,
            padding = 30.dp,
            baseY = (-44).dp,
        ) {
            WiiFaceCluster(controllerIndex, editing)
        }
    }

    LocalEditableItem(
        prefs = prefs,
        key = "wii_plus",
        alignment = Alignment.BottomCenter,
        editing = editing,
        selectedKey = selectedKey,
        selectedBaseScale = selectedBaseScale,
        editorSizePercent = editorSizePercent,
        resetToken = resetToken,
        onSelect = onSelect,
        padding = 18.dp,
        baseX = (-46).dp,
    ) {
        LocalButton("+", NativeInput.WiimoteButton.PLUS, controllerIndex, editing, Modifier.size(48.dp), circular = true, light = true)
    }
    LocalEditableItem(
        prefs = prefs,
        key = "wii_minus",
        alignment = Alignment.BottomCenter,
        editing = editing,
        selectedKey = selectedKey,
        selectedBaseScale = selectedBaseScale,
        editorSizePercent = editorSizePercent,
        resetToken = resetToken,
        onSelect = onSelect,
        padding = 18.dp,
        baseX = 46.dp,
    ) {
        LocalButton("−", NativeInput.WiimoteButton.MINUS, controllerIndex, editing, Modifier.size(48.dp), circular = true, light = true)
    }
}

@Composable
private fun WiiDpadCluster(controllerIndex: Int, editing: Boolean) {
    Box(Modifier.size(188.dp)) {
        Box(Modifier.align(Alignment.TopCenter)) {
            LocalButton("▲", NativeInput.WiimoteButton.UP, controllerIndex, editing, Modifier.size(62.dp), light = true)
        }
        Box(Modifier.align(Alignment.CenterStart)) {
            LocalButton("◀", NativeInput.WiimoteButton.LEFT, controllerIndex, editing, Modifier.size(62.dp), light = true)
        }
        Box(Modifier.align(Alignment.CenterEnd)) {
            LocalButton("▶", NativeInput.WiimoteButton.RIGHT, controllerIndex, editing, Modifier.size(62.dp), light = true)
        }
        Box(Modifier.align(Alignment.BottomCenter)) {
            LocalButton("▼", NativeInput.WiimoteButton.DOWN, controllerIndex, editing, Modifier.size(62.dp), light = true)
        }
    }
}

@Composable
private fun WiiFaceCluster(controllerIndex: Int, editing: Boolean) {
    Box(Modifier.size(206.dp)) {
        Box(Modifier.align(Alignment.TopCenter)) {
            LocalButton("B", NativeInput.WiimoteButton.B, controllerIndex, editing, Modifier.size(66.dp), circular = true, light = true)
        }
        Box(Modifier.align(Alignment.CenterStart)) {
            LocalButton("1", NativeInput.WiimoteButton.ONE, controllerIndex, editing, Modifier.size(66.dp), circular = true, light = true)
        }
        Box(Modifier.align(Alignment.CenterEnd)) {
            LocalButton("A", NativeInput.WiimoteButton.A, controllerIndex, editing, Modifier.size(66.dp), circular = true, light = true)
        }
        Box(Modifier.align(Alignment.BottomCenter)) {
            LocalButton("2", NativeInput.WiimoteButton.TWO, controllerIndex, editing, Modifier.size(66.dp), circular = true, light = true)
        }
    }
}

@Composable
private fun BoxScope.LocalGamePadLayout(
    prefs: SharedPreferences,
    controllerIndex: Int,
    editing: Boolean,
    selectedKey: String?,
    selectedBaseScale: Float,
    editorSizePercent: Float,
    resetToken: Int,
    onSelect: (String, Float) -> Unit,
) {
    // D-pad stays one selectable control, matching the original Cemu overlay semantics.
    LocalEditableItem(
        prefs, "gp_dpad", Alignment.BottomStart, editing,
        selectedKey, selectedBaseScale, editorSizePercent, resetToken, onSelect,
        padding = 22.dp,
    ) {
        GamePadDpad(controllerIndex, editing)
    }

    // ABXY are independently selectable/resizable.
    LocalEditableItem(
        prefs, "gp_x", Alignment.BottomEnd, editing,
        selectedKey, selectedBaseScale, editorSizePercent, resetToken, onSelect,
        padding = 22.dp, baseX = (-66).dp, baseY = (-114).dp,
    ) { LocalButton("X", NativeInput.VPADButton.X, controllerIndex, editing, Modifier.size(56.dp), circular = true) }
    LocalEditableItem(
        prefs, "gp_y", Alignment.BottomEnd, editing,
        selectedKey, selectedBaseScale, editorSizePercent, resetToken, onSelect,
        padding = 22.dp, baseX = (-122).dp, baseY = (-58).dp,
    ) { LocalButton("Y", NativeInput.VPADButton.Y, controllerIndex, editing, Modifier.size(56.dp), circular = true) }
    LocalEditableItem(
        prefs, "gp_a", Alignment.BottomEnd, editing,
        selectedKey, selectedBaseScale, editorSizePercent, resetToken, onSelect,
        padding = 22.dp, baseX = (-10).dp, baseY = (-58).dp,
    ) { LocalButton("A", NativeInput.VPADButton.A, controllerIndex, editing, Modifier.size(56.dp), circular = true) }
    LocalEditableItem(
        prefs, "gp_b", Alignment.BottomEnd, editing,
        selectedKey, selectedBaseScale, editorSizePercent, resetToken, onSelect,
        padding = 22.dp, baseX = (-66).dp, baseY = (-2).dp,
    ) { LocalButton("B", NativeInput.VPADButton.B, controllerIndex, editing, Modifier.size(56.dp), circular = true) }

    LocalEditableItem(
        prefs, "gp_left_stick", Alignment.CenterStart, editing,
        selectedKey, selectedBaseScale, editorSizePercent, resetToken, onSelect,
        padding = 20.dp,
    ) {
        LocalStick(editing, "L") { x, y -> sendVpadStick(controllerIndex, true, x, y) }
    }
    LocalEditableItem(
        prefs, "gp_right_stick", Alignment.CenterEnd, editing,
        selectedKey, selectedBaseScale, editorSizePercent, resetToken, onSelect,
        padding = 20.dp,
    ) {
        LocalStick(editing, "R") { x, y -> sendVpadStick(controllerIndex, false, x, y) }
    }

    LocalEditableItem(
        prefs, "gp_zl", Alignment.TopCenter, editing,
        selectedKey, selectedBaseScale, editorSizePercent, resetToken, onSelect,
        padding = 16.dp, baseX = (-102).dp,
    ) { LocalButton("ZL", NativeInput.VPADButton.ZL, controllerIndex, editing, Modifier.size(width = 58.dp, height = 38.dp)) }
    LocalEditableItem(
        prefs, "gp_l", Alignment.TopCenter, editing,
        selectedKey, selectedBaseScale, editorSizePercent, resetToken, onSelect,
        padding = 16.dp, baseX = (-34).dp,
    ) { LocalButton("L", NativeInput.VPADButton.L, controllerIndex, editing, Modifier.size(width = 52.dp, height = 38.dp)) }
    LocalEditableItem(
        prefs, "gp_r", Alignment.TopCenter, editing,
        selectedKey, selectedBaseScale, editorSizePercent, resetToken, onSelect,
        padding = 16.dp, baseX = 34.dp,
    ) { LocalButton("R", NativeInput.VPADButton.R, controllerIndex, editing, Modifier.size(width = 52.dp, height = 38.dp)) }
    LocalEditableItem(
        prefs, "gp_zr", Alignment.TopCenter, editing,
        selectedKey, selectedBaseScale, editorSizePercent, resetToken, onSelect,
        padding = 16.dp, baseX = 102.dp,
    ) { LocalButton("ZR", NativeInput.VPADButton.ZR, controllerIndex, editing, Modifier.size(width = 58.dp, height = 38.dp)) }

    LocalEditableItem(
        prefs, "gp_minus", Alignment.BottomCenter, editing,
        selectedKey, selectedBaseScale, editorSizePercent, resetToken, onSelect,
        padding = 16.dp, baseX = (-30).dp,
    ) { LocalButton("−", NativeInput.VPADButton.MINUS, controllerIndex, editing, Modifier.size(42.dp), circular = true) }
    LocalEditableItem(
        prefs, "gp_plus", Alignment.BottomCenter, editing,
        selectedKey, selectedBaseScale, editorSizePercent, resetToken, onSelect,
        padding = 16.dp, baseX = 30.dp,
    ) { LocalButton("+", NativeInput.VPADButton.PLUS, controllerIndex, editing, Modifier.size(42.dp), circular = true) }
}

@Composable
private fun GamePadDpad(controllerIndex: Int, editing: Boolean) {
    Box(Modifier.size(150.dp)) {
        Box(Modifier.align(Alignment.TopCenter)) {
            LocalButton("↑", NativeInput.VPADButton.UP, controllerIndex, editing, Modifier.size(50.dp))
        }
        Box(Modifier.align(Alignment.CenterStart)) {
            LocalButton("←", NativeInput.VPADButton.LEFT, controllerIndex, editing, Modifier.size(50.dp))
        }
        Box(Modifier.align(Alignment.CenterEnd)) {
            LocalButton("→", NativeInput.VPADButton.RIGHT, controllerIndex, editing, Modifier.size(50.dp))
        }
        Box(Modifier.align(Alignment.BottomCenter)) {
            LocalButton("↓", NativeInput.VPADButton.DOWN, controllerIndex, editing, Modifier.size(50.dp))
        }
    }
}

@Composable
private fun BoxScope.LocalStaticTransform(
    prefs: SharedPreferences,
    key: String,
    alignment: Alignment,
    padding: Dp,
    baseX: Dp = 0.dp,
    baseY: Dp = 0.dp,
    resetToken: Int,
    modifier: Modifier = Modifier,
    content: @Composable BoxScope.() -> Unit,
) {
    val offsetX = prefs.getFloat("${key}_x", 0f)
    val offsetY = prefs.getFloat("${key}_y", 0f)
    val scale = prefs.getFloat("${key}_scale", 1f).coerceIn(0.25f, 2f)

    Box(
        modifier = Modifier
            .align(alignment)
            .padding(padding)
            .offset(x = baseX, y = baseY)
            .offset { IntOffset(offsetX.roundToInt(), offsetY.roundToInt()) }
            .graphicsLayer(scaleX = scale, scaleY = scale)
            .then(modifier),
        contentAlignment = Alignment.Center,
        content = content,
    )
}

@Composable
private fun BoxScope.LocalEditableItem(
    prefs: SharedPreferences,
    key: String,
    alignment: Alignment,
    editing: Boolean,
    selectedKey: String?,
    selectedBaseScale: Float,
    editorSizePercent: Float,
    resetToken: Int,
    onSelect: (String, Float) -> Unit,
    padding: Dp = 0.dp,
    baseX: Dp = 0.dp,
    baseY: Dp = 0.dp,
    content: @Composable () -> Unit,
) {
    var offsetX by remember(key, resetToken) { mutableFloatStateOf(prefs.getFloat("${key}_x", 0f)) }
    var offsetY by remember(key, resetToken) { mutableFloatStateOf(prefs.getFloat("${key}_y", 0f)) }
    var savedScale by remember(key, resetToken) {
        mutableFloatStateOf(prefs.getFloat("${key}_scale", 1f).coerceIn(0.25f, 2f))
    }

    val selected = editing && selectedKey == key
    val displayScale = if (selected) {
        (selectedBaseScale * (editorSizePercent / 100f)).coerceIn(0.25f, 2f)
    } else {
        savedScale
    }

    LaunchedEffect(selected, displayScale) {
        if (selected && savedScale != displayScale) {
            savedScale = displayScale
            prefs.edit().putFloat("${key}_scale", displayScale).apply()
        }
    }

    val selectModifier = if (editing) {
        Modifier.pointerInput(key, resetToken) {
            detectTapGestures(onTap = { onSelect(key, savedScale) })
        }
    } else {
        Modifier
    }

    val dragModifier = if (editing) {
        Modifier.pointerInput(key, resetToken, "drag") {
            detectDragGestures(
                onDragStart = { onSelect(key, savedScale) },
                onDrag = { _, delta ->
                    offsetX += delta.x
                    offsetY += delta.y
                },
                onDragEnd = {
                    prefs.edit()
                        .putFloat("${key}_x", offsetX)
                        .putFloat("${key}_y", offsetY)
                        .apply()
                },
                onDragCancel = {
                    prefs.edit()
                        .putFloat("${key}_x", offsetX)
                        .putFloat("${key}_y", offsetY)
                        .apply()
                },
            )
        }
    } else {
        Modifier
    }

    val selectedBorder = if (selected) {
        Modifier.border(2.dp, LocalPadCyan, RoundedCornerShape(14.dp))
    } else {
        Modifier
    }

    Box(
        modifier = Modifier
            .align(alignment)
            .padding(padding)
            .offset(x = baseX, y = baseY)
            .offset { IntOffset(offsetX.roundToInt(), offsetY.roundToInt()) }
            .graphicsLayer(scaleX = displayScale, scaleY = displayScale)
            .then(selectedBorder)
            .then(selectModifier)
            .then(dragModifier),
        contentAlignment = Alignment.Center,
    ) {
        content()
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

    val input = if (!editing) {
        Modifier.pointerInput(mappingId, controllerIndex) {
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
                },
            )
        }
    } else {
        Modifier
    }

    val bg = when {
        pressed -> LocalPadCyan.copy(alpha = 0.88f)
        light -> LocalPadLight
        else -> LocalPadDark
    }
    val ink = if (light && !pressed) LocalPadWhite else LocalPadWhite

    Box(
        modifier = modifier
            .background(bg, if (circular) CircleShape else RoundedCornerShape(14.dp))
            .border(
                1.dp,
                if (editing) LocalPadCyan.copy(alpha = 0.65f) else Color.White.copy(alpha = 0.20f),
                if (circular) CircleShape else RoundedCornerShape(14.dp),
            )
            .then(input),
        contentAlignment = Alignment.Center,
    ) {
        Text(label, color = ink, fontWeight = FontWeight.Bold, fontSize = 16.sp)
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

    DisposableEffect(Unit) {
        onDispose { onChanged(0f, 0f) }
    }

    val input = if (!editing) {
        Modifier.pointerInput(label) {
            fun update(px: Float, py: Float) {
                val cx = size.width / 2f
                val cy = size.height / 2f
                x = ((px - cx) / cx).coerceIn(-1f, 1f)
                y = ((py - cy) / cy).coerceIn(-1f, 1f)
                onChanged(x, y)
            }
            detectDragGestures(
                onDragStart = { p -> update(p.x, p.y) },
                onDrag = { c, _ -> update(c.position.x, c.position.y) },
                onDragEnd = { x = 0f; y = 0f; onChanged(0f, 0f) },
                onDragCancel = { x = 0f; y = 0f; onChanged(0f, 0f) },
            )
        }
    } else {
        Modifier
    }

    Box(
        modifier = Modifier
            .size(108.dp)
            .background(Color(0x661B2026), CircleShape)
            .border(2.dp, Color.White.copy(alpha = 0.45f), CircleShape)
            .then(input),
        contentAlignment = Alignment.Center,
    ) {
        Box(
            modifier = Modifier
                .offset { IntOffset((x * travel).roundToInt(), (y * travel).roundToInt()) }
                .size(50.dp)
                .background(LocalPadLight, CircleShape)
                .border(1.dp, Color.White.copy(alpha = 0.65f), CircleShape),
            contentAlignment = Alignment.Center,
        ) {
            Text(label, color = LocalPadInk, fontWeight = FontWeight.Black)
        }
    }
}
