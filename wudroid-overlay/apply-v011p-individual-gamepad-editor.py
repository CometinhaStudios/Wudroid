#!/usr/bin/env python3
from pathlib import Path
import re

screen_path = Path('cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationScreen.kt')
overlay_path = Path('cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/inputoverlay/InputOverlaySurfaceView.kt')

for p in (screen_path, overlay_path):
    if not p.exists():
        raise SystemExit(f'Required source not found: {p}')

screen = screen_path.read_text()
overlay = overlay_path.read_text()
marker = 'WUDROID_GAMEPAD_EDITOR_TEST8_INDIVIDUAL'

if marker in screen:
    print('Wudroid Gamepad Editor Test8 already applied')
    raise SystemExit(0)

if 'WUDROID_GAMEPAD_EDITOR_TEST7' not in screen:
    raise SystemExit('Gamepad Editor Test7/RobustFix2 must be applied before Test8')

# ---------------------------------------------------------------------------
# Helpers: structural Kotlin function replacement. Avoid fragile next-function
# anchors; this intentionally follows the strategy that made RobustFix2 work.
# ---------------------------------------------------------------------------
def find_function_region(text: str, function_name: str):
    match = re.search(r"(?m)^[ \t]*(?:private[ \t]+)?(?:override[ \t]+)?fun[ \t]+" + re.escape(function_name) + r"[ \t]*\(", text)
    if not match:
        return None

    start = match.start()
    line_start = text.rfind("\n", 0, start) + 1
    scan = line_start
    while scan > 0:
        prev_end = scan - 1
        prev_start = text.rfind("\n", 0, prev_end) + 1
        prev_line = text[prev_start:prev_end].strip()
        if prev_line.startswith("@"):
            start = prev_start
            scan = prev_start
            continue
        if prev_line == "":
            scan = prev_start
            continue
        break

    # Find the REAL function-body brace. Kotlin parameters can contain
    # default lambdas such as `onEditAlphaFinished: (Int) -> Unit = {}`.
    # The old Test8 parser mistook that `{}` for the function body and
    # replaced only the signature, leaving the old AndroidView body behind.
    # First walk the complete balanced parameter list, then find the body.
    paren = text.find("(", match.start(), match.end())
    if paren < 0:
        return None

    pdepth = 0
    i = paren
    in_string = False
    in_char = False
    escape = False
    line_comment = False
    block_comment = False
    signature_end = None
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""

        if line_comment:
            if ch == "\n":
                line_comment = False
            i += 1
            continue
        if block_comment:
            if ch == "*" and nxt == "/":
                block_comment = False
                i += 2
            else:
                i += 1
            continue
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            i += 1
            continue
        if in_char:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == "'":
                in_char = False
            i += 1
            continue

        if ch == "/" and nxt == "/":
            line_comment = True
            i += 2
            continue
        if ch == "/" and nxt == "*":
            block_comment = True
            i += 2
            continue
        if ch == '"':
            in_string = True
            i += 1
            continue
        if ch == "'":
            in_char = True
            i += 1
            continue

        if ch == "(":
            pdepth += 1
        elif ch == ")":
            pdepth -= 1
            if pdepth == 0:
                signature_end = i + 1
                break
        i += 1

    if signature_end is None:
        return None

    brace = text.find("{", signature_end)
    if brace < 0:
        return None

    depth = 0
    i = brace
    in_string = False
    in_char = False
    escape = False
    line_comment = False
    block_comment = False
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""

        if line_comment:
            if ch == "\n":
                line_comment = False
            i += 1
            continue
        if block_comment:
            if ch == "*" and nxt == "/":
                block_comment = False
                i += 2
            else:
                i += 1
            continue
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            i += 1
            continue
        if in_char:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == "'":
                in_char = False
            i += 1
            continue

        if ch == "/" and nxt == "/":
            line_comment = True
            i += 2
            continue
        if ch == "/" and nxt == "*":
            block_comment = True
            i += 2
            continue
        if ch == '"':
            in_string = True
            i += 1
            continue
        if ch == "'":
            in_char = True
            i += 1
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                if end < len(text) and text[end] == "\n":
                    end += 1
                return start, end
        i += 1
    return None


