#!/usr/bin/env python3
from pathlib import Path
import re

root = Path("cemu-engine/src/android/app/src/main/java/info/cemu/cemu")
controller = root / "settings/input/controller/ControllerInputSettingsScreen.kt"

if not controller.exists():
    raise SystemExit("ControllerInputSettingsScreen.kt not found")

s = controller.read_text()
needle = "WudroidKeyboardMouseSettings(controllerIndex = controllerIndex)"

if needle not in s:
    pattern = re.compile(
        r"(?P<block>\n(?P<indent>[ \t]*)if \(controllerType == EmulatedControllerType\.DISABLED\) \{\s*"
        r"return@ScreenContent\s*\})"
    )
    match = pattern.search(s)
    if not match:
        raise SystemExit("Keyboard mapping UI anchor missing in ControllerInputSettingsScreen.kt")
    indent = match.group("indent")
    insertion = match.group("block") + f"\n\n{indent}WudroidKeyboardMouseSettings(controllerIndex = controllerIndex)"
    s = s[:match.start()] + insertion + s[match.end():]

controller.write_text(s)

if needle not in controller.read_text():
    raise SystemExit("Keyboard + mouse mapping UI verification failed")

print("Wudroid 0.1.1 KeyboardMouse Mapping Test1 applied")
print("- keyboard: uses Cemu native per-input mapper")
print("- mouse: emulated right analog stick")
print("- settings: sensitivity, capture pointer, invert X/Y")
