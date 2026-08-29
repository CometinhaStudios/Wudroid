# Frame Generation source / asset notice

Wudroid 0.1.1 is moving away from game-specific 60 FPS Graphic Packs and
toward a renderer-side frame-generation path.

Reference implementations researched:
- Eden emulator's merged Android LSFG-VK implementation (GPLv3+).
- FrankBarretta/lsfg-vk-android (MIT), which adds Android AHardwareBuffer entry
  points to lsfg-vk.

This Foundation build does **not** copy Eden's GPL renderer code and does not
bundle Lossless Scaling assets.

`Lossless.dll` is proprietary to Lossless Scaling / THS and is never included
or downloaded by Wudroid. Users must select their own legitimately obtained
copy at runtime.
