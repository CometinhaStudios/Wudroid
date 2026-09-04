#!/usr/bin/env python3
from pathlib import Path
import re

screen_path = Path('cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationScreen.kt')
viewmodel_path = Path('cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationViewModel.kt')
overlay_path = Path('cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/inputoverlay/InputOverlaySurfaceView.kt')
settings_path = Path('cemu-engine/src/android/app/src/main/java/info/cemu/cemu/common/settings/Settings.kt')

for p in (screen_path, viewmodel_path, overlay_path, settings_path):
    if not p.exists():
        raise SystemExit(f'Layout Test14 Rebuild1: required source not found: {p}')

screen = screen_path.read_text()
viewmodel = viewmodel_path.read_text()
overlay = overlay_path.read_text()
settings = settings_path.read_text()
marker = 'WUDROID_LAYOUT_TEST14_REBUILD1'

if marker in screen and marker in overlay and marker in settings:
    print('Wudroid Layout Test14 Rebuild1 already applied')
    raise SystemExit(0)

if 'WUDROID_GAMEPAD_EDITOR_TEST8_INDIVIDUAL' not in screen or 'WUDROID_GAMEPAD_EDITOR_TEST8_INDIVIDUAL' not in overlay:
    raise SystemExit('Layout Test14 Rebuild1 requires the current individual gamepad editor (Test8) base')


def find_function_region(text: str, function_name: str):
    match = re.search(
        r'(?m)^[ \t]*(?:private[ \t]+)?(?:override[ \t]+)?fun[ \t]+' + re.escape(function_name) + r'[ \t]*\(',
        text,
    )
    if not match:
        return None

    start = match.start()
    line_start = text.rfind('\n', 0, start) + 1
    scan = line_start
    while scan > 0:
        prev_end = scan - 1
        prev_start = text.rfind('\n', 0, prev_end) + 1
        prev_line = text[prev_start:prev_end].strip()
        if prev_line.startswith('@'):
            start = prev_start
            scan = prev_start
            continue
        if prev_line == '':
            scan = prev_start
            continue
        break

    paren = text.find('(', match.start(), match.end())
    if paren < 0:
        return None

    pdepth = 0
    i = paren
    in_string = in_char = escape = line_comment = block_comment = False
    signature_end = None
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ''
        if line_comment:
            if ch == '\n': line_comment = False
            i += 1; continue
        if block_comment:
            if ch == '*' and nxt == '/': block_comment = False; i += 2
            else: i += 1
            continue
        if in_string:
            if escape: escape = False
            elif ch == '\\': escape = True
            elif ch == '"': in_string = False
            i += 1; continue
        if in_char:
            if escape: escape = False
            elif ch == '\\': escape = True
            elif ch == "'": in_char = False
            i += 1; continue
        if ch == '/' and nxt == '/': line_comment = True; i += 2; continue
        if ch == '/' and nxt == '*': block_comment = True; i += 2; continue
        if ch == '"': in_string = True; i += 1; continue
        if ch == "'": in_char = True; i += 1; continue
        if ch == '(':
            pdepth += 1
        elif ch == ')':
            pdepth -= 1
            if pdepth == 0:
                signature_end = i + 1
                break
        i += 1
    if signature_end is None:
        return None

    brace = text.find('{', signature_end)
    if brace < 0:
        return None

    depth = 0
    i = brace
    in_string = in_char = escape = line_comment = block_comment = False
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ''
        if line_comment:
            if ch == '\n': line_comment = False
            i += 1; continue
        if block_comment:
            if ch == '*' and nxt == '/': block_comment = False; i += 2
            else: i += 1
            continue
        if in_string:
            if escape: escape = False
            elif ch == '\\': escape = True
            elif ch == '"': in_string = False
            i += 1; continue
        if in_char:
            if escape: escape = False
            elif ch == '\\': escape = True
            elif ch == "'": in_char = False
            i += 1; continue
        if ch == '/' and nxt == '/': line_comment = True; i += 2; continue
        if ch == '/' and nxt == '*': block_comment = True; i += 2; continue
        if ch == '"': in_string = True; i += 1; continue
        if ch == "'": in_char = True; i += 1; continue
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                if end < len(text) and text[end] == '\n': end += 1
                return start, end
        i += 1
    return None


def replace_function(text: str, function_name: str, replacement: str):
    region = find_function_region(text, function_name)
    if region is None:
        return text, 0
    start, end = region
    return text[:start] + replacement + text[end:], 1


def ensure_import(source: str, imp: str) -> str:
    if imp in source:
        return source
    lines = source.splitlines(keepends=True)
    indexes = [i for i, line in enumerate(lines) if line.startswith('import ')]
    if not indexes:
        raise SystemExit('Layout Test14 Rebuild1: import block missing')
    lines.insert(indexes[-1] + 1, imp + '\n')
    return ''.join(lines)

