# Wudroid 0.1.1 — Gamepad Editor Test7 RobustFix2

Compile fix after RobustFix.

- Fixes Kotlin unresolved references `centerX`, `centerY`, `width`, and `height` in `InputOverlaySurfaceView.kt`.
- The Android Cemu branch returns a rectangle structure with coordinate fields from `Input.getBoundingRectangle()`, so the global scale code now computes center/width/height from `left`, `top`, `right`, and `bottom` directly.
- No sidebar/menu changes.
- Keeps the Test7 editor design: Transparency slider, Size slider, Reset, Finish.