def replace_function(text: str, function_name: str, replacement: str):
    region = find_function_region(text, function_name)
    if region is None:
        return text, 0
    start, end = region
    return text[:start] + replacement + text[end:], 1

# ---------------------------------------------------------------------------
# EmulationScreen: animated collapsible editor + selection-aware size slider.
# Transparency remains global; Size now controls only the selected touch input.
# ---------------------------------------------------------------------------
for imp in [
    'import androidx.compose.animation.AnimatedVisibility',
    'import androidx.compose.animation.fadeIn',
    'import androidx.compose.animation.fadeOut',
    'import androidx.compose.animation.slideInVertically',
    'import androidx.compose.animation.slideOutVertically',
    'import androidx.compose.animation.core.tween',
]:
    if imp not in screen:
        screen = screen.replace('package info.cemu.cemu.emulation\n', 'package info.cemu.cemu.emulation\n' + imp + '\n', 1)

state_anchor = '    var wudroidEditorSizePercent by rememberSaveable { mutableFloatStateOf(100f) }\n'
if state_anchor not in screen:
    raise SystemExit('Test8 state anchor missing: wudroidEditorSizePercent')
screen = screen.replace(
    state_anchor,
    state_anchor +
    '    var wudroidEditorHasSelection by rememberSaveable { mutableStateOf(false) } // WUDROID_GAMEPAD_EDITOR_TEST8_INDIVIDUAL\n'
    '    var wudroidEditorPanelCollapsed by rememberSaveable { mutableStateOf(false) }\n',
    1,
)

# Opening the editor always starts expanded with no selected control.
old_open = '''                        onEditInputOverlay = {
                            wudroidEditorAlpha = inputOverlaySettings.alpha.toFloat()
                            wudroidEditorSizePercent = 100f
                            inputOverlayInputMode = EDIT_POSITION
                            closeDrawer()
                        },
'''
new_open = '''                        onEditInputOverlay = {
                            wudroidEditorAlpha = inputOverlaySettings.alpha.toFloat()
                            wudroidEditorSizePercent = 100f
                            wudroidEditorHasSelection = false
                            wudroidEditorPanelCollapsed = false
                            inputOverlayInputMode = EDIT_POSITION
                            closeDrawer()
                        },
'''
if old_open not in screen:
    raise SystemExit('Test8 onEditInputOverlay anchor missing')
screen = screen.replace(old_open, new_open, 1)

# Extend the InputOverlaySurface call with selected-input scaling + callback.
old_surface_call = '''            editorAlpha = if (inputOverlayInputMode == DEFAULT) null else wudroidEditorAlpha.toInt(),
            editorScale = if (inputOverlayInputMode == DEFAULT) 1f else wudroidEditorSizePercent / 100f,
            onEditFinished = { viewModel.saveInputOverlayRectangles(it) },
            onEditAlphaFinished = { viewModel.saveInputOverlayAlpha(it) },
'''
new_surface_call = '''            editorAlpha = if (inputOverlayInputMode == DEFAULT) null else wudroidEditorAlpha.toInt(),
            editorScale = 1f,
            editorSelectedScale = if (inputOverlayInputMode == DEFAULT || !wudroidEditorHasSelection) 1f else wudroidEditorSizePercent / 100f,
            onEditFinished = { viewModel.saveInputOverlayRectangles(it) },
            onEditAlphaFinished = { viewModel.saveInputOverlayAlpha(it) },
            onEditorSelectionChanged = { selected ->
                wudroidEditorHasSelection = selected
                wudroidEditorSizePercent = 100f
            },
'''
if old_surface_call not in screen:
    raise SystemExit('Test8 InputOverlaySurface editor anchors missing')
screen = screen.replace(old_surface_call, new_surface_call, 1)

