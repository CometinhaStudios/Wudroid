# LSFG / Lossless Scaling source notice

Wudroid does **not** ship, download, or redistribute `Lossless.dll`.

The user must select their own legitimately obtained copy. Test 1 only copies
that user-selected file into Wudroid private storage after validating that it
looks like a Windows PE/DLL file.

Planned native backend reference:
- PancakeTAS/lsfg-vk (MIT)
- FrankBarretta/lsfg-vk-android (MIT Android AHardwareBuffer patches)

Important technical detail:
Android does not execute `Lossless.dll` directly. Android LSFG projects parse
the DLL to obtain the frame-generation shader/model resources, then execute
the interpolation pipeline with native Vulkan code.

No proprietary Lossless Scaling asset is included in this patch.
