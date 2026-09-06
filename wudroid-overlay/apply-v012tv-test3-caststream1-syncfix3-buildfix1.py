#!/usr/bin/env python3
from pathlib import Path

screen_path = Path("cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationScreen.kt")
if not screen_path.exists():
    raise SystemExit("TV Cast SyncFix3 BuildFix1: EmulationScreen.kt missing")

s = screen_path.read_text()
marker = "WUDROID_TV_CAST_SYNCFIX3_BUILDFIX1_KEEP_SOURCE"
if marker in s:
    print("Wudroid TV CastStream SyncFix3 BuildFix1 already applied")
    raise SystemExit(0)

required = [
    "WUDROID_TV_DIRECT_LINK1",
    "WUDROID_TV_CAST_STREAM1",
    "tvOutputActive = wudroidTvActive",
    "wudroidTvControllerType == NativeInput.EmulatedControllerType.VPAD",
    "WudroidLanVideoHost",
]
missing = [x for x in required if x not in s]
if missing:
    raise SystemExit("TV Cast SyncFix3 BuildFix1: required base missing: " + ", ".join(missing))

# DirectLink1 already replaced the old Test1 external-display branch with a
# MainSurface capture branch. The failed SyncFix3 was still looking for the old
# branch, so it could never apply.
#
# For Wii / Motion Cast we do not need the special tvOutputActive branch at all.
# More importantly, entering that branch changes the Compose tree and disposes
# the original SurfaceView for a moment. WudroidLanVideoHost/PixelCopy is bound
# to that SurfaceView, so the HLS stream can have only the few segments buffered
# before TV mode starts and then the Cast receiver sits loading around 0:03.
#
# Keep the normal EmulationSurfaces composition completely unchanged for Wii and
# Motion. DirectLink's opaque cover (drawn later) still hides the game on the
# phone while leaving the original capture SurfaceView alive continuously.
# Only VPAD/GamePad still uses the special TV output surface path so the phone can
# show its PadSurface as a real Wii U GamePad.
old = '''            tvOutputActive = wudroidTvActive,\n            tvOutputShowPad = wudroidTvActive && wudroidTvMode == "GAME" &&\n                wudroidTvControllerType == NativeInput.EmulatedControllerType.VPAD,\n'''
new = '''            // WUDROID_TV_CAST_SYNCFIX3_BUILDFIX1_KEEP_SOURCE\n            // Wii/Motion: never switch the emulator SurfaceView composition while\n            // Cast is active; the later opaque controller cover hides the game.\n            // VPAD keeps the dedicated PadSurface behavior.\n            tvOutputActive = wudroidTvActive && wudroidTvMode == "GAME" &&\n                wudroidTvControllerType == NativeInput.EmulatedControllerType.VPAD,\n            tvOutputShowPad = wudroidTvActive && wudroidTvMode == "GAME" &&\n                wudroidTvControllerType == NativeInput.EmulatedControllerType.VPAD,\n'''

if old not in s:
    raise SystemExit("TV Cast SyncFix3 BuildFix1: EmulationSurfaces TV call block not found")

s = s.replace(old, new, 1)

checks = [
    marker,
    'tvOutputActive = wudroidTvActive && wudroidTvMode == "GAME" &&',
    'wudroidTvControllerType == NativeInput.EmulatedControllerType.VPAD',
]
missing = [x for x in checks if x not in s]
if missing:
    raise SystemExit("TV Cast SyncFix3 BuildFix1 verification failed: " + ", ".join(missing))

screen_path.write_text(s)
print("Wudroid 0.1.2TV CastStream SyncFix3 BuildFix1 applied")
print("- fixes the failed SyncFix3 anchor against the real DirectLink1 source")
print("- Wii/Motion keeps the same main SurfaceView alive before and during Cast")
print("- avoids disposing/recreating the PixelCopy/H.264 capture source at TV-mode activation")
print("- GamePad keeps its dedicated PadSurface TV-mode behavior")
