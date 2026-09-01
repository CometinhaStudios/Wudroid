#!/usr/bin/env python3
from pathlib import Path
import re

screen_path = Path('cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationScreen.kt')
viewmodel_path = Path('cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationViewModel.kt')
overlay_path = Path('cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/inputoverlay/InputOverlaySurfaceView.kt')

for p in (screen_path, viewmodel_path, overlay_path):
    if not p.exists():
        raise SystemExit(f'Required source not found: {p}')

screen = screen_path.read_text()
viewmodel = viewmodel_path.read_text()
overlay = overlay_path.read_text()
marker = 'WUDROID_GAMEPAD_EDITOR_TEST7'

if marker in screen:
    print('Wudroid Gamepad Editor Test7 already applied')
    raise SystemExit(0)

if 'WUDROID_MENU_FLOW_GAMEPAD_TEST6' not in screen:
    raise SystemExit('Menu Flow + Gamepad Test6 must be applied before Test7')

# ---------------------------------------------------------------------------
# EmulationScreen: replace the old Done / Move / Resize editor with a clean
# Wudroid panel containing global transparency + size sliders and Reset/Done.
# ---------------------------------------------------------------------------
for imp in [
    'import androidx.compose.material3.Slider',
    'import androidx.compose.material3.SliderDefaults',
]:
    if imp not in screen:
        screen = screen.replace('package info.cemu.cemu.emulation\n', 'package info.cemu.cemu.emulation\n' + imp + '\n', 1)

state_anchor = '    var inputOverlayInputMode by rememberSaveable { mutableStateOf(DEFAULT) }\n'
if state_anchor not in screen:
    raise SystemExit('inputOverlayInputMode state anchor missing')
screen = screen.replace(
    state_anchor,
    state_anchor +
    '    var wudroidEditorAlpha by rememberSaveable { mutableFloatStateOf(128f) } // WUDROID_GAMEPAD_EDITOR_TEST7\n'
    '    var wudroidEditorSizePercent by rememberSaveable { mutableFloatStateOf(100f) }\n',
    1,
)

old_edit_cb = '''                        onEditInputOverlay = {
                            snackbarHostState.showMessage(scope, tr("Edit input positions"))
                            inputOverlayInputMode = EDIT_POSITION
                            closeDrawer()
                        },
'''
new_edit_cb = '''                        onEditInputOverlay = {
                            wudroidEditorAlpha = inputOverlaySettings.alpha.toFloat()
                            wudroidEditorSizePercent = 100f
                            inputOverlayInputMode = EDIT_POSITION
                            closeDrawer()
                        },
'''
if old_edit_cb not in screen:
    raise SystemExit('onEditInputOverlay callback anchor missing')
screen = screen.replace(old_edit_cb, new_edit_cb, 1)

old_surface = '''        InputOverlaySurface(
            isVisible = isInputOverlayVisible,
            inputOverlaySettings = inputOverlaySettings,
            inputMode = inputOverlayInputMode,
            onEditFinished = { viewModel.saveInputOverlayRectangles(it) },
        )
'''
new_surface = '''        InputOverlaySurface(
            isVisible = isInputOverlayVisible,
            inputOverlaySettings = inputOverlaySettings,
            inputMode = inputOverlayInputMode,
            editorAlpha = if (inputOverlayInputMode == DEFAULT) null else wudroidEditorAlpha.toInt(),
            editorScale = if (inputOverlayInputMode == DEFAULT) 1f else wudroidEditorSizePercent / 100f,
            onEditFinished = { viewModel.saveInputOverlayRectangles(it) },
            onEditAlphaFinished = { viewModel.saveInputOverlayAlpha(it) },
        )
'''
if old_surface not in screen:
    raise SystemExit('InputOverlaySurface call anchor missing')
screen = screen.replace(old_surface, new_surface, 1)

old_editor_call_re = re.compile(
    r'''        if \(inputOverlayInputMode != DEFAULT\) \{\n            EditInputsLayout\(\n.*?            \)\n        \}\n''',
    re.S,
)
new_editor_call = '''        if (inputOverlayInputMode != DEFAULT) {
            EditInputsLayout(
                alpha = wudroidEditorAlpha,
                sizePercent = wudroidEditorSizePercent,
                onAlphaChange = { wudroidEditorAlpha = it },
                onSizeChange = { wudroidEditorSizePercent = it },
                onResetClick = {
                    wudroidEditorAlpha = 128f
                    wudroidEditorSizePercent = 100f
                    viewModel.resetInputOverlayLayout()
                },
                onFinishClick = {
                    snackbarHostState.showMessage(scope, "Controles salvos")
                    inputOverlayInputMode = DEFAULT
                },
            )
        }
'''
screen, editor_call_count = old_editor_call_re.subn(new_editor_call, screen, count=1)
if editor_call_count != 1:
    raise SystemExit('EditInputsLayout call region missing')