# ---------------------------------------------------------------------------
# 1) Persist the Separar switch and the four independent D-pad rectangles.
#    Reset clears positions/sizes, but intentionally keeps the switch state.
# ---------------------------------------------------------------------------
settings_anchor = '    val inputOverlayRectMap: Map<OverlayInputConfig, InputOverlayRect> = emptyMap(),\n'
if settings_anchor not in settings:
    raise SystemExit('Layout Test14 Rebuild1: InputOverlaySettings rectangle-map anchor missing')
settings = settings.replace(
    settings_anchor,
    settings_anchor +
    '    val wudroidLayoutSeparated: Boolean = false, // WUDROID_LAYOUT_TEST14_REBUILD1\n'
    '    val wudroidSeparatedDpadRectMap: Map<String, InputOverlayRect> = emptyMap(),\n',
    1,
)

reset_old = 'it.inputOverlaySettings.copy(inputOverlayRectMap = emptyMap())'
reset_new = '''it.inputOverlaySettings.copy(
                        inputOverlayRectMap = emptyMap(),
                        wudroidSeparatedDpadRectMap = emptyMap(),
                    )'''
if reset_old in viewmodel:
    viewmodel = viewmodel.replace(reset_old, reset_new, 1)
elif 'wudroidSeparatedDpadRectMap = emptyMap()' not in viewmodel:
    raise SystemExit('Layout Test14 Rebuild1: resetInputOverlayLayout anchor missing')

vm_insert_anchor = '    fun resetInputOverlayLayout() {\n'
if vm_insert_anchor not in viewmodel:
    raise SystemExit('Layout Test14 Rebuild1: view-model reset function anchor missing')
vm_methods = r'''    // WUDROID_LAYOUT_TEST14_REBUILD1
    fun saveWudroidLayoutSeparated(separated: Boolean) {
        viewModelScope.launch {
            dataStore.updateData {
                val overlaySettings =
                    it.inputOverlaySettings.copy(wudroidLayoutSeparated = separated)
                it.copy(inputOverlaySettings = overlaySettings)
            }
        }
    }

    fun saveWudroidSeparatedDpadRectangles(rectangles: Map<String, InputOverlayRect>) {
        viewModelScope.launch {
            dataStore.updateData {
                val overlaySettings =
                    it.inputOverlaySettings.copy(wudroidSeparatedDpadRectMap = rectangles)
                it.copy(inputOverlaySettings = overlaySettings)
            }
        }
    }

'''
viewmodel = viewmodel.replace(vm_insert_anchor, vm_methods + vm_insert_anchor, 1)

# ---------------------------------------------------------------------------
# 2) Editor UI: rename to Editar layout and add Separar as a persistent switch.
# ---------------------------------------------------------------------------
for imp in [
    'import androidx.compose.material3.Switch',
    'import androidx.compose.material3.SwitchDefaults',
]:
    screen = ensure_import(screen, imp)

# Sidebar name, anchored to the callback so a future "Controles" item stays free.
sidebar_re = re.compile(
    r'(label\s*=\s*")Controles(",\s*\n\s*enabled\s*=\s*sideMenuState\.isInputOverlayVisible,\s*\n\s*onClick\s*=\s*onEditInputOverlay,)'
)
screen2, n = sidebar_re.subn(r'\1Editar layout\2 // WUDROID_LAYOUT_TEST14_REBUILD1', screen, count=1)
if n:
    screen = screen2
elif 'label = "Editar layout"' not in screen or 'onClick = onEditInputOverlay' not in screen:
    raise SystemExit('Layout Test14 Rebuild1: sidebar editor entry not found')

# Pass the switch state + save callback to the editor panel.
collapse_line = '                isCollapsed = wudroidEditorPanelCollapsed,\n'
if collapse_line not in screen:
    raise SystemExit('Layout Test14 Rebuild1: editor call isCollapsed anchor missing')
screen = screen.replace(
    collapse_line,
    collapse_line + '                isSeparated = inputOverlaySettings.wudroidLayoutSeparated,\n',
    1,
)

collapse_cb = '                onCollapseChange = { wudroidEditorPanelCollapsed = it },\n'
if collapse_cb not in screen:
    raise SystemExit('Layout Test14 Rebuild1: editor collapse callback anchor missing')
screen = screen.replace(
    collapse_cb,
    collapse_cb + '                onSeparatedChange = { viewModel.saveWudroidLayoutSeparated(it) },\n',
    1,
)

selection_cb = '''            onEditorSelectionChanged = { selected ->
                wudroidEditorHasSelection = selected
                wudroidEditorSizePercent = 100f
            },
'''
if selection_cb not in screen:
    raise SystemExit('Layout Test14 Rebuild1: InputOverlaySurface selection callback anchor missing')