# Replace the editor invocation.
editor_call_re = re.compile(
    r'''        if \(inputOverlayInputMode != DEFAULT\) \{\n            EditInputsLayout\(\n.*?            \)\n        \}\n''',
    re.S,
)
new_editor_call = '''        if (inputOverlayInputMode != DEFAULT) {
            EditInputsLayout(
                alpha = wudroidEditorAlpha,
                sizePercent = wudroidEditorSizePercent,
                hasSelection = wudroidEditorHasSelection,
                isCollapsed = wudroidEditorPanelCollapsed,
                onAlphaChange = { wudroidEditorAlpha = it },
                onSizeChange = { wudroidEditorSizePercent = it },
                onCollapseChange = { wudroidEditorPanelCollapsed = it },
                onResetClick = {
                    wudroidEditorAlpha = 128f
                    wudroidEditorSizePercent = 100f
                    viewModel.resetInputOverlayLayout()
                },
                onFinishClick = {
                    snackbarHostState.showMessage(scope, "Controles salvos")
                    wudroidEditorHasSelection = false
                    wudroidEditorPanelCollapsed = false
                    inputOverlayInputMode = DEFAULT
                },
            )
        }
'''
screen, call_count = editor_call_re.subn(new_editor_call, screen, count=1)
if call_count != 1:
    raise SystemExit('Test8 EditInputsLayout call region missing')

new_editor_fn = r'''@Composable
private fun EditInputsLayout(
    alpha: Float,
    sizePercent: Float,
    hasSelection: Boolean,
    isCollapsed: Boolean,
    onAlphaChange: (Float) -> Unit,
    onSizeChange: (Float) -> Unit,
    onCollapseChange: (Boolean) -> Unit,
    onResetClick: () -> Unit,
    onFinishClick: () -> Unit,
) {
    // WUDROID_GAMEPAD_EDITOR_TEST8_INDIVIDUAL
    // The panel can be tucked away to expose almost the whole game screen.
    // Size is intentionally per selected input; transparency remains global.
    Box(modifier = Modifier.fillMaxSize()) {
        AnimatedVisibility(
            visible = !isCollapsed,
            modifier = Modifier.align(Alignment.TopCenter),
            enter = slideInVertically(
                animationSpec = tween(durationMillis = 230),
                initialOffsetY = { -it / 2 },
            ) + fadeIn(animationSpec = tween(180)),
            exit = slideOutVertically(
                animationSpec = tween(durationMillis = 230),
                targetOffsetY = { -it },
            ) + fadeOut(animationSpec = tween(150)),
        ) {
            Column(
                modifier = Modifier
                    .padding(horizontal = 18.dp, vertical = 10.dp)
                    .fillMaxWidth(0.92f)
                    .background(WudroidDrawerBackground, RoundedCornerShape(20.dp))
                    .padding(horizontal = 18.dp, vertical = 12.dp),
            ) {
                Text(
                    text = "Editar controles",
                    color = WudroidCyan,
                    fontSize = 20.sp,
                    fontWeight = FontWeight.Bold,
                )

                Row(
                    modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text("Transparência", color = WudroidDrawerText, modifier = Modifier.weight(1f))
                    Text("${((alpha / 255f) * 100f).toInt()}%", color = WudroidCyan, fontWeight = FontWeight.Bold)
                }
                Slider(
                    value = alpha,
                    onValueChange = { onAlphaChange(it.coerceIn(0f, 255f)) },
                    valueRange = 0f..255f,
                    colors = SliderDefaults.colors(
                        thumbColor = WudroidCyan,
                        activeTrackColor = WudroidCyan,
                        inactiveTrackColor = WudroidDrawerOutline,
                    ),
                )

                Row(
                    modifier = Modifier.fillMaxWidth().padding(top = 0.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text("Tamanho", color = WudroidDrawerText, modifier = Modifier.weight(1f))
                    Text(
                        if (hasSelection) "${sizePercent.toInt()}%" else "Selecione um botão",
                        color = if (hasSelection) WudroidCyan else WudroidDrawerMuted,
                        fontWeight = FontWeight.Bold,
                    )
                }
                Slider(
                    value = sizePercent,
                    onValueChange = { onSizeChange(it.coerceIn(25f, 200f)) },
                    valueRange = 25f..200f,
                    enabled = hasSelection,
                    colors = SliderDefaults.colors(
                        thumbColor = WudroidCyan,
                        activeTrackColor = WudroidCyan,
                        inactiveTrackColor = WudroidDrawerOutline,
                        disabledThumbColor = WudroidDrawerOutline,
                        disabledActiveTrackColor = WudroidDrawerOutline,
                        disabledInactiveTrackColor = WudroidDrawerOutline,
                    ),
                )

                if (!hasSelection) {
                    Text(
                        text = "Toque em um botão do controle para editar somente o tamanho dele.",
                        color = WudroidDrawerMuted,
                        fontSize = 12.sp,
                        modifier = Modifier.padding(top = 2.dp, bottom = 4.dp),
                    )
                }

                Row(
                    modifier = Modifier.fillMaxWidth().padding(top = 4.dp),
                    horizontalArrangement = Arrangement.spacedBy(12.dp, Alignment.End),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    TextButton(onClick = onResetClick) {
                        Text("Reset", color = WudroidDrawerText)
                    }
                    Button(onClick = onFinishClick) {
                        Text("Concluir")
                    }
                }

                // Center-bottom handle: smoothly tucks the whole panel upward.
                Box(
                    modifier = Modifier.fillMaxWidth(),
                    contentAlignment = Alignment.Center,
                ) {
                    TextButton(onClick = { onCollapseChange(true) }) {
                        Text("▲", color = WudroidCyan, fontSize = 18.sp, fontWeight = FontWeight.Bold)
                    }
                }
            }
        }

        AnimatedVisibility(
            visible = isCollapsed,
            modifier = Modifier.align(Alignment.TopCenter),
            enter = slideInVertically(
                animationSpec = tween(durationMillis = 210),
                initialOffsetY = { -it },
            ) + fadeIn(animationSpec = tween(160)),
            exit = slideOutVertically(
                animationSpec = tween(durationMillis = 180),
                targetOffsetY = { -it },
            ) + fadeOut(animationSpec = tween(120)),
        ) {
            // When collapsed this is the only editor chrome left on screen.
            TextButton(
                onClick = { onCollapseChange(false) },
                modifier = Modifier
                    .padding(top = 4.dp)
                    .background(WudroidDrawerBackground, RoundedCornerShape(18.dp)),
            ) {
                Text("▼", color = WudroidCyan, fontSize = 18.sp, fontWeight = FontWeight.Bold)
            }
        }
    }
}
'''
screen, fn_count = replace_function(screen, 'EditInputsLayout', new_editor_fn)
if fn_count != 1:
    raise SystemExit('Test8 EditInputsLayout function missing structurally')

