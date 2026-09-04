#!/usr/bin/env python3
from pathlib import Path

screen_path = Path("cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationScreen.kt")
if not screen_path.exists():
    raise SystemExit("EmulationScreen.kt missing")
screen = screen_path.read_text()
marker = "WUDROID_012_LOCAL_MULTIPLAYER_TEST19"
if marker in screen:
    print("Test19 already applied")
    raise SystemExit(0)

old_marker = "        // WUDROID_012_LOCAL_MULTIPLAYER_TEST5\n"
start = screen.find(old_marker)
if start < 0:
    raise SystemExit("Test19 Test5 wrapper marker missing")

# Extract the already-patched InputOverlaySurface call so Pro/Classic behavior stays intact.
call_start = screen.find("InputOverlaySurface(", start)
if call_start < 0:
    raise SystemExit("Test19 InputOverlaySurface call missing")
open_paren = screen.find("(", call_start)
depth = 0
in_string = False
escaped = False
call_end = -1
for i in range(open_paren, len(screen)):
    ch = screen[i]
    if in_string:
        if escaped:
            escaped = False
        elif ch == "\\":
            escaped = True
        elif ch == '"':
            in_string = False
        continue
    if ch == '"':
        in_string = True
    elif ch == '(':
        depth += 1
    elif ch == ')':
        depth -= 1
        if depth == 0:
            call_end = i + 1
            break
if call_end < 0:
    raise SystemExit("Test19 malformed InputOverlaySurface")
original_call = screen[call_start:call_end]

# Find end of the whole Test5 if/else block by brace matching from its if.
if_start = screen.find("        if (wudroidPlayer1IsWiimote", start)
if if_start < 0:
    raise SystemExit("Test19 old Wiimote if missing")
brace = screen.find("{", if_start)
depth = 0
in_string = False
escaped = False
block_end = -1
for i in range(brace, len(screen)):
    ch = screen[i]
    if in_string:
        if escaped:
            escaped = False
        elif ch == "\\":
            escaped = True
        elif ch == '"':
            in_string = False
        continue
    if ch == '"':
        in_string = True
    elif ch == '{':
        depth += 1
    elif ch == '}':
        depth -= 1
        if depth == 0:
            block_end = i + 1
            break
if block_end < 0:
    raise SystemExit("Test19 old wrapper malformed")
if block_end < len(screen) and screen[block_end] == '\n':
    block_end += 1

# Keep indentation correct for fallback AndroidView overlay.
fallback = original_call
replacement = f"""        // {marker}\n        val wudroidPlayer1ControllerType = runCatching {{\n            NativeInput.getControllerType(0)\n        }}.getOrDefault(NativeInput.EmulatedControllerType.VPAD)\n        val wudroidUsesUnifiedTouchOverlay =\n            wudroidPlayer1ControllerType == NativeInput.EmulatedControllerType.VPAD ||\n                wudroidPlayer1ControllerType == NativeInput.EmulatedControllerType.WIIMOTE\n\n        if (wudroidUsesUnifiedTouchOverlay) {{\n            WudroidLocalControllerOverlay(\n                isVisible = isInputOverlayVisible,\n                controllerType = wudroidPlayer1ControllerType,\n                controllerIndex = 0,\n                editing = inputOverlayInputMode != DEFAULT,\n            )\n        }} else {{\n            {fallback}\n        }}\n"""

screen = screen[:start] + replacement + screen[block_end:]
screen_path.write_text(screen)

for required in (
    marker,
    "WudroidLocalControllerOverlay(",
    "controllerType = wudroidPlayer1ControllerType",
    "editing = inputOverlayInputMode != DEFAULT",
):
    if required not in screen:
        raise SystemExit("Test19 verification failed: " + required)

print("Wudroid 0.1.2 Local Multiplayer Test19 applied")
print("- Player 1 VPAD uses the multiplayer GamePad visual as the standard overlay")
print("- Player 1 Wii stays Wii while editing instead of falling back to GamePad")
print("- Player 1 Wii Nunchuk uses onOverlayAxis, matching Cemu Android")
