# Wudroid 0.1.1 - Gamepad Editor Test7 RobustFix

This rebuild stops using the fragile function-order anchors that caused the Test7 BuildFix chain to fail one function at a time.

Changes in the patcher:
- structural Kotlin function replacement for EditInputsLayout
- structural ViewModel insertion after saveInputOverlayRectangles
- structural replacement for InputOverlaySurfaceView.setInputMode
- structural removal of Test6 wudroidScaleOverlayRect
- structural replacement of getBoundingRectangleForInput
- structural replacement of InputOverlaySurface composable
- fixes the mixed Rect/InputOverlayRect lookup that would have caused a Kotlin type error later

Feature target remains unchanged:
- top editor panel
- Transparency slider
- Size slider
- Reset and Concluir
- no per-button resize symbols
- position dragging remains available
- no repeated 1.60x growth on every Done/Concluir
- Test6 menu flow remains unchanged
