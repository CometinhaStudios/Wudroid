# Wudroid 0.1.1 — FPS Unlock — Test 1

This starts the 0.1.1 line.

## Per-game FPS unlock

Long-press a game -> `Configurações gráficas deste jogo` -> `FPS`.

Options:

- `Original`
- `FPS desbloqueado (60 FPS)` when a compatible v980 patch is detected

When enabled, Wudroid:

1. matches the Graphic Pack to the game's Title ID;
2. activates the game's FPS/FPS++/60FPS/uncapped pack;
3. selects a 60 FPS preset when the pack exposes an FPS limit;
4. applies it before boot.

When `Original` is selected, Wudroid disables those FPS patches again.

This is not generic frame generation. It uses the game's own community patch,
so the goal is 60 FPS at native game speed.

## Included collection

The build bundles **45 FPS-related packs** from Graphic Packs v980,
including normal 60 FPS packs, FPS++, static-FPS, uncapped-framerate and
partial 60 FPS packs.

Some patches are version-specific or only affect part of a game. The UI marks
the feature as a per-game patch rather than promising universal compatibility.

See `FPS_PACKS_V980.md` for the exact list.

## Kept from 0.1.0

- WUX importer + post-import delete confirmation
- per-game graphics
- Minecraft / NSMBU compatibility packs
- real resolution scaling
- Graphic-Pack anti-aliasing integration
- Vulkan X
- performance overlay
- Wudroid touch layout
- automatic box art

## Expected APK

`Wudroid-0.1.1-FPS-Unlock-Test1.apk`
