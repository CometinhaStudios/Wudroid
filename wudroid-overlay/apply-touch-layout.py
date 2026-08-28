#!/usr/bin/env python3
from pathlib import Path

path = Path("cemu-engine/src/android/app/src/main/java/info/cemu/cemu/common/settings/InputOverlayDefaultConfigs.kt")
s = path.read_text()
start = s.find("fun defaultOverlayConfigFor(input: OverlayInputConfig): InputOverlayConfig {")
end = s.find("fun getDefaultRectangle(", start)
if start < 0 or end < 0:
    raise SystemExit("Could not locate defaultOverlayConfigFor()")

replacement = r"""fun defaultOverlayConfigFor(input: OverlayInputConfig): InputOverlayConfig {
    // Wudroid Touch Layout v1.1 — larger phone preset.
    return when (input) {
        OverlayInputConfig.BUTTON_ZL -> InputOverlayConfig(paddingHorizontal = 14, paddingVertical = 8, width = 86, height = 34)
        OverlayInputConfig.BUTTON_L -> InputOverlayConfig(paddingHorizontal = 14, paddingVertical = 50, width = 86, height = 34)
        OverlayInputConfig.BUTTON_ZR -> InputOverlayConfig(alignEnd = true, paddingHorizontal = 14, paddingVertical = 8, width = 86, height = 34)
        OverlayInputConfig.BUTTON_R -> InputOverlayConfig(alignEnd = true, paddingHorizontal = 14, paddingVertical = 50, width = 86, height = 34)

        OverlayInputConfig.JOYSTICK_LEFT -> InputOverlayConfig(alignBottom = true, paddingHorizontal = 18, paddingVertical = 34, size = 76)
        OverlayInputConfig.JOYSTICK_RIGHT -> InputOverlayConfig(alignEnd = true, alignBottom = true, paddingHorizontal = 18, paddingVertical = 34, size = 76)

        OverlayInputConfig.BUTTON_L_STICK_CLICK -> InputOverlayConfig(paddingHorizontal = 105, paddingVertical = 92, size = 42)
        OverlayInputConfig.BUTTON_R_STICK_CLICK -> InputOverlayConfig(alignEnd = true, paddingHorizontal = 105, paddingVertical = 92, size = 42)

        OverlayInputConfig.DPAD -> InputOverlayConfig(alignBottom = true, paddingHorizontal = 108, paddingVertical = 8, size = 92)

        OverlayInputConfig.BUTTON_Y -> InputOverlayConfig(alignBottom = true, alignEnd = true, paddingHorizontal = 138, paddingVertical = 42, size = 44)
        OverlayInputConfig.BUTTON_A -> InputOverlayConfig(alignBottom = true, alignEnd = true, paddingHorizontal = 72, paddingVertical = 42, size = 44)
        OverlayInputConfig.BUTTON_X -> InputOverlayConfig(alignBottom = true, alignEnd = true, paddingHorizontal = 105, paddingVertical = 75, size = 44)
        OverlayInputConfig.BUTTON_B -> InputOverlayConfig(alignBottom = true, alignEnd = true, paddingHorizontal = 105, paddingVertical = 9, size = 44)

        OverlayInputConfig.BUTTON_MINUS -> InputOverlayConfig(alignBottom = true, paddingHorizontal = 205, paddingVertical = 8, size = 36)
        OverlayInputConfig.BUTTON_PLUS -> InputOverlayConfig(alignBottom = true, alignEnd = true, paddingHorizontal = 205, paddingVertical = 8, size = 36)

        OverlayInputConfig.BUTTON_HOME -> InputOverlayConfig(alignBottom = true, alignEnd = true, paddingHorizontal = 164, paddingVertical = 8, size = 36)
        OverlayInputConfig.BUTTON_BLOW_MIC -> InputOverlayConfig(alignBottom = true, alignEnd = true, paddingHorizontal = 8, paddingVertical = 8, size = 36)

        OverlayInputConfig.BUTTON_C -> InputOverlayConfig(alignEnd = true, paddingHorizontal = 62, paddingVertical = 8, size = 46)
        OverlayInputConfig.BUTTON_Z -> InputOverlayConfig(alignEnd = true, paddingHorizontal = 52, paddingVertical = 58, width = 72, height = 34)
        OverlayInputConfig.BUTTON_ONE -> InputOverlayConfig(alignBottom = true, alignEnd = true, paddingHorizontal = 138, paddingVertical = 42, size = 44)
        OverlayInputConfig.BUTTON_TWO -> InputOverlayConfig(alignBottom = true, alignEnd = true, paddingHorizontal = 105, paddingVertical = 75, size = 44)
    }
}

"""
path.write_text(s[:start] + replacement + s[end:])
print("Wudroid Touch Layout v1.1 applied")
