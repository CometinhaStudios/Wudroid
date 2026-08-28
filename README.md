# Wudroid 0.0.8 — Performance Overlay BuildFix 1

Corrige a compilação Kotlin do patch Performance Overlay Stats 1.

O `NativeSettings` atual do Cemu Android mantém as posições do overlay dentro do objeto
`NativeSettings.OverlayScreenPosition`. O patch anterior usava nomes planos que não existem.

Correções:
- `OVERLAY_SCREEN_POSITION_DISABLED` -> `OverlayScreenPosition.DISABLED`
- `OVERLAY_SCREEN_POSITION_TOP_LEFT` -> `OverlayScreenPosition.TOP_LEFT`
- `OVERLAY_SCREEN_POSITION_TOP_RIGHT` -> `OverlayScreenPosition.TOP_RIGHT`
- `OVERLAY_SCREEN_POSITION_BOTTOM_LEFT` -> `OverlayScreenPosition.BOTTOM_LEFT`
- `OVERLAY_SCREEN_POSITION_BOTTOM_RIGHT` -> `OverlayScreenPosition.BOTTOM_RIGHT`

Não altera o core, Vulkan X ou Graphic Packs.
