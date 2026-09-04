#!/usr/bin/env python3
from pathlib import Path
import re

screen_path = Path('cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationScreen.kt')
viewmodel_path = Path('cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationViewModel.kt')
overlay_path = Path('cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/inputoverlay/InputOverlaySurfaceView.kt')
settings_path = Path('cemu-engine/src/android/app/src/main/java/info/cemu/cemu/common/settings/Settings.kt')

for p in (screen_path, viewmodel_path, overlay_path, settings_path):
    if not p.exists():
        raise SystemExit(f'Layout Test14 Rebuild2: required source not found: {p}')

screen = screen_path.read_text()
viewmodel = viewmodel_path.read_text()
overlay = overlay_path.read_text()
settings = settings_path.read_text()
marker = 'WUDROID_LAYOUT_TEST14_REBUILD2'

if marker in screen and marker in overlay and marker in settings:
    print('Wudroid Layout Test14 Rebuild2 already applied')
    raise SystemExit(0)

if 'WUDROID_LAYOUT_TEST14_REBUILD1' not in screen or 'WUDROID_LAYOUT_TEST14_REBUILD1' not in overlay:
    raise SystemExit('Layout Test14 Rebuild2 requires Rebuild1 to run first')


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

# ---------------------------------------------------------------------------
# 1) Give Layout14's Wii Remote its OWN rectangle map.
#    This intentionally ignores old Wii/Nunchuk rectangles already saved in
#    inputOverlayRectMap, which is why Rebuild1 visually stayed on the old UI.
# ---------------------------------------------------------------------------
settings_anchor = '    val wudroidSeparatedDpadRectMap: Map<String, InputOverlayRect> = emptyMap(),\n'
if settings_anchor not in settings:
    raise SystemExit('Rebuild2: Rebuild1 settings anchor missing')
settings = settings.replace(
    settings_anchor,
    settings_anchor +
    '    val wudroidLayout14WiimoteRectMap: Map<OverlayInputConfig, InputOverlayRect> = emptyMap(), // WUDROID_LAYOUT_TEST14_REBUILD2\n',
    1,
)

reset_anchor = '''                        wudroidSeparatedDpadRectMap = emptyMap(),\n                    )'''
if reset_anchor not in viewmodel:
    raise SystemExit('Rebuild2: reset map anchor missing')
viewmodel = viewmodel.replace(
    reset_anchor,
    '''                        wudroidSeparatedDpadRectMap = emptyMap(),\n                        wudroidLayout14WiimoteRectMap = emptyMap(),\n                    )''',
    1,
)

vm_anchor = '    fun saveWudroidSeparatedDpadRectangles(rectangles: Map<String, InputOverlayRect>) {'
region = find_function_region(viewmodel, 'saveWudroidSeparatedDpadRectangles')
if region is None:
    raise SystemExit('Rebuild2: separated D-pad save function missing')
vm_method = r'''
    // WUDROID_LAYOUT_TEST14_REBUILD2
    fun saveWudroidLayout14WiimoteRectangles(rectangles: Map<OverlayInputConfig, InputOverlayRect>) {
        viewModelScope.launch {
            dataStore.updateData {
                val overlaySettings =
                    it.inputOverlaySettings.copy(wudroidLayout14WiimoteRectMap = rectangles)
                it.copy(inputOverlaySettings = overlaySettings)
            }
        }
    }
'''
viewmodel = viewmodel[:region[1]] + vm_method + viewmodel[region[1]:]

# ---------------------------------------------------------------------------
# 2) Make Separar immediate in the editor instead of waiting for DataStore.
#    Save the toggle when Concluir is pressed. This also avoids rebuilding the
#    controls mid-edit and losing the selected control.
# ---------------------------------------------------------------------------
state_anchor = '    var wudroidEditorPanelCollapsed by rememberSaveable { mutableStateOf(false) }\n'
if state_anchor not in screen:
    raise SystemExit('Rebuild2: editor collapsed-state anchor missing')
screen = screen.replace(
    state_anchor,
    state_anchor + '    var wudroidEditorSeparated by rememberSaveable { mutableStateOf(false) } // WUDROID_LAYOUT_TEST14_REBUILD2\n',
    1,
)