# ---------------------------------------------------------------------------
# InputOverlaySurfaceView: persistent selected input + per-input scale.
# A translucent cyan overlay makes the selected button obvious.
# ---------------------------------------------------------------------------
for imp in [
    'import android.graphics.Color',
    'import android.graphics.Paint',
]:
    if imp not in overlay:
        overlay = overlay.replace('import android.graphics.Canvas\n', 'import android.graphics.Canvas\n' + imp + '\n', 1)

listener_anchor = '    var onEditAlphaFinishedListener: ((Int) -> Unit)? = null // WUDROID_GAMEPAD_EDITOR_TEST7\n'
if listener_anchor not in overlay:
    raise SystemExit('Test8 alpha listener anchor missing')
overlay = overlay.replace(
    listener_anchor,
    listener_anchor + '    var onWudroidSelectionChangedListener: ((Boolean) -> Unit)? = null // WUDROID_GAMEPAD_EDITOR_TEST8_INDIVIDUAL\n',
    1,
)

field_anchor = '    private var wudroidTransientRectangles: Map<OverlayInputConfig, Rect>? = null\n'
if field_anchor not in overlay:
    raise SystemExit('Test8 transient rectangle field anchor missing')
overlay = overlay.replace(
    field_anchor,
    field_anchor +
    '    private var wudroidSelectedConfig: OverlayInputConfig? = null\n'
    '    private var wudroidSelectedInput: Input? = null\n'
    '    private var wudroidSelectedScale = 1f\n'
    '    private val wudroidSelectionFillPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {\n'
    '        color = Color.argb(72, 0, 188, 255)\n'
    '        style = Paint.Style.FILL\n'
    '    }\n'
    '    private val wudroidSelectionStrokePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {\n'
    '        color = Color.argb(210, 0, 188, 255)\n'
    '        style = Paint.Style.STROKE\n'
    '        strokeWidth = 2.5f * context.resources.displayMetrics.density\n'
    '    }\n',
    1,
)

