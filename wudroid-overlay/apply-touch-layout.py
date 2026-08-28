#!/usr/bin/env python3
from pathlib import Path

path = Path(
    "cemu-engine/src/android/app/src/main/java/info/cemu/cemu/common/settings/"
    "InputOverlayDefaultConfigs.kt"
)
s = path.read_text()

start = s.find("fun defaultOverlayConfigFor(input: OverlayInputConfig): InputOverlayConfig {")
end = s.find("fun getDefaultRectangle(", start)
if start < 0 or end < 0:
    raise SystemExit("Could not locate defaultOverlayConfigFor()")

replacement = r"""fun defaultOverlayConfigFor(input: OverlayInputConfig): InputOverlayConfig {
    // Wudroid Touch Layout v1
    return when (input) {
        OverlayInputConfig.BUTTON_ZL -> InputOverlayConfig(
            paddingHorizontal = 18, paddingVertical = 8, width = 64, height = 28
        )
        OverlayInputConfig.BUTTON_L -> InputOverlayConfig(
            paddingHorizontal = 18, paddingVertical = 44, width = 64, height = 28
        )
        OverlayInputConfig.BUTTON_ZR -> InputOverlayConfig(
            alignEnd = true, paddingHorizontal = 18, paddingVertical = 8, width = 64, height = 28
        )
        OverlayInputConfig.BUTTON_R -> InputOverlayConfig(
            alignEnd = true, paddingHorizontal = 18, paddingVertical = 44, width = 64, height = 28
        )

        OverlayInputConfig.JOYSTICK_LEFT -> InputOverlayConfig(
            alignBottom = true, paddingHorizontal = 22, paddingVertical = 48, size = 56
        )
        OverlayInputConfig.JOYSTICK_RIGHT -> InputOverlayConfig(
            alignEnd = true, alignBottom = true,
            paddingHorizontal = 22, paddingVertical = 48, size = 56
        )

        OverlayInputConfig.BUTTON_L_STICK_CLICK -> InputOverlayConfig(
            paddingHorizontal = 95, paddingVertical = 82, size = 36
        )
        OverlayInputConfig.BUTTON_R_STICK_CLICK -> InputOverlayConfig(
            alignEnd = true, paddingHorizontal = 95, paddingVertical = 82, size = 36
        )

        OverlayInputConfig.DPAD -> InputOverlayConfig(
            alignBottom = true, paddingHorizontal = 112, paddingVertical = 8, size = 72
        )

        OverlayInputConfig.BUTTON_Y -> InputOverlayConfig(
            alignBottom = true, alignEnd = true,
            paddingHorizontal = 130, paddingVertical = 34, size = 32
        )
        OverlayInputConfig.BUTTON_A -> InputOverlayConfig(
            alignBottom = true, alignEnd = true,
            paddingHorizontal = 78, paddingVertical = 34, size = 32
        )
        OverlayInputConfig.BUTTON_X -> InputOverlayConfig(
            alignBottom = true, alignEnd = true,
            paddingHorizontal = 104, paddingVertical = 60, size = 32
        )
        OverlayInputConfig.BUTTON_B -> InputOverlayConfig(
            alignBottom = true, alignEnd = true,
            paddingHorizontal = 104, paddingVertical = 8, size = 32
        )

        OverlayInputConfig.BUTTON_MINUS -> InputOverlayConfig(
            alignBottom = true, paddingHorizontal = 205, paddingVertical = 6, size = 30
        )
        OverlayInputConfig.BUTTON_PLUS -> InputOverlayConfig(
            alignBottom = true, alignEnd = true,
            paddingHorizontal = 205, paddingVertical = 6, size = 30
        )

        OverlayInputConfig.BUTTON_HOME -> InputOverlayConfig(
            alignBottom = true, alignEnd = true,
            paddingHorizontal = 168, paddingVertical = 6, size = 30
        )
        OverlayInputConfig.BUTTON_BLOW_MIC -> InputOverlayConfig(
            alignBottom = true, alignEnd = true,
            paddingHorizontal = 8, paddingVertical = 8, size = 30
        )

        OverlayInputConfig.BUTTON_C -> InputOverlayConfig(
            alignEnd = true, paddingHorizontal = 60, paddingVertical = 8, size = 40
        )
        OverlayInputConfig.BUTTON_Z -> InputOverlayConfig(
            alignEnd = true, paddingHorizontal = 48, paddingVertical = 54, width = 60, height = 30
        )
        OverlayInputConfig.BUTTON_ONE -> InputOverlayConfig(
            alignBottom = true, alignEnd = true,
            paddingHorizontal = 130, paddingVertical = 34, size = 32
        )
        OverlayInputConfig.BUTTON_TWO -> InputOverlayConfig(
            alignBottom = true, alignEnd = true,
            paddingHorizontal = 104, paddingVertical = 60, size = 32
        )
    }
}

"""
s = s[:start] + replacement + s[end:]
path.write_text(s)
print("Wudroid Touch Layout v1 defaults applied")
