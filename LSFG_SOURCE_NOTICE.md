# LSFG / Lossless Scaling source notice

Wudroid does **not** ship, download, or redistribute `Lossless.dll` or extracted proprietary shader blobs.

The user must select their own legitimately obtained copy.

Native frame-generation library used by this Test 1b build:
- FrankBarretta/lsfg-vk-android, `release` branch — MIT license, derived from PancakeTAS/lsfg-vk.

Implementation reference used for the Wudroid renderer plan:
- Eden Emulator PR #4263, LSFG-VK Android/Vulkan implementation (GPL-3.0-or-later files).

This package only links the MIT framegen engine and adds Wudroid-specific JNI/UI preparation. It does not copy Eden's GPL renderer implementation into Cemu in Test 1b.