# BuildFix2: locate the Kotlin function structurally instead of assuming what
# composable comes immediately after it. Previous builds changed the order of
# helper composables, so the old regex could see the call but miss the function.
def replace_kotlin_function(text: str, function_name: str, replacement: str):
    match = re.search(r"(?m)^[ \t]*(?:private[ \t]+)?fun[ \t]+" + re.escape(function_name) + r"[ \t]*\(", text)
    if not match:
        return text, 0

    # Include @Composable and any immediately-adjacent annotations in the
    # replacement when they belong to this function.
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

    brace = text.find("{", match.end())
    if brace < 0:
        return text, 0

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
                return text[:start] + replacement + text[end:], 1
        i += 1

    return text, 0

new_editor_fn = r'''@Composable
private fun EditInputsLayout(
    alpha: Float,
    sizePercent: Float,
    onAlphaChange: (Float) -> Unit,
    onSizeChange: (Float) -> Unit,
    onResetClick: () -> Unit,
    onFinishClick: () -> Unit,
) {
    // WUDROID_GAMEPAD_EDITOR_TEST7
    // The controller itself stays directly draggable. Per-button resize icons are
    // removed; size and transparency are now global sliders at the top.
    Box(modifier = Modifier.fillMaxSize()) {
        Column(
            modifier = Modifier
                .align(Alignment.TopCenter)
                .padding(horizontal = 18.dp, vertical = 14.dp)
                .fillMaxWidth(0.92f)
                .background(WudroidDrawerBackground, RoundedCornerShape(20.dp))
                .padding(horizontal = 18.dp, vertical = 14.dp),
        ) {
            Text(
                text = "Editar controles",
                color = WudroidCyan,
                fontSize = 20.sp,
                fontWeight = FontWeight.Bold,
            )

            Row(
                modifier = Modifier.fillMaxWidth().padding(top = 10.dp),
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
                modifier = Modifier.fillMaxWidth().padding(top = 2.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text("Tamanho", color = WudroidDrawerText, modifier = Modifier.weight(1f))
                Text("${sizePercent.toInt()}%", color = WudroidCyan, fontWeight = FontWeight.Bold)
            }
            Slider(
                value = sizePercent,
                onValueChange = { onSizeChange(it.coerceIn(25f, 200f)) },
                valueRange = 25f..200f,
                colors = SliderDefaults.colors(
                    thumbColor = WudroidCyan,
                    activeTrackColor = WudroidCyan,
                    inactiveTrackColor = WudroidDrawerOutline,
                ),
            )

            Row(
                modifier = Modifier.fillMaxWidth().padding(top = 6.dp),
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
        }
    }
}
'''
screen, editor_fn_count = replace_kotlin_function(screen, "EditInputsLayout", new_editor_fn)
if editor_fn_count != 1:
    # Debug output is intentionally useful in Actions if upstream changes again.
    candidates = [line.strip() for line in screen.splitlines() if "EditInputs" in line]
    raise SystemExit("EditInputsLayout function not found structurally. Candidates: " + repr(candidates[:20]))

# ---------------------------------------------------------------------------
# ViewModel: persist the chosen transparency only when editor is concluded.
# ---------------------------------------------------------------------------
vm_alpha_fn = r'''
    fun saveInputOverlayAlpha(alpha: Int) {
        viewModelScope.launch {
            dataStore.updateData {
                val overlaySettings = it.inputOverlaySettings.copy(alpha = alpha.coerceIn(0, 255))
                it.copy(inputOverlaySettings = overlaySettings)
            }
        }
    }
'''
if 'fun saveInputOverlayAlpha(alpha: Int)' not in viewmodel:
    vm_match = re.search(r"(?m)^[ \t]*fun[ \t]+saveInputOverlayRectangles[ \t]*\(", viewmodel)
    if not vm_match:
        raise SystemExit('saveInputOverlayRectangles function missing')
    vm_brace = viewmodel.find('{', vm_match.end())
    if vm_brace < 0:
        raise SystemExit('saveInputOverlayRectangles opening brace missing')
    depth = 0
    vm_end = None
    for i in range(vm_brace, len(viewmodel)):
        if viewmodel[i] == '{': depth += 1
        elif viewmodel[i] == '}':
            depth -= 1
            if depth == 0:
                vm_end = i + 1
                break
    if vm_end is None:
        raise SystemExit('saveInputOverlayRectangles closing brace missing')
    viewmodel = viewmodel[:vm_end] + '\n' + vm_alpha_fn + viewmodel[vm_end:]