screen = screen.replace(
    selection_cb,
    selection_cb + '            onSeparatedDpadEditFinished = { viewModel.saveWudroidSeparatedDpadRectangles(it) },\n',
    1,
)

new_editor_fn = r'''@Composable
private fun EditInputsLayout(
    alpha: Float,
    sizePercent: Float,
    hasSelection: Boolean,
    isCollapsed: Boolean,
    isSeparated: Boolean,
    onAlphaChange: (Float) -> Unit,
    onSizeChange: (Float) -> Unit,
    onCollapseChange: (Boolean) -> Unit,
    onSeparatedChange: (Boolean) -> Unit,
    onResetClick: () -> Unit,
    onFinishClick: () -> Unit,
) {
    // WUDROID_LAYOUT_TEST14_REBUILD1
    var isSizeDragging by remember { mutableStateOf(false) }
    val floatingPanelAlpha by animateFloatAsState(
        targetValue = if (isSizeDragging) 0.22f else 0.98f,
        animationSpec = tween(durationMillis = 150),
        label = "WudroidEditorPanelAlpha",
    )

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
                    .padding(top = 10.dp)
                    .fillMaxWidth(0.58f)
                    .widthIn(min = 310.dp, max = 470.dp)
                    .alpha(floatingPanelAlpha)
                    .background(WudroidDrawerSurface, RoundedCornerShape(22.dp))
                    .padding(horizontal = 14.dp, vertical = 8.dp),
            ) {
                Text(
                    text = "Editar layout",
                    color = WudroidCyan,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold,
                )

                Row(
                    modifier = Modifier.fillMaxWidth().padding(top = 3.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text("Transparência", color = WudroidDrawerText, fontSize = 12.sp, modifier = Modifier.weight(1f))
                    Text("${((alpha / 255f) * 100f).toInt()}%", color = WudroidCyan, fontSize = 11.sp, fontWeight = FontWeight.Bold)
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
                    modifier = Modifier.fillMaxWidth().padding(vertical = 1.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text("Separar", color = WudroidDrawerText, fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
                        Text(
                            text = if (isSeparated) "Peças independentes" else "Grupos unidos",
                            color = if (isSeparated) WudroidCyan else WudroidDrawerMuted,
                            fontSize = 10.sp,
                        )
                    }
                    Switch(
                        checked = isSeparated,
                        onCheckedChange = onSeparatedChange,
                        colors = SwitchDefaults.colors(
                            checkedThumbColor = WudroidCyan,
                            checkedTrackColor = WudroidCyan.copy(alpha = 0.35f),
                            uncheckedThumbColor = WudroidDrawerText,
                            uncheckedTrackColor = WudroidDrawerOutline,
                        ),
                    )
                }

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text("Tamanho", color = WudroidDrawerText, fontSize = 12.sp, modifier = Modifier.weight(1f))
                    Text(
                        if (hasSelection) "${sizePercent.toInt()}%" else "Selecione um botão",
                        color = if (hasSelection) WudroidCyan else WudroidDrawerMuted,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                    )
                }
                Slider(
                    value = sizePercent,
                    onValueChange = {
                        isSizeDragging = true
                        onSizeChange(it.coerceIn(25f, 200f))
                    },
                    onValueChangeFinished = { isSizeDragging = false },
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
                        text = if (isSeparated) {
                            "Toque na peça que deseja mover ou redimensionar."
                        } else {
                            "Toque em um grupo ou botão para mover/redimensionar junto."
                        },
                        color = WudroidDrawerMuted,
                        fontSize = 10.sp,
                    )
                }

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp, Alignment.End),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    TextButton(onClick = onResetClick) {
                        Text("Resetar", color = WudroidDrawerText, fontSize = 11.sp)
                    }
                    Button(onClick = onFinishClick) {
                        Text("Concluir", fontSize = 11.sp)
                    }
                }

                Box(modifier = Modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
                    TextButton(onClick = { onCollapseChange(true) }) {
                        Text("▲", color = WudroidCyan, fontSize = 16.sp, fontWeight = FontWeight.Bold)
                    }
                }
            }
        }

        AnimatedVisibility(
            visible = isCollapsed,
            modifier = Modifier.align(Alignment.TopCenter),
            enter = slideInVertically(animationSpec = tween(210), initialOffsetY = { -it }) + fadeIn(tween(160)),
            exit = slideOutVertically(animationSpec = tween(180), targetOffsetY = { -it }) + fadeOut(tween(120)),
        ) {
            TextButton(
                onClick = { onCollapseChange(false) },
                modifier = Modifier
                    .padding(top = 4.dp)
                    .background(WudroidDrawerSurface, RoundedCornerShape(18.dp)),
            ) {
                Text("▼", color = WudroidCyan, fontSize = 18.sp, fontWeight = FontWeight.Bold)
            }
        }
    }
}
'''
screen, count = replace_function(screen, 'EditInputsLayout', new_editor_fn)
if count != 1:
    raise SystemExit('Layout Test14 Rebuild1: could not replace EditInputsLayout')