# Selection helpers are inserted before setInputMode.
set_mode_region = find_function_region(overlay, 'setInputMode')
if set_mode_region is None:
    raise SystemExit('Test8 setInputMode missing')
helper_insert = set_mode_region[0]
selection_helpers = r'''    private fun setWudroidEditorSelection(config: OverlayInputConfig?, input: Input?) {
        wudroidSelectedConfig = config
        wudroidSelectedInput = input
        wudroidSelectedScale = 1f
        onWudroidSelectionChangedListener?.invoke(config != null && input != null)
        invalidate()
    }

    private fun clearWudroidEditorSelection(notify: Boolean = true) {
        wudroidSelectedConfig = null
        wudroidSelectedInput = null
        wudroidSelectedScale = 1f
        if (notify) onWudroidSelectionChangedListener?.invoke(false)
        invalidate()
    }

    private fun restoreWudroidSelectedInput() {
        val selectedConfig = wudroidSelectedConfig ?: run {
            wudroidSelectedInput = null
            return
        }
        wudroidSelectedInput = inputs.firstOrNull { it.first.toConfig() == selectedConfig }?.second
        if (wudroidSelectedInput == null) {
            clearWudroidEditorSelection()
        }
    }

'''
overlay = overlay[:helper_insert] + selection_helpers + overlay[helper_insert:]

new_set_mode = r'''    fun setInputMode(inputMode: InputMode) {
        if (this.inputMode == inputMode) {
            return
        }

        val previousMode = this.inputMode
        this.inputMode = inputMode

        if (previousMode == InputMode.DEFAULT && inputMode != InputMode.DEFAULT) {
            wudroidEditorScale = 1f
            clearWudroidEditorSelection(notify = false)
        }

        if (this.inputMode != InputMode.DEFAULT) {
            return
        }

        val inputsRectangles =
            inputs.associate { it.first.toConfig() to it.second.getBoundingRectangle() }
        onEditFinishedListener?.invoke(inputsRectangles)
        wudroidEditorAlphaOverride?.let { onEditAlphaFinishedListener?.invoke(it) }
        wudroidEditorAlphaOverride = null
        wudroidEditorScale = 1f
        clearWudroidEditorSelection(notify = false)
    }
'''
overlay, count = replace_function(overlay, 'setInputMode', new_set_mode)
if count != 1:
    raise SystemExit('Test8 could not replace setInputMode')

# Settings rebuilds (e.g. Reset) need to re-bind the selected object because
# Input instances are recreated. Reset also becomes the new 100% baseline.
new_apply_settings = r'''    fun applySettings(inputOverlaySettings: InputOverlaySettings) {
        if (this.settings == inputOverlaySettings) {
            return
        }

        this.settings = inputOverlaySettings
        setInputs()
        if (inputMode != InputMode.DEFAULT && wudroidSelectedConfig != null) {
            wudroidSelectedScale = 1f
            restoreWudroidSelectedInput()
        }
        invalidate()
    }
'''
overlay, count = replace_function(overlay, 'applySettings', new_apply_settings)
if count != 1:
    raise SystemExit('Test8 could not replace applySettings')

# Alpha preview rebuilds Input instances too, but keeps the current per-button
# scale as-is because transient rectangles preserve the live geometry.
new_alpha = r'''    fun setWudroidEditorAlpha(alpha: Int?) {
        if (inputMode == InputMode.DEFAULT && alpha == null) {
            wudroidEditorAlphaOverride = null
            return
        }
        if (alpha == null || wudroidEditorAlphaOverride == alpha) return

        wudroidTransientRectangles = inputs.associate {
            val rect = it.second.getBoundingRectangle()
            it.first.toConfig() to Rect(rect.left, rect.top, rect.right, rect.bottom)
        }
        wudroidEditorAlphaOverride = alpha.coerceIn(0, 255)
        setInputs()
        restoreWudroidSelectedInput()
        wudroidTransientRectangles = null
        invalidate()
    }
'''
overlay, count = replace_function(overlay, 'setWudroidEditorAlpha', new_alpha)
if count != 1:
    raise SystemExit('Test8 could not replace setWudroidEditorAlpha')