# ---------------------------------------------------------------------------
# InputOverlaySurfaceView:
# - remove Test6's automatic 1.60x runtime scaler (source of compounding)
# - no per-button resize mode in the editor
# - global size slider scales all existing controls relative to the CURRENT
#   editor session, so pressing Done repeatedly can never multiply them again
# - alpha preview preserves unsaved positions/sizes while rebuilding drawings
# ---------------------------------------------------------------------------
overlay = overlay.replace(
    '    private val currentAlpha get() = settings.alpha\n',
    '    private val currentAlpha get() = wudroidEditorAlphaOverride ?: settings.alpha\n',
    1,
)

listener_anchor = '''    var onEditFinishedListener: ((Map<OverlayInputConfig, InputOverlayRect>) -> Unit)? =
        null
'''
if listener_anchor not in overlay:
    raise SystemExit('onEditFinishedListener anchor missing')
overlay = overlay.replace(
    listener_anchor,
    listener_anchor + '    var onEditAlphaFinishedListener: ((Int) -> Unit)? = null // WUDROID_GAMEPAD_EDITOR_TEST7\n',
    1,
)

field_anchor = '    private var inputMode = InputMode.DEFAULT\n'
if field_anchor not in overlay:
    raise SystemExit('inputMode field anchor missing')
overlay = overlay.replace(
    field_anchor,
    field_anchor +
    '    private var wudroidEditorAlphaOverride: Int? = null\n'
    '    private var wudroidEditorScale = 1f\n'
    '    private var wudroidTransientRectangles: Map<OverlayInputConfig, Rect>? = null\n',
    1,
)

set_mode_fn = r'''    fun setInputMode(inputMode: InputMode) {
        if (this.inputMode == inputMode) {
            return
        }

        val previousMode = this.inputMode
        this.inputMode = inputMode

        if (previousMode == InputMode.DEFAULT && inputMode != InputMode.DEFAULT) {
            wudroidEditorScale = 1f
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
    }
'''
overlay, set_mode_count = replace_kotlin_function(overlay, "setInputMode", set_mode_fn)
if set_mode_count != 1:
    candidates = [line.strip() for line in overlay.splitlines() if "setInputMode" in line]
    raise SystemExit("setInputMode function not found structurally. Candidates: " + repr(candidates[:20]))

# Remove Test6's automatic scaler structurally, then replace normal rectangle lookup.
if 'fun wudroidScaleOverlayRect' in overlay:
    overlay, removed_scale_fn = replace_kotlin_function(overlay, "wudroidScaleOverlayRect", "")
    if removed_scale_fn != 1:
        raise SystemExit('wudroidScaleOverlayRect function could not be removed structurally')

replacement_rect_fn = r'''    // WUDROID_GAMEPAD_EDITOR_TEST7
    private fun getBoundingRectangleForInput(input: OverlayInput): Rect {
        val config = input.toConfig()
        val transient = wudroidTransientRectangles?.get(config)
        if (transient != null) {
            return Rect(transient.left, transient.top, transient.right, transient.bottom)
        }

        val saved = settings.inputOverlayRectMap[config]
        if (saved != null) {
            return Rect(saved.left, saved.top, saved.right, saved.bottom)
        }

        return getDefaultRectangle(config, width, height, pixelDensity)
    }
'''
overlay, rect_count = replace_kotlin_function(overlay, "getBoundingRectangleForInput", replacement_rect_fn)
if rect_count != 1:
    raise SystemExit('getBoundingRectangleForInput function not found structurally')


editor_api_anchor = replacement_rect_fn
editor_api = r'''
    fun setWudroidEditorAlpha(alpha: Int?) {
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
        wudroidTransientRectangles = null
        invalidate()
    }

    fun setWudroidEditorScale(scale: Float) {
        if (inputMode == InputMode.DEFAULT || width <= 0 || height <= 0) return

        val targetScale = scale.coerceIn(0.25f, 2.0f)
        val ratio = targetScale / wudroidEditorScale
        if (ratio in 0.999f..1.001f) return

        for ((_, input) in inputs) {
            val before = input.getBoundingRectangle()
            val centerX = before.centerX()
            val centerY = before.centerY()
            val targetWidth = (before.width() * ratio).roundToInt().coerceAtLeast(inputsMinSize)
            val targetHeight = (before.height() * ratio).roundToInt().coerceAtLeast(inputsMinSize)

            input.resize(
                diffX = targetWidth - before.width(),
                diffY = targetHeight - before.height(),
                maxWidth = width,
                maxHeight = height,
                minWidthHeight = inputsMinSize,
            )
            input.moveInput(centerX, centerY, width, height)
        }

        wudroidEditorScale = targetScale
        invalidate()
    }
'''
# Insert editor APIs immediately after getBoundingRectangleForInput.
rect_match = re.search(r"(?m)^[ \t]*private[ \t]+fun[ \t]+getBoundingRectangleForInput[ \t]*\(", overlay)
if not rect_match:
    raise SystemExit('getBoundingRectangleForInput missing after replacement')
