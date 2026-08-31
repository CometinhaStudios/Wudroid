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

editor_fn_re = re.compile(
    r'''@Composable\nprivate fun EditInputsLayout\(.*?\n\}\n(?=@Composable\nprivate fun EmulationSideMenuContent)''',
    re.S,
)
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
screen, editor_fn_count = editor_fn_re.subn(new_editor_fn, screen, count=1)
if editor_fn_count != 1:
    raise SystemExit('EditInputsLayout function region missing')

# ---------------------------------------------------------------------------
# ViewModel: persist the chosen transparency only when editor is concluded.
# ---------------------------------------------------------------------------
vm_anchor = '''    fun saveInputOverlayRectangles(inputOverlayRectMap: Map<OverlayInputConfig, InputOverlayRect>) {
        viewModelScope.launch {
            dataStore.updateData {
                val overlaySettings =
                    it.inputOverlaySettings.copy(inputOverlayRectMap = inputOverlayRectMap)
                it.copy(inputOverlaySettings = overlaySettings)
            }
        }
    }
'''
if vm_anchor not in viewmodel:
    raise SystemExit('saveInputOverlayRectangles anchor missing')
vm_extra = vm_anchor + '''
    fun saveInputOverlayAlpha(alpha: Int) {
        viewModelScope.launch {
            dataStore.updateData {
                val overlaySettings = it.inputOverlaySettings.copy(alpha = alpha.coerceIn(0, 255))
                it.copy(inputOverlaySettings = overlaySettings)
            }
        }
    }
'''
viewmodel = viewmodel.replace(vm_anchor, vm_extra, 1)

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

set_mode_re = re.compile(
    r'''    fun setInputMode\(inputMode: InputMode\) \{.*?\n    \}\n(?=    private fun overlayButtonToVPADButton)''',
    re.S,
)
set_mode_fn = r'''    fun setInputMode(inputMode: InputMode) {
        if (this.inputMode == inputMode) {
            return
        }

        val previousMode = this.inputMode
        this.inputMode = inputMode

        if (previousMode == InputMode.DEFAULT && inputMode != InputMode.DEFAULT) {
            // 100% always means "the size when this edit session started".
            // This is what prevents the old Done -> grow -> Done -> grow loop.
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
overlay, set_mode_count = set_mode_re.subn(set_mode_fn, overlay, count=1)
if set_mode_count != 1:
    raise SystemExit('setInputMode function region missing')

# Replace Test6's forced scale block with normal rectangle lookup + editor APIs.
scale_block_re = re.compile(
    r'''    // WUDROID_MENU_FLOW_GAMEPAD_TEST6\n    // Scale both saved and default Cemu touch rectangles around their centers\..*?    private fun getBoundingRectangleForInput\(input: OverlayInput\): Rect \{.*?\n    \}\n(?=    private fun MutableList<Pair<OverlayInput, Input>>\.addRoundButton)''',
    re.S,
)
replacement_rect_block = r'''    // WUDROID_GAMEPAD_EDITOR_TEST7
    // Normal runtime lookup: no automatic multiplier is applied when the
    // overlay is recreated. This removes Test6's compounding-size bug.
    private fun getBoundingRectangleForInput(input: OverlayInput): Rect {
        val config = input.toConfig()
        val rect = wudroidTransientRectangles?.get(config) ?: settings.inputOverlayRectMap[config]
        if (rect != null) {
            return Rect(rect.left, rect.top, rect.right, rect.bottom)
        }
        return getDefaultRectangle(config, width, height, pixelDensity)
    }

    fun setWudroidEditorAlpha(alpha: Int?) {
        if (inputMode == InputMode.DEFAULT && alpha == null) {
            wudroidEditorAlphaOverride = null
            return
        }
        if (alpha == null || wudroidEditorAlphaOverride == alpha) return

        // Re-create the drawings with the new alpha, but use the exact current
        // rectangles so unsaved movement/size changes are not lost.
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
overlay, scale_count = scale_block_re.subn(replacement_rect_block, overlay, count=1)
if scale_count != 1:
    raise SystemExit('Test6 forced scale block not found')

# Remove colored bounding-rectangle symbols while moving controls.
overlay = re.sub(
    r'''\n\s*input\.enableDrawingBoundingRect\(\n\s*resources\.getColor\(R\.color\.purple, context\.theme\)\n\s*\)''',
    '',
    overlay,
    count=1,
)
overlay = overlay.replace('            configuredInput.disableDrawingBoundingRect()\n', '', 1)

# Extend InputOverlaySurface composable so Compose sliders can control the real view.
surface_fn_re = re.compile(
    r'''@Composable\nfun InputOverlaySurface\(.*?\n\}\n\s*$''',
    re.S,
)
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
            // Save the live editor state before clearing preview overrides.
            view.setInputMode(inputMode)
            view.setWudroidEditorAlpha(editorAlpha)
            view.setWudroidEditorScale(editorScale)
        }
    )
}
'''
overlay, surface_count = surface_fn_re.subn(surface_fn, overlay, count=1)
if surface_count != 1:
    raise SystemExit('InputOverlaySurface composable region missing')

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

print('Wudroid 0.1.1 Gamepad Editor Test7 applied')
print('- menu flow from Test6 left unchanged')
print('- old per-button Move/Resize editor UI removed')
print('- top Wudroid editor panel: Transparency + Size')
print('- Reset + Concluir buttons')
print('- size is relative to each edit session; Done no longer compounds size')
print('- transparency previews live and persists on Concluir')
print('- controls remain draggable for position editing')
