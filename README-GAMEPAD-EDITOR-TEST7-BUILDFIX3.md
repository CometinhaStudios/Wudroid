# Wudroid 0.1.1 — Gamepad Editor Test7 BuildFix3

BuildFix3 removes the fragile exact-text anchor around `saveInputOverlayRectangles`.
The patch now finds the real Kotlin function structurally by its signature and matching braces, then appends `saveInputOverlayAlpha` after it.

This keeps the Test6 menu flow unchanged and keeps the Test7 goal unchanged:
- no old per-button resize symbols
- top editor panel with Transparency and Size sliders
- Reset and Concluir buttons
- no automatic 1.60x compounding when finishing editing