# Test7 global scaler stays available internally but is no longer driven by the
# UI. Test8 adds a dedicated scaler for ONLY the currently selected control.
scale_region = find_function_region(overlay, 'setWudroidEditorScale')
if scale_region is None:
    raise SystemExit('Test8 setWudroidEditorScale missing')
selected_scale_api = r'''
    fun setWudroidSelectedInputScale(scale: Float) {
        if (inputMode == InputMode.DEFAULT || width <= 0 || height <= 0) return
        val selected = wudroidSelectedInput ?: return

        val targetScale = scale.coerceIn(0.25f, 2.0f)
        val ratio = targetScale / wudroidSelectedScale
        if (ratio in 0.999f..1.001f) return

        val before = selected.getBoundingRectangle()
        val beforeWidth = before.right - before.left
        val beforeHeight = before.bottom - before.top
        val centerX = before.left + beforeWidth / 2
        val centerY = before.top + beforeHeight / 2
        val targetWidth = (beforeWidth * ratio).roundToInt().coerceAtLeast(inputsMinSize)
        val targetHeight = (beforeHeight * ratio).roundToInt().coerceAtLeast(inputsMinSize)

        selected.resize(
            diffX = targetWidth - beforeWidth,
            diffY = targetHeight - beforeHeight,
            maxWidth = width,
            maxHeight = height,
            minWidthHeight = inputsMinSize,
        )
        selected.moveInput(centerX, centerY, width, height)
        wudroidSelectedScale = targetScale
        invalidate()
    }
'''
overlay = overlay[:scale_region[1]] + selected_scale_api + overlay[scale_region[1]:]

# Selection + moving share EDIT_POSITION. A tap selects without immediately
# jumping the control; dragging after the tap still moves it naturally.
new_edit_position = r'''    private fun onEditPosition(event: MotionEvent): Boolean {
        val configuredInput = currentConfiguredInput

        if (event.actionMasked == MotionEvent.ACTION_DOWN) {
            if (configuredInput != null) return false

            val x = event.x
            val y = event.y
            for ((overlayInput, input) in inputs.asReversed()) {
                if (input.isInside(x, y)) {
                    setWudroidEditorSelection(overlayInput.toConfig(), input)
                    currentConfiguredInput = input
                    return true
                }
            }

            clearWudroidEditorSelection()
            return true
        }

        if (configuredInput == null) {
            return false
        }

        if (event.actionMasked == MotionEvent.ACTION_UP || event.actionMasked == MotionEvent.ACTION_CANCEL) {
            currentConfiguredInput = null
            return true
        }

        if (event.actionMasked == MotionEvent.ACTION_MOVE) {
            configuredInput.moveInput(event.x.toInt(), event.y.toInt(), width, height)
            return true
        }

        return false
    }
'''
overlay, count = replace_function(overlay, 'onEditPosition', new_edit_position)
if count != 1:
    raise SystemExit('Test8 could not replace onEditPosition')

# Draw a translucent cyan tint over the selected control's rectangle. This is
# separate from the old purple/red edit symbols and therefore stays clean.
new_draw = r'''    override fun draw(canvas: Canvas) {
        super.draw(canvas)

        for ((overlayInput, input) in inputs) {
            input.draw(canvas)
            if (inputMode != InputMode.DEFAULT && overlayInput.toConfig() == wudroidSelectedConfig) {
                val rect = input.getBoundingRectangle()
                val radius = 12f * resources.displayMetrics.density
                canvas.drawRoundRect(
                    rect.left.toFloat(),
                    rect.top.toFloat(),
                    rect.right.toFloat(),
                    rect.bottom.toFloat(),
                    radius,
                    radius,
                    wudroidSelectionFillPaint,
                )
                canvas.drawRoundRect(
                    rect.left.toFloat(),
                    rect.top.toFloat(),
                    rect.right.toFloat(),
                    rect.bottom.toFloat(),
                    radius,
                    radius,
                    wudroidSelectionStrokePaint,
                )
            }
        }
    }
'''
overlay, count = replace_function(overlay, 'draw', new_draw)
if count != 1:
    raise SystemExit('Test8 could not replace draw')

