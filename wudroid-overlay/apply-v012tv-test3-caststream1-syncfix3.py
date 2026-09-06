#!/usr/bin/env python3
from pathlib import Path

screen_path = Path("cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationScreen.kt")
if not screen_path.exists():
    raise SystemExit("TV Cast SyncFix3: EmulationScreen.kt missing")

s = screen_path.read_text()
marker = "WUDROID_TV_CAST_SYNCFIX3_SURFACE_KEEPALIVE"
if marker in s:
    print("Wudroid TV CastStream SyncFix3 already applied")
    raise SystemExit(0)

required = [
    "WUDROID_TV_MODE_TEST1",
    "WUDROID_TV_CAST_STREAM1",
    "tvOutputActive: Boolean = false",
    "WudroidLanVideoHost",
]
missing = [x for x in required if x not in s]
if missing:
    raise SystemExit("TV Cast SyncFix3: required base missing: " + ", ".join(missing))

old = '''    if (tvOutputActive) {
        // Main/TV Surface is owned by WudroidTvPresentation now.
        // VPAD keeps the Wii U GamePad framebuffer on the phone; Wii/Motion
        // leaves only the touch controller visible over a dark background.
        Box(modifier = Modifier.fillMaxSize().background(Color(0xFF0B0E12))) {
            if (tvOutputShowPad) {
                PadSurface(Modifier.fillMaxSize())
            }
        }
        return
    }

    LinearLayout(isVertical) { itemModifier ->
        SurfacesInOrder(itemModifier)
    }
'''

new = '''    // WUDROID_TV_CAST_SYNCFIX3_SURFACE_KEEPALIVE
    // Google Cast/HLS still captures Cemu through PixelCopy on the phone's
    // original main SurfaceView. Removing EmulationSurfaces when TV mode becomes
    // active destroys that SurfaceView, so the TV only receives the few HLS
    // segments buffered before activation and then stalls forever.
    //
    // Keep the normal emulator surfaces mounted and rendering underneath an
    // opaque phone-side cover. The player never sees the game on the phone, but
    // PixelCopy keeps receiving fresh frames for Cast. VPAD gets its GamePad
    // surface redrawn above the cover; Wii/Motion leaves only the touch overlay,
    // which is composed later by EmulationScreen.
    Box(modifier = Modifier.fillMaxSize()) {
        LinearLayout(isVertical) { itemModifier ->
            SurfacesInOrder(itemModifier)
        }

        if (tvOutputActive) {
            Box(modifier = Modifier.fillMaxSize().background(Color(0xFF0B0E12))) {
                if (tvOutputShowPad) {
                    PadSurface(Modifier.fillMaxSize())
                }
            }
        }
    }
'''

if old not in s:
    raise SystemExit("TV Cast SyncFix3: TV output surface block not found")

s = s.replace(old, new, 1)

checks = [
    marker,
    "SurfacesInOrder(itemModifier)",
    "if (tvOutputActive)",
    "PadSurface(Modifier.fillMaxSize())",
]
missing = [x for x in checks if x not in s]
if missing:
    raise SystemExit("TV Cast SyncFix3 verification failed: " + ", ".join(missing))

screen_path.write_text(s)
print("Wudroid 0.1.2TV CastStream SyncFix3 applied")
print("- keeps the main Cemu SurfaceView alive while casting")
print("- prevents PixelCopy/H.264 capture from stopping when the phone becomes controller-only")
print("- keeps the game hidden on the phone behind an opaque cover")
