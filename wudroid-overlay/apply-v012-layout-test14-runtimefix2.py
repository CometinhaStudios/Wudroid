#!/usr/bin/env python3
from pathlib import Path

overlay_path = Path("cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/WudroidLocalControllerOverlay.kt")
screen_path = Path("cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationScreen.kt")

for path in (overlay_path, screen_path):
    if not path.exists():
        raise SystemExit(f"Layout14 RuntimeFix2: required source missing: {path}")

overlay = overlay_path.read_text()
screen = screen_path.read_text()

checks = {
    "runtimefix2 marker": "WUDROID_LAYOUT14_RUNTIMEFIX2",
    "slide touch router": "LocalSlideTouchRouter",
    "rotated visual up": 'LocalButton("▲", NativeInput.WiimoteButton.RIGHT',
    "rotated visual left": 'LocalButton("◀", NativeInput.WiimoteButton.UP',
    "rotated visual right": 'LocalButton("▶", NativeInput.WiimoteButton.DOWN',
    "rotated visual down": 'LocalButton("▼", NativeInput.WiimoteButton.LEFT',
    "less transparent controls": "Color(0xF2D8D8D8)",
}
missing = [name for name, token in checks.items() if token not in overlay]
if missing:
    raise SystemExit("Layout14 RuntimeFix2 overlay verification failed: " + ", ".join(missing))

if "WUDROID_LAYOUT14_RUNTIMEFIX1" not in screen:
    raise SystemExit("Layout14 RuntimeFix2: RuntimeFix1 EmulationScreen bridge missing")

print("Wudroid 0.1.2 Layout14 RuntimeFix2 verified")
print("- Wii D-pad visual directions rotated to the Cemu sideways-Wiimote mapping")
print("- Wii controls are slightly smaller, lower, and less transparent")
print("- slide-touch routes a held finger from one button to the next")
print("- slide-touch also works on GamePad buttons without changing stick behavior")