open_anchor = '''                            wudroidEditorHasSelection = false\n                            wudroidEditorPanelCollapsed = false\n                            inputOverlayInputMode = EDIT_POSITION'''
if open_anchor not in screen:
    raise SystemExit('Rebuild2: editor-open anchor missing')
screen = screen.replace(
    open_anchor,
    '''                            wudroidEditorHasSelection = false\n                            wudroidEditorPanelCollapsed = false\n                            wudroidEditorSeparated = inputOverlaySettings.wudroidLayoutSeparated\n                            inputOverlayInputMode = EDIT_POSITION''',
    1,
)

if '                isSeparated = inputOverlaySettings.wudroidLayoutSeparated,\n' not in screen:
    raise SystemExit('Rebuild2: editor isSeparated call anchor missing')
screen = screen.replace(
    '                isSeparated = inputOverlaySettings.wudroidLayoutSeparated,\n',
    '                isSeparated = wudroidEditorSeparated,\n',
    1,
)

if '                onSeparatedChange = { viewModel.saveWudroidLayoutSeparated(it) },\n' not in screen:
    raise SystemExit('Rebuild2: editor separated callback anchor missing')
screen = screen.replace(
    '                onSeparatedChange = { viewModel.saveWudroidLayoutSeparated(it) },\n',
    '                onSeparatedChange = { wudroidEditorSeparated = it },\n',
    1,
)

finish_anchor = '''                    wudroidEditorHasSelection = false\n                    wudroidEditorPanelCollapsed = false\n                    inputOverlayInputMode = DEFAULT'''
if finish_anchor not in screen:
    raise SystemExit('Rebuild2: editor finish anchor missing')
screen = screen.replace(
    finish_anchor,
    '''                    viewModel.saveWudroidLayoutSeparated(wudroidEditorSeparated)\n                    wudroidEditorHasSelection = false\n                    wudroidEditorPanelCollapsed = false\n                    inputOverlayInputMode = DEFAULT''',
    1,
)

surface_scale_anchor = '            editorSelectedScale = if (inputOverlayInputMode == DEFAULT || !wudroidEditorHasSelection) 1f else wudroidEditorSizePercent / 100f,\n'
if surface_scale_anchor not in screen:
    raise SystemExit('Rebuild2: surface selected-scale anchor missing')
screen = screen.replace(
    surface_scale_anchor,
    surface_scale_anchor + '            editorSeparated = if (inputOverlayInputMode == DEFAULT) null else wudroidEditorSeparated,\n',
    1,
)

surface_cb_anchor = '            onSeparatedDpadEditFinished = { viewModel.saveWudroidSeparatedDpadRectangles(it) },\n'
if surface_cb_anchor not in screen:
    raise SystemExit('Rebuild2: separated D-pad callback anchor missing')
screen = screen.replace(
    surface_cb_anchor,
    surface_cb_anchor + '            onWiimoteLayoutEditFinished = { viewModel.saveWudroidLayout14WiimoteRectangles(it) },\n',
    1,
)

# ---------------------------------------------------------------------------
# 3) Runtime/editor: exact Wii Remote default, live Separar, and restore the
#    original Test8 individual-selection behavior for GamePad/Pro/Classic.
# ---------------------------------------------------------------------------
listener_anchor = '    var onWudroidSeparatedDpadFinishedListener: ((Map<String, InputOverlayRect>) -> Unit)? = null // WUDROID_LAYOUT_TEST14_REBUILD1\n'
if listener_anchor not in overlay:
    raise SystemExit('Rebuild2: separated D-pad listener anchor missing')
overlay = overlay.replace(
    listener_anchor,
    listener_anchor + '    var onWudroidWiimoteLayoutFinishedListener: ((Map<OverlayInputConfig, InputOverlayRect>) -> Unit)? = null // WUDROID_LAYOUT_TEST14_REBUILD2\n',
    1,
)

field_anchor = '    private var wudroidTransientSeparatedDpadRectangles: Map<String, InputOverlayRect>? = null\n'
if field_anchor not in overlay:
    raise SystemExit('Rebuild2: transient separated D-pad field anchor missing')
