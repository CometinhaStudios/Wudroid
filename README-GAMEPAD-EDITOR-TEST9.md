# Wudroid 0.1.1 — Gamepad Editor Polish + PT-BR + Save UI Test9

Changes on top of Test8 BuildFix1:

- Smaller floating gamepad editor window, visually closer to the exit confirmation dialog.
- While the per-button size slider is being dragged, the editor window fades to 22% opacity so the selected control is visible.
- Right Quick Settings menu labels translated to PT-BR.
- New `Jogo e Save State` entry in the main in-game menu.
- A Wudroid Save State dialog shell with six slots (3 + 3), prepared for future real state metadata/thumbnail callbacks.

## Important Save State limitation

This test intentionally does **not** fake saving or restoring emulator state. Current Cemu does not expose a complete emulator-state serialization backend. Therefore `Carregar jogo` and `Save State rápido` remain disabled, and the six slots are visual placeholders until a native backend exists.

The UI is structured so the future native backend can later wire:

- tap occupied slot -> preview/load,
- long press occupied slot -> delete/reuse,
- empty slot -> save,
- timestamp/date + screenshot thumbnail.
