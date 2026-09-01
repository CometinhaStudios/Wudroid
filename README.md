# Wudroid 0.1.1 — Save Station Test12

Pacote incremental mais recente. Leia `README-SAVESTATION-TEST12.md` para as mudanças do Test12.

# Wudroid 0.1.1 — Shader Preload Test 1

- LSFG removed from the build.
- Frame Generation menu stays visible, forced OFF.
- No Lossless.dll, MediaProjection or external capture backend.
- Before gameplay, Wudroid uses Cemu's real transferable shader cache and Vulkan stable pipeline cache.
- Cached shaders/pipelines are completed before gameplay.
- A shader that has never been seen cannot be predicted; Cemu async compilation remains the fallback for those first-use misses.

## Gamepad Editor Test8
Adds collapsible editor chrome and individual touch-control sizing on top of RobustFix2.

## Save Station Test11
Test11 adiciona a primeira UI funcional de 6 slots (3x2) em cima do Quick State Test10 validado. Veja `README-SAVESTATION-TEST11.md`.