overlay = overlay.replace(
    field_anchor,
    field_anchor + '    private var wudroidEditorSeparatedOverride: Boolean? = null // WUDROID_LAYOUT_TEST14_REBUILD2\n',
    1,
)

center_region = find_function_region(overlay, 'wudroidCenteredRect')
if center_region is None:
    raise SystemExit('Rebuild2: reference layout helper anchor missing')
helper_insert = center_region[0]
helpers = r'''    // WUDROID_LAYOUT_TEST14_REBUILD2
    private fun wudroidIsSeparated(): Boolean =
        wudroidEditorSeparatedOverride ?: settings.wudroidLayoutSeparated

    private fun wudroidIsLayout14WiimoteInput(input: OverlayInput): Boolean =
        input is OverlayDpad ||
            input == OverlayButton.A ||
            input == OverlayButton.B ||
            input == OverlayButton.ONE ||
            input == OverlayButton.TWO ||
            input == OverlayButton.PLUS ||
            input == OverlayButton.MINUS

'''
overlay = overlay[:helper_insert] + helpers + overlay[helper_insert:]

new_sep_dpad_rect = r'''    private fun wudroidSeparatedDpadRectangle(direction: OverlayDpad): Rect {
        val transient = wudroidTransientSeparatedDpadRectangles?.get(direction.name)
        if (transient != null) return Rect(transient.left, transient.top, transient.right, transient.bottom)

        val saved = settings.wudroidSeparatedDpadRectMap[direction.name]
        if (saved != null) return Rect(saved.left, saved.top, saved.right, saved.bottom)

        val savedGroup = settings.wudroidLayout14WiimoteRectMap[OverlayInputConfig.DPAD]
        val group = if (savedGroup != null) {
            Rect(savedGroup.left, savedGroup.top, savedGroup.right, savedGroup.bottom)
        } else {
            wudroidWiimoteReferenceRectangle(direction)
                ?: getDefaultRectangle(OverlayInputConfig.DPAD, width, height, pixelDensity)
        }
        val cellW = (group.right - group.left) / 3
        val cellH = (group.bottom - group.top) / 3
        return when (direction) {
            OverlayDpad.DPAD_UP -> Rect(group.left + cellW, group.top, group.left + cellW * 2, group.top + cellH)
            OverlayDpad.DPAD_DOWN -> Rect(group.left + cellW, group.top + cellH * 2, group.left + cellW * 2, group.bottom)
            OverlayDpad.DPAD_LEFT -> Rect(group.left, group.top + cellH, group.left + cellW, group.top + cellH * 2)
            OverlayDpad.DPAD_RIGHT -> Rect(group.left + cellW * 2, group.top + cellH, group.right, group.top + cellH * 2)
        }
    }
'''
overlay, count = replace_function(overlay, 'wudroidSeparatedDpadRectangle', new_sep_dpad_rect)
if count != 1:
    raise SystemExit('Rebuild2: separated D-pad rectangle replacement failed')

new_group = r'''    private fun wudroidEditorGroupFor(overlayInput: OverlayInput): List<Pair<OverlayInput, Input>> {
        // Keep the proven Test8 behavior on GamePad/Pro/Classic: one selected
        // control means one independently resizable control.
        if (nativeControllerType != NativeInput.EmulatedControllerType.WIIMOTE) {
            return inputs.filter { it.first == overlayInput }
        }
        if (wudroidIsSeparated()) {
            return inputs.filter { it.first == overlayInput }
        }
        val faceGroup = wudroidFaceGroup()
        if (overlayInput in faceGroup) {
            return inputs.filter { it.first in faceGroup }
        }
        return inputs.filter { it.first == overlayInput }
    }
'''
overlay, count = replace_function(overlay, 'wudroidEditorGroupFor', new_group)
if count != 1:
    raise SystemExit('Rebuild2: editor-group replacement failed')

