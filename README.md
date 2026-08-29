# Wudroid 0.1.1 — FrameGen Foundation 1

This corrects the direction of 0.1.1:

## Removed
- 45 bundled 60 FPS/FPS++/uncapped Graphic Packs
- `WudroidFpsPatchManager`
- per-game `FPS desbloqueado` patch selector

Compatibility/workaround packs such as the NSMBU and Minecraft crash fixes are
**not** removed.

## Added
### Lossless.dll import
Advanced Settings -> Frame Generation:
- import the user's own `Lossless.dll`
- validate MZ + PE headers
- copy it into Wudroid private storage
- SHA-256 fingerprint
- replace/remove it safely
- no downloading/bundling of proprietary assets

### Per-game Frame Generation profile
Long-press game -> per-game graphics:
- Disabled
- `LSFG 2X [Foundation]`

A private session file is created before game launch for the upcoming native
Vulkan presentation hook.

## Important status
This is intentionally called **Foundation 1**. It does NOT yet interpolate
frames. The DLL path, validation and per-game wiring are real; the next native
test must connect the Vulkan presenter to the frame-generation pipeline.

Eden's Android LSFG merge touched thousands of lines across the Vulkan
presentation path, so Wudroid will do this in tested stages rather than
pretending a UI toggle is already functional.

## Expected APK
`Wudroid-0.1.1-FrameGen-Foundation1.apk`