# ---------------------------------------------------------------------------
# 3) Input overlay runtime/editor behavior.
# ---------------------------------------------------------------------------
# Listener for independent D-pad rectangles.
listener_anchor = '    var onWudroidSelectionChangedListener: ((Boolean) -> Unit)? = null // WUDROID_GAMEPAD_EDITOR_TEST8_INDIVIDUAL\n'
if listener_anchor not in overlay:
    raise SystemExit('Layout Test14 Rebuild1: selection-listener anchor missing')
overlay = overlay.replace(
    listener_anchor,
    listener_anchor + '    var onWudroidSeparatedDpadFinishedListener: ((Map<String, InputOverlayRect>) -> Unit)? = null // WUDROID_LAYOUT_TEST14_REBUILD1\n',
    1,
)

field_anchor = '    private var wudroidSelectedScale = 1f\n'
if field_anchor not in overlay:
    raise SystemExit('Layout Test14 Rebuild1: selected-scale field anchor missing')
overlay = overlay.replace(
    field_anchor,
    field_anchor +
    '    private var wudroidSelectedOverlayInput: OverlayInput? = null // WUDROID_LAYOUT_TEST14_REBUILD1\n'
    '    private var wudroidSelectedGroup: List<Pair<OverlayInput, Input>> = emptyList()\n'
    '    private var wudroidDragStartX = 0f\n'
    '    private var wudroidDragStartY = 0f\n'
    '    private var wudroidDragStartCenters: List<Pair<Input, Pair<Int, Int>>> = emptyList()\n'
    '    private var wudroidTransientSeparatedDpadRectangles: Map<String, InputOverlayRect>? = null\n',
    1,
)

# Helpers for reference layout + grouping.
rect_region = find_function_region(overlay, 'getBoundingRectangleForInput')
if rect_region is None:
    raise SystemExit('Layout Test14 Rebuild1: getBoundingRectangleForInput missing')
helper_insert = rect_region[0]
helpers = r'''    // WUDROID_LAYOUT_TEST14_REBUILD1
    private fun wudroidCenteredRect(cx: Float, cy: Float, side: Int): Rect {
        val safeSide = side.coerceAtLeast(inputsMinSize)
        val centerX = (width * cx).roundToInt()
        val centerY = (height * cy).roundToInt()
        val left = (centerX - safeSide / 2).coerceIn(0, (width - safeSide).coerceAtLeast(0))
        val top = (centerY - safeSide / 2).coerceIn(0, (height - safeSide).coerceAtLeast(0))
        return Rect(left, top, left + safeSide, top + safeSide)
    }

    private fun wudroidReferenceSide(widthFraction: Float, heightFraction: Float): Int =
        kotlin.math.min(width * widthFraction, height * heightFraction).roundToInt().coerceAtLeast(inputsMinSize)

    private fun wudroidWiimoteReferenceRectangle(input: OverlayInput): Rect? {
        if (nativeControllerType != NativeInput.EmulatedControllerType.WIIMOTE || width <= 0 || height <= 0) return null
        return when (input) {
            is OverlayDpad -> wudroidCenteredRect(0.135f, 0.725f, wudroidReferenceSide(0.197f, 0.351f))
            OverlayButton.PLUS -> wudroidCenteredRect(0.468f, 0.940f, wudroidReferenceSide(0.050f, 0.088f))
            OverlayButton.MINUS -> wudroidCenteredRect(0.534f, 0.940f, wudroidReferenceSide(0.050f, 0.088f))
            OverlayButton.B -> wudroidCenteredRect(0.845f, 0.634f, wudroidReferenceSide(0.074f, 0.132f))
            OverlayButton.ONE -> wudroidCenteredRect(0.764f, 0.777f, wudroidReferenceSide(0.074f, 0.132f))
            OverlayButton.A -> wudroidCenteredRect(0.926f, 0.776f, wudroidReferenceSide(0.074f, 0.132f))
            OverlayButton.TWO -> wudroidCenteredRect(0.845f, 0.910f, wudroidReferenceSide(0.074f, 0.132f))
            else -> null
        }
    }

    private fun wudroidSeparatedDpadRectangle(direction: OverlayDpad): Rect {
        val transient = wudroidTransientSeparatedDpadRectangles?.get(direction.name)
        if (transient != null) return Rect(transient.left, transient.top, transient.right, transient.bottom)

        val saved = settings.wudroidSeparatedDpadRectMap[direction.name]
        if (saved != null) return Rect(saved.left, saved.top, saved.right, saved.bottom)

        val group = wudroidWiimoteReferenceRectangle(direction)
            ?: getDefaultRectangle(OverlayInputConfig.DPAD, width, height, pixelDensity)
        val cellW = (group.right - group.left) / 3
        val cellH = (group.bottom - group.top) / 3
        return when (direction) {
            OverlayDpad.DPAD_UP -> Rect(group.left + cellW, group.top, group.left + cellW * 2, group.top + cellH)
            OverlayDpad.DPAD_DOWN -> Rect(group.left + cellW, group.top + cellH * 2, group.left + cellW * 2, group.bottom)
            OverlayDpad.DPAD_LEFT -> Rect(group.left, group.top + cellH, group.left + cellW, group.top + cellH * 2)
            OverlayDpad.DPAD_RIGHT -> Rect(group.left + cellW * 2, group.top + cellH, group.right, group.top + cellH * 2)
        }
    }

    private fun MutableList<Pair<OverlayInput, Input>>.addWudroidSeparatedDpadButton(
        direction: OverlayDpad,
        text: String,
    ) {
        add(
            direction to RectangleButton(
                TextButtonInnerDrawing(text),
                { onButtonStateChange(direction, it) },
                currentAlpha,
                wudroidSeparatedDpadRectangle(direction),
            )
        )
    }

    private fun wudroidFaceGroup(): Set<OverlayInput> =
        if (nativeControllerType == NativeInput.EmulatedControllerType.WIIMOTE) {
            setOf(OverlayButton.A, OverlayButton.B, OverlayButton.ONE, OverlayButton.TWO)
        } else {
            setOf(OverlayButton.A, OverlayButton.B, OverlayButton.X, OverlayButton.Y)
        }

    private fun wudroidEditorGroupFor(overlayInput: OverlayInput): List<Pair<OverlayInput, Input>> {
        if (settings.wudroidLayoutSeparated) {
            return inputs.filter { it.first == overlayInput }
        }
        val faceGroup = wudroidFaceGroup()
        if (overlayInput in faceGroup) {
            return inputs.filter { it.first in faceGroup }
        }
        return inputs.filter { it.first == overlayInput }
    }

'''
overlay = overlay[:helper_insert] + helpers + overlay[helper_insert:]