new_rect = r'''    private fun getBoundingRectangleForInput(input: OverlayInput): Rect {
        val config = input.toConfig()
        val transient = wudroidTransientRectangles?.get(config)
        if (transient != null) {
            return Rect(transient.left, transient.top, transient.right, transient.bottom)
        }

        if (nativeControllerType == NativeInput.EmulatedControllerType.WIIMOTE && wudroidIsLayout14WiimoteInput(input)) {
            val saved = settings.wudroidLayout14WiimoteRectMap[config]
            if (saved != null) {
                return Rect(saved.left, saved.top, saved.right, saved.bottom)
            }
            wudroidWiimoteReferenceRectangle(input)?.let { return it }
        }

        val saved = settings.inputOverlayRectMap[config]
        if (saved != null) {
            return Rect(saved.left, saved.top, saved.right, saved.bottom)
        }
        return getDefaultRectangle(config, width, height, pixelDensity)
    }
'''
overlay, count = replace_function(overlay, 'getBoundingRectangleForInput', new_rect)
if count != 1:
    raise SystemExit('Rebuild2: bounding rectangle replacement failed')

new_alpha = r'''    fun setWudroidEditorAlpha(alpha: Int?) {
        if (inputMode == InputMode.DEFAULT && alpha == null) {
            wudroidEditorAlphaOverride = null
            return
        }
        if (alpha == null || wudroidEditorAlphaOverride == alpha) return

        wudroidTransientRectangles = inputs
            .filterNot { nativeControllerType == NativeInput.EmulatedControllerType.WIIMOTE && wudroidIsSeparated() && it.first is OverlayDpad }
            .associate {
                val rect = it.second.getBoundingRectangle()
                it.first.toConfig() to Rect(rect.left, rect.top, rect.right, rect.bottom)
            }
        wudroidTransientSeparatedDpadRectangles = if (
            nativeControllerType == NativeInput.EmulatedControllerType.WIIMOTE && wudroidIsSeparated()
        ) {
            inputs.filter { it.first is OverlayDpad }.associate {
                (it.first as OverlayDpad).name to it.second.getBoundingRectangle()
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
    raise SystemExit('Rebuild2: alpha replacement failed')

# Insert immediate separation preview API directly after alpha.
alpha_region = find_function_region(overlay, 'setWudroidEditorAlpha')
if alpha_region is None:
    raise SystemExit('Rebuild2: alpha function missing after replacement')
separate_api = r'''
    fun setWudroidEditorSeparated(separated: Boolean?) {
        if (inputMode == InputMode.DEFAULT) {
            wudroidEditorSeparatedOverride = null
            return
        }
        val target = separated ?: settings.wudroidLayoutSeparated
        val current = wudroidIsSeparated()
        if (current == target && wudroidEditorSeparatedOverride == target) return

        val transientNormal = mutableMapOf<OverlayInputConfig, Rect>()
        for ((overlayInput, input) in inputs) {
            if (!(nativeControllerType == NativeInput.EmulatedControllerType.WIIMOTE && current && overlayInput is OverlayDpad)) {
                val rect = input.getBoundingRectangle()
                transientNormal[overlayInput.toConfig()] = Rect(rect.left, rect.top, rect.right, rect.bottom)
            }
        }

        var transientSeparated: Map<String, InputOverlayRect>? = null
        if (nativeControllerType == NativeInput.EmulatedControllerType.WIIMOTE && !current && target) {
            val grouped = inputs.firstOrNull { it.first is OverlayDpad }?.second?.getBoundingRectangle()
            if (grouped != null) {
                val cellW = (grouped.right - grouped.left) / 3
                val cellH = (grouped.bottom - grouped.top) / 3
                transientSeparated = mapOf(
                    OverlayDpad.DPAD_UP.name to InputOverlayRect(grouped.left + cellW, grouped.top, grouped.left + cellW * 2, grouped.top + cellH),
                    OverlayDpad.DPAD_DOWN.name to InputOverlayRect(grouped.left + cellW, grouped.top + cellH * 2, grouped.left + cellW * 2, grouped.bottom),
                    OverlayDpad.DPAD_LEFT.name to InputOverlayRect(grouped.left, grouped.top + cellH, grouped.left + cellW, grouped.top + cellH * 2),
                    OverlayDpad.DPAD_RIGHT.name to InputOverlayRect(grouped.left + cellW * 2, grouped.top + cellH, grouped.right, grouped.top + cellH * 2),
                )
                transientNormal.remove(OverlayInputConfig.DPAD)
            }
        } else if (nativeControllerType == NativeInput.EmulatedControllerType.WIIMOTE && current && !target) {
            val dpadRects = inputs.filter { it.first is OverlayDpad }.map { it.second.getBoundingRectangle() }
            if (dpadRects.isNotEmpty()) {
                transientNormal[OverlayInputConfig.DPAD] = Rect(
                    dpadRects.minOf { it.left },
                    dpadRects.minOf { it.top },
                    dpadRects.maxOf { it.right },
                    dpadRects.maxOf { it.bottom },
                )
            }
        }

        wudroidTransientRectangles = transientNormal
        wudroidTransientSeparatedDpadRectangles = transientSeparated
        wudroidEditorSeparatedOverride = target
        setInputs()
        clearWudroidEditorSelection()
        wudroidTransientRectangles = null
        wudroidTransientSeparatedDpadRectangles = null
        invalidate()
    }