brace = overlay.find('{', rect_match.end())
depth = 0
rect_end = None
for i in range(brace, len(overlay)):
    if overlay[i] == '{': depth += 1
    elif overlay[i] == '}':
        depth -= 1
        if depth == 0:
            rect_end = i + 1
            break
if rect_end is None:
    raise SystemExit('getBoundingRectangleForInput closing brace missing')
overlay = overlay[:rect_end] + '\n' + editor_api + overlay[rect_end:]

# Remove colored bounding-rectangle symbols while moving controls.
overlay = re.sub(
    r'''\n\s*input\.enableDrawingBoundingRect\(\n\s*resources\.getColor\(R\.color\.purple, context\.theme\)\n\s*\)''',
    '',
    overlay,
    count=1,
)
overlay = overlay.replace('            configuredInput.disableDrawingBoundingRect()\n', '', 1)

# Extend InputOverlaySurface composable structurally.
surface_fn = r'''@Composable
fun InputOverlaySurface(
    isVisible: Boolean,
    inputOverlaySettings: InputOverlaySettings,
    inputMode: InputOverlaySurfaceView.InputMode,
    editorAlpha: Int? = null,
    editorScale: Float = 1f,
    onEditFinished: (Map<OverlayInputConfig, InputOverlayRect>) -> Unit,
    onEditAlphaFinished: (Int) -> Unit = {},
) {
    AndroidView(
        modifier = Modifier.fillMaxSize(),
        factory = { context ->
            InputOverlaySurfaceView(context).apply {
                setVisible(isVisible)
                applySettings(inputOverlaySettings)
                onEditFinishedListener = onEditFinished
                onEditAlphaFinishedListener = onEditAlphaFinished
                setInputMode(inputMode)
                setWudroidEditorAlpha(editorAlpha)
                setWudroidEditorScale(editorScale)
            }
        },
        update = { view ->
            view.setVisible(isVisible)
            view.applySettings(inputOverlaySettings)
            view.onEditFinishedListener = onEditFinished
            view.onEditAlphaFinishedListener = onEditAlphaFinished
            view.setInputMode(inputMode)
            view.setWudroidEditorAlpha(editorAlpha)
            view.setWudroidEditorScale(editorScale)
        }
    )
}
'''
overlay, surface_count = replace_kotlin_function(overlay, "InputOverlaySurface", surface_fn)
if surface_count != 1:
    raise SystemExit('InputOverlaySurface composable not found structurally')

screen_path.write_text(screen)
viewmodel_path.write_text(viewmodel)
overlay_path.write_text(overlay)

# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------
checks = {
    screen_path: [
        marker,
        'text = "Editar controles"',
        'Text("Transparência"',
        'Text("Tamanho"',
        'Text("Reset"',
        'Text("Concluir")',
        'editorScale = if (inputOverlayInputMode == DEFAULT)',
    ],
    viewmodel_path: ['fun saveInputOverlayAlpha(alpha: Int)'],
    overlay_path: [
        'setWudroidEditorScale',
        'setWudroidEditorAlpha',
        'wudroidEditorScale = 1f',
        'onEditAlphaFinishedListener',
    ],
}
for path, required in checks.items():
    text = path.read_text()
    missing = [x for x in required if x not in text]
    if missing:
        raise SystemExit(f'Test7 verification failed in {path}: ' + ', '.join(missing))

if 'wudroidScaleOverlayRect' in overlay_path.read_text():
    raise SystemExit('Test7 failed: old Test6 automatic gamepad scaler still exists')

print('Wudroid 0.1.1 Gamepad Editor Test7 RobustFix applied')
print('- menu flow from Test6 left unchanged')
print('- old per-button Move/Resize editor UI removed')
print('- top Wudroid editor panel: Transparency + Size')
print('- Reset + Concluir buttons')
print('- size is relative to each edit session; Done no longer compounds size')
print('- transparency previews live and persists on Concluir')
print('- controls remain draggable for position editing')