new_rect_fn = r'''    private fun getBoundingRectangleForInput(input: OverlayInput): Rect {
        val config = input.toConfig()
        val transient = wudroidTransientRectangles?.get(config)
        if (transient != null) {
            return Rect(transient.left, transient.top, transient.right, transient.bottom)
        }

        val saved = settings.inputOverlayRectMap[config]
        if (saved != null) {
            return Rect(saved.left, saved.top, saved.right, saved.bottom)
        }

        wudroidWiimoteReferenceRectangle(input)?.let { return it }
        return getDefaultRectangle(config, width, height, pixelDensity)
    }
'''
overlay, count = replace_function(overlay, 'getBoundingRectangleForInput', new_rect_fn)
if count != 1:
    raise SystemExit('Layout Test14 Rebuild1: rectangle function replacement failed')

# Replace selection helpers.
new_select = r'''    private fun setWudroidEditorSelection(overlayInput: OverlayInput, input: Input) {
        wudroidSelectedOverlayInput = overlayInput
        wudroidSelectedConfig = overlayInput.toConfig()
        wudroidSelectedInput = input
        wudroidSelectedGroup = wudroidEditorGroupFor(overlayInput)
        wudroidSelectedScale = 1f
        onWudroidSelectionChangedListener?.invoke(true)
        invalidate()
    }
'''
overlay, count = replace_function(overlay, 'setWudroidEditorSelection', new_select)
if count != 1:
    raise SystemExit('Layout Test14 Rebuild1: selection helper replacement failed')

new_clear = r'''    private fun clearWudroidEditorSelection(notify: Boolean = true) {
        wudroidSelectedConfig = null
        wudroidSelectedOverlayInput = null
        wudroidSelectedInput = null
        wudroidSelectedGroup = emptyList()
        wudroidDragStartCenters = emptyList()
        wudroidSelectedScale = 1f
        if (notify) onWudroidSelectionChangedListener?.invoke(false)
        invalidate()
    }
'''
overlay, count = replace_function(overlay, 'clearWudroidEditorSelection', new_clear)
if count != 1:
    raise SystemExit('Layout Test14 Rebuild1: clear-selection helper replacement failed')

new_restore = r'''    private fun restoreWudroidSelectedInput() {
        val selectedOverlay = wudroidSelectedOverlayInput ?: run {
            wudroidSelectedInput = null
            wudroidSelectedGroup = emptyList()
            return
        }
        val selectedPair = inputs.firstOrNull { it.first == selectedOverlay }
        wudroidSelectedInput = selectedPair?.second
        if (selectedPair == null) {
            clearWudroidEditorSelection()
            return
        }
        wudroidSelectedConfig = selectedOverlay.toConfig()
        wudroidSelectedGroup = wudroidEditorGroupFor(selectedOverlay)
    }
'''
overlay, count = replace_function(overlay, 'restoreWudroidSelectedInput', new_restore)
if count != 1:
    raise SystemExit('Layout Test14 Rebuild1: restore-selection helper replacement failed')