'''
overlay = overlay[:alpha_region[1]] + separate_api + overlay[alpha_region[1]:]

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

        if (nativeControllerType == NativeInput.EmulatedControllerType.WIIMOTE) {
            val wiimoteRectangles = mutableMapOf<OverlayInputConfig, InputOverlayRect>()
            val separatedDpadRectangles = mutableMapOf<String, InputOverlayRect>()
            for ((overlayInput, input) in inputs) {
                if (wudroidIsSeparated() && overlayInput is OverlayDpad) {
                    separatedDpadRectangles[overlayInput.name] = input.getBoundingRectangle()
                } else if (wudroidIsLayout14WiimoteInput(overlayInput)) {
                    wiimoteRectangles[overlayInput.toConfig()] = input.getBoundingRectangle()
                }
            }
            onWudroidWiimoteLayoutFinishedListener?.invoke(wiimoteRectangles)
            if (wudroidIsSeparated()) {
                onWudroidSeparatedDpadFinishedListener?.invoke(separatedDpadRectangles)
            }
        } else {
            val rectangles = inputs.associate { it.first.toConfig() to it.second.getBoundingRectangle() }
            onEditFinishedListener?.invoke(rectangles)
        }

        wudroidEditorAlphaOverride?.let { onEditAlphaFinishedListener?.invoke(it) }
        wudroidEditorAlphaOverride = null
        wudroidEditorScale = 1f
        clearWudroidEditorSelection(notify = false)
        wudroidEditorSeparatedOverride = null
    }
'''
overlay, count = replace_function(overlay, 'setInputMode', new_set_mode)
if count != 1:
    raise SystemExit('Rebuild2: setInputMode replacement failed')

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

            if (nativeControllerType == NativeInput.EmulatedControllerType.WIIMOTE && wudroidIsSeparated()) {
                addWudroidSeparatedDpadButton(OverlayDpad.DPAD_UP, "▲")
                addWudroidSeparatedDpadButton(OverlayDpad.DPAD_DOWN, "▼")
                addWudroidSeparatedDpadButton(OverlayDpad.DPAD_LEFT, "◀")
                addWudroidSeparatedDpadButton(OverlayDpad.DPAD_RIGHT, "▶")
            } else {
                addDpad()
            }

            addRoundButton(OverlayButton.A)
            addRoundButton(OverlayButton.B)

            if (nativeControllerType != NativeInput.EmulatedControllerType.WIIMOTE) {
                addJoystick(OverlayJoystick.RIGHT)
                addRoundButton(OverlayButton.X)
                addRoundButton(OverlayButton.Y)
                addRectangleButton(OverlayButton.ZL)
                addRectangleButton(OverlayButton.ZR)
                addRectangleButton(OverlayButton.L)
                addRectangleButton(OverlayButton.R)
                addJoystick(OverlayJoystick.LEFT)
            } else {
                // Exact Layout14 Wii Remote requested by the user: no Nunchuk
                // stick/C/Z/Home on the default overlay.
                addRoundButton(OverlayButton.ONE, "1")
                addRoundButton(OverlayButton.TWO, "2")
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
    raise SystemExit('Rebuild2: setInputs replacement failed')

new_visibility = r'''    private fun isInputVisible(overlayInput: OverlayInput): Boolean {
        if (nativeControllerType == NativeInput.EmulatedControllerType.WIIMOTE) {
            // Force the supplied Layout14 Wii Remote set, so stale Nunchuk
            // visibility preferences from older builds cannot bring C/Z/stick back.
            return wudroidIsLayout14WiimoteInput(overlayInput)
        }
        settings.inputVisibilityMap[overlayInput.toConfig()]?.let { return it }
        return true
    }
'''
overlay, count = replace_function(overlay, 'isInputVisible', new_visibility)
if count != 1:
    raise SystemExit('Rebuild2: visibility replacement failed')

new_surface = r'''@Composable
fun InputOverlaySurface(
    isVisible: Boolean,
    inputOverlaySettings: InputOverlaySettings,
    inputMode: InputOverlaySurfaceView.InputMode,
    editorAlpha: Int? = null,
    editorScale: Float = 1f,
    editorSelectedScale: Float = 1f,
    editorSeparated: Boolean? = null,
    onEditFinished: (Map<OverlayInputConfig, InputOverlayRect>) -> Unit,
    onEditAlphaFinished: (Int) -> Unit = {},
    onEditorSelectionChanged: (Boolean) -> Unit = {},
    onSeparatedDpadEditFinished: (Map<String, InputOverlayRect>) -> Unit = {},
    onWiimoteLayoutEditFinished: (Map<OverlayInputConfig, InputOverlayRect>) -> Unit = {},
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
                onWudroidWiimoteLayoutFinishedListener = onWiimoteLayoutEditFinished
                setInputMode(inputMode)
                setWudroidEditorSeparated(editorSeparated)
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
            view.onWudroidWiimoteLayoutFinishedListener = onWiimoteLayoutEditFinished
            // Important order: on exit, setInputMode(DEFAULT) saves using the
            // live Separar override before the override is cleared below.
            view.setInputMode(inputMode)
            view.setWudroidEditorSeparated(editorSeparated)
            view.setWudroidEditorAlpha(editorAlpha)
            view.setWudroidEditorScale(editorScale)
            view.setWudroidSelectedInputScale(editorSelectedScale)
        }
    )
}
'''
overlay, count = replace_function(overlay, 'InputOverlaySurface', new_surface)
if count != 1:
    raise SystemExit('Rebuild2: InputOverlaySurface replacement failed')

# ---------------------------------------------------------------------------
# Write + verify.
# ---------------------------------------------------------------------------
settings_path.write_text(settings)
viewmodel_path.write_text(viewmodel)
screen_path.write_text(screen)
overlay_path.write_text(overlay)

checks = {
    settings_path: [marker, 'wudroidLayout14WiimoteRectMap'],
    viewmodel_path: ['saveWudroidLayout14WiimoteRectangles', 'wudroidLayout14WiimoteRectMap = emptyMap()'],
    screen_path: [marker, 'wudroidEditorSeparated', 'editorSeparated =', 'onWiimoteLayoutEditFinished ='],
    overlay_path: [
        marker,
        'wudroidEditorSeparatedOverride',
        'fun setWudroidEditorSeparated',
        'wudroidLayout14WiimoteRectMap',
        'onWudroidWiimoteLayoutFinishedListener',
        'nativeControllerType != NativeInput.EmulatedControllerType.WIIMOTE',
        'return wudroidIsLayout14WiimoteInput(overlayInput)',
    ],
}
for path, needles in checks.items():
    text = path.read_text()
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise SystemExit(f'Layout Test14 Rebuild2 verification failed in {path}: {missing}')

print('Wudroid Layout Test14 Rebuild2 applied')
print('- old Wii/Nunchuk saved rectangles no longer override the new Layout14 Wii Remote')
print('- exact Wii Remote default now uses D-pad +/− + B/1/A/2 only')
print('- Separar updates immediately while the editor is open and is saved on Concluir')
print('- Reset keeps Separar state but clears Layout14 geometry')
print('- GamePad/Pro/Classic selection + individual resize behavior restored to Test8 semantics')