# Extend the Compose bridge. editorScale remains for backwards compatibility
# but Test8 UI always sends 1f; editorSelectedScale is the live individual one.
new_surface_fn = r'''@Composable
fun InputOverlaySurface(
    isVisible: Boolean,
    inputOverlaySettings: InputOverlaySettings,
    inputMode: InputOverlaySurfaceView.InputMode,
    editorAlpha: Int? = null,
    editorScale: Float = 1f,
    editorSelectedScale: Float = 1f,
    onEditFinished: (Map<OverlayInputConfig, InputOverlayRect>) -> Unit,
    onEditAlphaFinished: (Int) -> Unit = {},
    onEditorSelectionChanged: (Boolean) -> Unit = {},
) {
    AndroidView(
        modifier = Modifier.fillMaxSize(),
        factory = { context ->
            InputOverlaySurfaceView(context).apply {
                setVisible(isVisible)
                applySettings(inputOverlaySettings)
                onEditFinishedListener = onEditFinished
                onEditAlphaFinishedListener = onEditAlphaFinished
                onWudroidSelectionChangedListener = onEditorSelectionChanged
                setInputMode(inputMode)
                setWudroidEditorAlpha(editorAlpha)
                setWudroidEditorScale(editorScale)
                setWudroidSelectedInputScale(editorSelectedScale)
            }
        },
        update = { view ->
            view.setVisible(isVisible)
            view.applySettings(inputOverlaySettings)
            view.onEditFinishedListener = onEditFinished
            view.onEditAlphaFinishedListener = onEditAlphaFinished
            view.onWudroidSelectionChangedListener = onEditorSelectionChanged
            view.setInputMode(inputMode)
            view.setWudroidEditorAlpha(editorAlpha)
            view.setWudroidEditorScale(editorScale)
            view.setWudroidSelectedInputScale(editorSelectedScale)
        }
    )
}
'''
overlay, count = replace_function(overlay, 'InputOverlaySurface', new_surface_fn)
if count != 1:
    raise SystemExit('Test8 InputOverlaySurface composable missing')

# BuildFix1 regression guard: the old parser stopped at the default `{}`
# lambda in the parameter list and left a second stale AndroidView body.
# After a correct replacement there must be exactly one composable signature
# and one factory call using the new selection callback.
if overlay.count('fun InputOverlaySurface(') != 1:
    raise SystemExit('BuildFix1 verification: duplicate InputOverlaySurface function remains')
if overlay.count('onWudroidSelectionChangedListener = onEditorSelectionChanged') != 2:
    raise SystemExit('BuildFix1 verification: InputOverlaySurface bridge body is incomplete')

screen_path.write_text(screen)
overlay_path.write_text(overlay)

# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------
checks = {
    screen_path: [
        marker,
        'wudroidEditorPanelCollapsed',
        'wudroidEditorHasSelection',
        'Text("▲"',
        'Text("▼"',
        'editorSelectedScale =',
        'onEditorSelectionChanged =',
        'enabled = hasSelection',
    ],
    overlay_path: [
        'wudroidSelectedConfig',
        'setWudroidSelectedInputScale',
        'onWudroidSelectionChangedListener',
        'Color.argb(72, 0, 188, 255)',
        'setWudroidEditorSelection(overlayInput.toConfig(), input)',
    ],
}
for path, required in checks.items():
    text = path.read_text()
    missing = [x for x in required if x not in text]
    if missing:
        raise SystemExit(f'Test8 verification failed in {path}: ' + ', '.join(missing))

print('Wudroid 0.1.1 Gamepad Editor Test8 Individual Size applied')
print('- existing in-game menus left untouched')
print('- editor panel collapses upward with smooth animation')
print('- collapsed state leaves only a centered down-arrow button')
print('- tap a touch control to select it with translucent cyan highlight')
print('- Size slider changes only the selected control')
print('- Transparency remains global')
print('- Reset + Concluir preserved')