# Alpha rebuild must preserve four independent D-pad rectangles.
new_alpha = r'''    fun setWudroidEditorAlpha(alpha: Int?) {
        if (inputMode == InputMode.DEFAULT && alpha == null) {
            wudroidEditorAlphaOverride = null
            return
        }
        if (alpha == null || wudroidEditorAlphaOverride == alpha) return

        wudroidTransientRectangles = inputs
            .filterNot { settings.wudroidLayoutSeparated && it.first is OverlayDpad }
            .associate {
                val rect = it.second.getBoundingRectangle()
                it.first.toConfig() to Rect(rect.left, rect.top, rect.right, rect.bottom)
            }
        wudroidTransientSeparatedDpadRectangles = if (settings.wudroidLayoutSeparated) {
            inputs.filter { it.first is OverlayDpad }.associate {
                it.first.toString() to it.second.getBoundingRectangle()
            }
        } else null

        wudroidEditorAlphaOverride = alpha.coerceIn(0, 255)
        setInputs()
        restoreWudroidSelectedInput()
        wudroidTransientRectangles = null
        wudroidTransientSeparatedDpadRectangles = null
        invalidate()
    }
'''
overlay, count = replace_function(overlay, 'setWudroidEditorAlpha', new_alpha)
if count != 1:
    raise SystemExit('Layout Test14 Rebuild1: alpha function replacement failed')

# Exiting the editor saves normal rectangles plus the four separated D-pad pieces.
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

        val rectangles = settings.inputOverlayRectMap.toMutableMap()
        val separatedDpadRectangles = mutableMapOf<String, InputOverlayRect>()
        for ((overlayInput, input) in inputs) {
            if (settings.wudroidLayoutSeparated && overlayInput is OverlayDpad) {
                separatedDpadRectangles[overlayInput.name] = input.getBoundingRectangle()
            } else {
                rectangles[overlayInput.toConfig()] = input.getBoundingRectangle()
            }
        }
        onEditFinishedListener?.invoke(rectangles)
        if (settings.wudroidLayoutSeparated) {
            onWudroidSeparatedDpadFinishedListener?.invoke(separatedDpadRectangles)
        }
        wudroidEditorAlphaOverride?.let { onEditAlphaFinishedListener?.invoke(it) }
        wudroidEditorAlphaOverride = null
        wudroidEditorScale = 1f
        clearWudroidEditorSelection(notify = false)
    }
'''
overlay, count = replace_function(overlay, 'setInputMode', new_set_mode)
if count != 1:
    raise SystemExit('Layout Test14 Rebuild1: setInputMode replacement failed')

# When Separar is OFF, face buttons are edited as one group; when ON, only the selected piece scales.
new_scale = r'''    fun setWudroidSelectedInputScale(scale: Float) {
        if (inputMode == InputMode.DEFAULT || width <= 0 || height <= 0) return
        val selected = wudroidSelectedInput ?: return
        val group = if (wudroidSelectedGroup.isEmpty()) {
            listOf(wudroidSelectedOverlayInput to selected).filter { it.first != null }.map { it.first!! to it.second }
        } else {
            wudroidSelectedGroup
        }

        val targetScale = scale.coerceIn(0.25f, 2.0f)
        val ratio = targetScale / wudroidSelectedScale
        if (ratio in 0.999f..1.001f) return

        if (group.size == 1) {
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
        } else {
            val rects = group.map { it.second.getBoundingRectangle() }
            val left = rects.minOf { it.left }
            val top = rects.minOf { it.top }
            val right = rects.maxOf { it.right }
            val bottom = rects.maxOf { it.bottom }
            val groupCenterX = (left + right) / 2f
            val groupCenterY = (top + bottom) / 2f

            for ((_, input) in group) {
                val before = input.getBoundingRectangle()
                val beforeWidth = before.right - before.left
                val beforeHeight = before.bottom - before.top
                val beforeCenterX = before.left + beforeWidth / 2f
                val beforeCenterY = before.top + beforeHeight / 2f
                val targetWidth = (beforeWidth * ratio).roundToInt().coerceAtLeast(inputsMinSize)
                val targetHeight = (beforeHeight * ratio).roundToInt().coerceAtLeast(inputsMinSize)
                val targetCenterX = groupCenterX + (beforeCenterX - groupCenterX) * ratio
                val targetCenterY = groupCenterY + (beforeCenterY - groupCenterY) * ratio
                input.resize(
                    diffX = targetWidth - beforeWidth,
                    diffY = targetHeight - beforeHeight,
                    maxWidth = width,
                    maxHeight = height,
                    minWidthHeight = inputsMinSize,
                )
                input.moveInput(targetCenterX.roundToInt(), targetCenterY.roundToInt(), width, height)
            }
        }

        wudroidSelectedScale = targetScale
        invalidate()
    }
