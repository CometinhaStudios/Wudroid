#!/usr/bin/env python3
from pathlib import Path

screen_path = Path("cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationScreen.kt")
if not screen_path.exists():
    raise SystemExit("EmulationScreen.kt not found")

screen = screen_path.read_text()
marker = "WUDROID_012_LOCAL_MULTIPLAYER_TEST5"
if marker in screen:
    print("Wudroid 0.1.2 Local Multiplayer Test5 already applied")
    raise SystemExit(0)

def ensure_import(source: str, imp: str) -> str:
    if imp in source:
        return source
    lines = source.splitlines(keepends=True)
    indexes = [i for i, line in enumerate(lines) if line.startswith("import ")]
    if not indexes:
        raise SystemExit("EmulationScreen import block missing")
    lines.insert(indexes[-1] + 1, imp + "\n")
    return "".join(lines)

screen = ensure_import(screen, "import info.cemu.cemu.nativeinterface.NativeInput")

# Locate the final InputOverlaySurface call structurally. All prior editor patches
# have already run, so we wrap their final call without changing its arguments.
token = "        InputOverlaySurface("
start = screen.find(token)
if start < 0:
    raise SystemExit("Test5 InputOverlaySurface call missing")

open_paren = screen.find("(", start)
depth = 0
in_string = False
escaped = False
end = -1
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
            end = i + 1
            break
if end < 0:
    raise SystemExit("Test5 InputOverlaySurface call malformed")

# Include the trailing newline but not unrelated code.
if end < len(screen) and screen[end] == '\n':
    end += 1

old_call = screen[start:end]
if "inputOverlaySettings" not in old_call or "isVisible = isInputOverlayVisible" not in old_call:
    raise SystemExit("Test5 unexpected InputOverlaySurface shape")

wrapped = """        // WUDROID_012_LOCAL_MULTIPLAYER_TEST5
        val wudroidPlayer1IsWiimote = runCatching {
            NativeInput.getControllerType(0) == NativeInput.EmulatedControllerType.WIIMOTE
        }.getOrDefault(false)

        if (wudroidPlayer1IsWiimote && inputOverlayInputMode == DEFAULT) {
            WudroidSoloWiimoteOverlay(
                isVisible = isInputOverlayVisible,
                controllerIndex = 0,
            )
        } else {
""" + old_call.replace("        ", "            ", 1) + """        }\n"""

screen = screen[:start] + wrapped + screen[end:]

for needle in (
    marker,
    "wudroidPlayer1IsWiimote",
    "NativeInput.EmulatedControllerType.WIIMOTE",
    "WudroidSoloWiimoteOverlay(",
):
    if needle not in screen:
        raise SystemExit(f"Test5 verification failed: {needle}")

screen_path.write_text(screen)
print("Wudroid 0.1.2 Local Multiplayer Test5 applied")
print("- solo Player 1 Wii Remote uses horizontal Wudroid overlay")
print("- GamePad keeps the existing editable overlay")
