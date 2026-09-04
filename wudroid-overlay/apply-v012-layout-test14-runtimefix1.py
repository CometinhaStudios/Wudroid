#!/usr/bin/env python3
from pathlib import Path
import re

screen_path = Path("cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationScreen.kt")
local_overlay_path = Path("cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/WudroidLocalControllerOverlay.kt")

for p in (screen_path, local_overlay_path):
    if not p.exists():
        raise SystemExit(f"Layout14 RuntimeFix1: required source missing: {p}")

screen = screen_path.read_text()
local_overlay = local_overlay_path.read_text()
marker = "WUDROID_LAYOUT14_RUNTIMEFIX1"

if marker not in local_overlay:
    raise SystemExit("Layout14 RuntimeFix1: new WudroidLocalControllerOverlay.kt was not copied")

if marker in screen:
    print("Wudroid Layout14 RuntimeFix1 already applied")
    raise SystemExit(0)

# Rebuild2 provides the editor-side Separar state. RuntimeFix1 bridges the
# *actual* Test19 VPAD/WIIMOTE overlay to that editor state.
state_anchor = (
    "    var wudroidEditorSeparated by rememberSaveable { mutableStateOf(false) } "
    "// WUDROID_LAYOUT_TEST14_REBUILD2\n"
)
if state_anchor not in screen:
    raise SystemExit("Layout14 RuntimeFix1: Rebuild2 editor state anchor missing")
screen = screen.replace(
    state_anchor,
    state_anchor
    + "    var wudroidLocalOverlayResetToken by rememberSaveable { mutableStateOf(0) } // WUDROID_LAYOUT14_RUNTIMEFIX1\n",
    1,
)

# Replace the Local Multiplayer Test19 call, which is the path actually used by
# VPAD and WIIMOTE. The old Layout14 patches changed InputOverlaySurfaceView,
# but Test19 bypasses that view for these controller types.
call_re = re.compile(
    r'''WudroidLocalControllerOverlay\(\n\s*isVisible\s*=\s*isInputOverlayVisible,\n\s*controllerType\s*=\s*wudroidPlayer1ControllerType,\n\s*controllerIndex\s*=\s*0,\n\s*editing\s*=\s*inputOverlayInputMode\s*!=\s*DEFAULT,\n\s*\)'''
)
new_call = '''WudroidLocalControllerOverlay(
                isVisible = isInputOverlayVisible,
                controllerType = wudroidPlayer1ControllerType,
                controllerIndex = 0,
                editing = inputOverlayInputMode != DEFAULT,
                editorSizePercent = if (inputOverlayInputMode == DEFAULT || !wudroidEditorHasSelection) 100f else wudroidEditorSizePercent,
                separated = wudroidEditorSeparated,
                resetToken = wudroidLocalOverlayResetToken,
                overlayAlpha = (if (inputOverlayInputMode == DEFAULT) inputOverlaySettings.alpha.toFloat() else wudroidEditorAlpha).coerceIn(0f, 255f) / 255f,
                onSelectionChanged = { selected ->
                    wudroidEditorHasSelection = selected
                    wudroidEditorSizePercent = 100f
                },
            ) // WUDROID_LAYOUT14_RUNTIMEFIX1'''
screen, count = call_re.subn(new_call, screen, count=1)
if count != 1:
    raise SystemExit("Layout14 RuntimeFix1: Test19 LocalControllerOverlay call not found")

# Reset must clear the SharedPreferences used by the real Test19 overlay while
# keeping the Separar switch untouched, exactly as requested by the user.
reset_re = re.compile(
    r'''(onResetClick\s*=\s*\{\n\s*wudroidEditorAlpha\s*=\s*128f\n\s*wudroidEditorSizePercent\s*=\s*100f\n)(\s*viewModel\.resetInputOverlayLayout\(\))'''
)
screen, count = reset_re.subn(
    r'''\1                    wudroidLocalOverlayResetToken += 1
\2''',
    screen,
    count=1,
)
if count != 1:
    raise SystemExit("Layout14 RuntimeFix1: editor Reset callback anchor not found")

# On opening the editor we want no stale LocalController selection.
open_anchor = '''                            wudroidEditorHasSelection = false
                            wudroidEditorPanelCollapsed = false
                            wudroidEditorSeparated = inputOverlaySettings.wudroidLayoutSeparated
                            inputOverlayInputMode = EDIT_POSITION'''
if open_anchor not in screen:
    raise SystemExit("Layout14 RuntimeFix1: editor-open anchor missing")

screen = screen.replace(
    open_anchor,
    '''                            wudroidEditorHasSelection = false
                            wudroidEditorPanelCollapsed = false
                            wudroidEditorSeparated = inputOverlaySettings.wudroidLayoutSeparated
                            inputOverlayInputMode = EDIT_POSITION''',
    1,
)

screen_path.write_text(screen)

checks = [
    marker,
    "wudroidLocalOverlayResetToken",
    "editorSizePercent = if (inputOverlayInputMode == DEFAULT || !wudroidEditorHasSelection)",
    "separated = wudroidEditorSeparated",
    "resetToken = wudroidLocalOverlayResetToken",
    "onSelectionChanged = { selected ->",
]
final = screen_path.read_text()
missing = [x for x in checks if x not in final]
if missing:
    raise SystemExit(f"Layout14 RuntimeFix1 verification failed: {missing}")

print("Wudroid 0.1.2 Layout14 RuntimeFix1 applied")
print("- fixes the actual Test19 VPAD/WIIMOTE overlay path")
print("- Wii Remote is now D-pad + +/- + B/1/A/2, no Nunchuk controls")
print("- Separar updates the real Wii layout immediately")
print("- selected GamePad/Wii controls now drive the Tamanho slider")
print("- Reset clears positions/sizes without changing Separar")