'''
overlay, count = replace_function(overlay, 'setWudroidSelectedInputScale', new_scale)
if count != 1:
    raise SystemExit('Layout Test14 Rebuild1: selected-scale replacement failed')

# Move selected face group together when grouped; move only one piece when separated.
new_edit_position = r'''    private fun onEditPosition(event: MotionEvent): Boolean {
        val configuredInput = currentConfiguredInput

        if (event.actionMasked == MotionEvent.ACTION_DOWN) {
            if (configuredInput != null) return false

            val x = event.x
            val y = event.y
            for ((overlayInput, input) in inputs.asReversed()) {
                if (input.isInside(x, y)) {
                    setWudroidEditorSelection(overlayInput, input)
                    currentConfiguredInput = input
                    wudroidDragStartX = event.x
                    wudroidDragStartY = event.y
                    wudroidDragStartCenters = wudroidSelectedGroup.map { (_, member) ->
                        val rect = member.getBoundingRectangle()
                        member to Pair((rect.left + rect.right) / 2, (rect.top + rect.bottom) / 2)
                    }
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
            wudroidDragStartCenters = emptyList()
            return true
        }

        if (event.actionMasked == MotionEvent.ACTION_MOVE) {
            val dx = event.x - wudroidDragStartX
            val dy = event.y - wudroidDragStartY
            if (wudroidDragStartCenters.isEmpty()) {
                configuredInput.moveInput(event.x.toInt(), event.y.toInt(), width, height)
            } else {
                for ((member, center) in wudroidDragStartCenters) {
                    member.moveInput(
                        (center.first + dx).roundToInt(),
                        (center.second + dy).roundToInt(),
                        width,
                        height,
                    )
                }
            }
            return true
        }

        return false
    }
'''
overlay, count = replace_function(overlay, 'onEditPosition', new_edit_position)
if count != 1:
    raise SystemExit('Layout Test14 Rebuild1: editor-position replacement failed')

# New default Wii Remote layout from the user's reference; D-pad splits into four editable pieces.
new_set_inputs = r'''    private fun setInputs() {
        if (isControllerDisabled(controllerIndex)) {
            inputs = mutableListOf()
            return
        }
        nativeControllerType = getControllerType(controllerIndex)
        overlyButtonToNativeButton = when (nativeControllerType) {
            NativeInput.EmulatedControllerType.VPAD -> ::overlayButtonToVPADButton
            NativeInput.EmulatedControllerType.CLASSIC -> ::overlayButtonToClassicButton
            NativeInput.EmulatedControllerType.PRO -> ::overlayButtonToProButton
            NativeInput.EmulatedControllerType.WIIMOTE -> ::overlayButtonToWiimoteButton
            else -> { _ -> -1 }
        }
        onJoystickChange = when (nativeControllerType) {
            NativeInput.EmulatedControllerType.VPAD -> ::onVPADJoystickStateChange
            NativeInput.EmulatedControllerType.PRO -> ::onProJoystickStateChange
            NativeInput.EmulatedControllerType.CLASSIC -> ::onClassicJoystickStateChange
            NativeInput.EmulatedControllerType.WIIMOTE -> ::onWiimoteJoystickStateChange
            else -> { _, _, _, _, _ -> }
        }
        inputs = mutableListOf<Pair<OverlayInput, Input>>().apply {
            addRoundButton(OverlayButton.MINUS, "-")
            addRoundButton(OverlayButton.PLUS, "+")

            if (settings.wudroidLayoutSeparated) {
                addWudroidSeparatedDpadButton(OverlayDpad.DPAD_UP, "▲")
                addWudroidSeparatedDpadButton(OverlayDpad.DPAD_DOWN, "▼")
                addWudroidSeparatedDpadButton(OverlayDpad.DPAD_LEFT, "◀")
                addWudroidSeparatedDpadButton(OverlayDpad.DPAD_RIGHT, "▶")
            } else {
                addDpad()
            }

            addRoundButton(OverlayButton.A)
            addRoundButton(OverlayButton.B)
            addJoystick(OverlayJoystick.RIGHT)
            if (nativeControllerType != NativeInput.EmulatedControllerType.WIIMOTE) {
                addRoundButton(OverlayButton.X)
                addRoundButton(OverlayButton.Y)
                addRectangleButton(OverlayButton.ZL)
                addRectangleButton(OverlayButton.ZR)
                addRectangleButton(OverlayButton.L)
                addRectangleButton(OverlayButton.R)
                addJoystick(OverlayJoystick.LEFT)
            }
            if (nativeControllerType == NativeInput.EmulatedControllerType.WIIMOTE) {
                addRoundButton(OverlayButton.ONE, "1")
                addRoundButton(OverlayButton.TWO, "2")
                addRoundButton(OverlayButton.C)
                addRectangleButton(OverlayButton.Z)
                addRoundButton(OverlayButton.HOME, HomeButtonInnerDrawing())
            }
            if (nativeControllerType != NativeInput.EmulatedControllerType.CLASSIC && nativeControllerType != NativeInput.EmulatedControllerType.WIIMOTE) {
                addRoundButton(OverlayButton.L_STICK_CLICK, "L3")
                addRoundButton(OverlayButton.R_STICK_CLICK, "R3")
            }
            if (nativeControllerType == NativeInput.EmulatedControllerType.VPAD) {
                addRoundButton(OverlayButton.BLOW_MIC, BlowButtonInnerDrawing())
            }

            removeAll { (overlayInput, _) -> !isInputVisible(overlayInput) }
        }
    }
'''
overlay, count = replace_function(overlay, 'setInputs', new_set_inputs)
if count != 1:
    raise SystemExit('Layout Test14 Rebuild1: setInputs replacement failed')

new_visibility = r'''    private fun isInputVisible(overlayInput: OverlayInput): Boolean {
        settings.inputVisibilityMap[overlayInput.toConfig()]?.let { return it }
        if (nativeControllerType == NativeInput.EmulatedControllerType.WIIMOTE) {
            // The new default Wii Remote layout matches the supplied reference image.
            // Extended Nunchuk/Home controls stay available if explicitly enabled later.
            if (overlayInput == OverlayButton.C ||
                overlayInput == OverlayButton.Z ||
                overlayInput == OverlayButton.HOME ||
                overlayInput == OverlayJoystick.RIGHT
            ) return false
        }
        return true
    }
'''
overlay, count = replace_function(overlay, 'isInputVisible', new_visibility)
if count != 1:
    raise SystemExit('Layout Test14 Rebuild1: visibility function replacement failed')

# Highlight all members of a grouped face cluster; one piece only when separated.
new_draw = r'''    override fun draw(canvas: Canvas) {
        super.draw(canvas)

        val selectedInputs = wudroidSelectedGroup.map { it.second }.toSet()
        for ((_, input) in inputs) {
            input.draw(canvas)
            if (inputMode != InputMode.DEFAULT && input in selectedInputs) {
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
    raise SystemExit('Layout Test14 Rebuild1: draw replacement failed')

# Extend Compose bridge with separated-D-pad persistence callback.
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
    onSeparatedDpadEditFinished: (Map<String, InputOverlayRect>) -> Unit = {},
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
                onWudroidSeparatedDpadFinishedListener = onSeparatedDpadEditFinished
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
            view.onWudroidSeparatedDpadFinishedListener = onSeparatedDpadEditFinished
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
    raise SystemExit('Layout Test14 Rebuild1: InputOverlaySurface bridge replacement failed')

# ---------------------------------------------------------------------------
# Write + verification.
# ---------------------------------------------------------------------------
settings_path.write_text(settings)
viewmodel_path.write_text(viewmodel)
screen_path.write_text(screen)
overlay_path.write_text(overlay)

checks = {
    settings_path: [
        marker,
        'wudroidLayoutSeparated: Boolean = false',
        'wudroidSeparatedDpadRectMap: Map<String, InputOverlayRect>',
    ],
    viewmodel_path: [
        'fun saveWudroidLayoutSeparated',
        'fun saveWudroidSeparatedDpadRectangles',
        'wudroidSeparatedDpadRectMap = emptyMap()',
    ],
    screen_path: [
        marker,
        'text = "Editar layout"',
        'Text("Separar"',
        'checked = isSeparated',
        'onSeparatedChange = { viewModel.saveWudroidLayoutSeparated(it) }',
        'onSeparatedDpadEditFinished =',
        'Text("Resetar"',
    ],
    overlay_path: [
        marker,
        'wudroidWiimoteReferenceRectangle',
        'addWudroidSeparatedDpadButton',
        'settings.wudroidLayoutSeparated',
        'wudroidSelectedGroup',
        'onWudroidSeparatedDpadFinishedListener',
        'OverlayButton.ONE, "1"',
        'OverlayButton.TWO, "2"',
    ],
}
for path, needles in checks.items():
    text = path.read_text()
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise SystemExit(f'Layout Test14 Rebuild1 verification failed in {path}: {missing}')

print('Wudroid Layout Test14 Rebuild1 applied')
print('- Wii Remote default overlay replaced by the supplied reference layout')
print('- Editar layout naming applied without replacing MainActivity/workflow')
print('- Separar is a persistent switch')
print('- Separar ON: D-pad directions and face buttons can be edited independently')
print('- Separar OFF: D-pad is grouped; face-button cluster moves/scales together')
print('- Reset clears positions/sizes but intentionally keeps Separar state')
print('- Concluir saves the exact resulting layout')
