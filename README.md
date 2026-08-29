# Wudroid 0.1.1 — Frame Generation Config — Test 1

This replaces the previous 60-FPS-patch experiment.

## Removed
- automatic 60 FPS Graphic Pack collection
- `FPS desbloqueado` per-game patch mode

The old FPS files may remain in a Git checkout after copying this ZIP, but the
new workflow does not package or use them. The apply commands supplied by
ChatGPT remove the stale files from the Wudroid repository too.

## Added: detailed Frame Generation per game

Long-press game -> Configurações gráficas deste jogo -> Frame generation.

Options modeled after the requested Eden-style screen:
- enable / disable
- use global configuration
- import/remove user-supplied `Lossless.dll`
- target: fixed multiplier / 60 / 90 / 120 / 144 / 165 FPS
- multiplier: 2x / 3x / 4x
- queue: lowest latency / balanced / smoothest
- match motion estimation to game resolution
- half-precision shaders

## Lossless.dll importer
- uses Android SAF
- validates MZ + PE signatures
- copies to private app storage
- never modifies or deletes the user's original DLL
- Wudroid does not include or download Lossless.dll

## What is functional in Test 1
- DLL import/storage/validation
- all per-game settings
- settings persistence by Title ID
- FIFO-style VSync preparation when FG is enabled
- no 60 FPS patches are applied

## What is NOT claimed yet
Actual LSFG-generated frames are **not wired to the Cemu Vulkan renderer in
Test 1**. The next native stage must connect Cemu's rendered images to the
Android LSFG Vulkan pipeline (AHardwareBuffer path) and feed generated images
back to presentation.

Expected APK:
`Wudroid-0.1.1-FrameGen-Config-Test1.apk`
