from pathlib import Path

p = Path("cemu-engine/src/android/app/src/main/java/info/cemu/cemu/nativeinterface/NativeSettings.kt")
if not p.exists():
    raise SystemExit(f"NativeSettings.kt not found: {p}")

s = p.read_text()

# NativeSettings.cpp in the Android port already exposes JNI entry points for
# CPU-per-core and VRAM overlay stats; the Kotlin interface simply doesn't
# declare them. Add the declarations without changing the native ABI.
if "isOverlayCPUPerCoreUsageEnabled" not in s:
    marker = '''    @JvmStatic\n    external fun isOverlayRAMUsageEnabled(): Boolean\n'''
    insert = '''    @JvmStatic\n    external fun isOverlayCPUPerCoreUsageEnabled(): Boolean\n\n    @JvmStatic\n    external fun setOverlayCPUPerCoreUsageEnabled(value: Boolean)\n\n'''
    if marker not in s:
        raise SystemExit("Could not locate RAM overlay declarations")
    s = s.replace(marker, insert + marker, 1)

if "isOverlayVRAMUsageEnabled" not in s:
    marker = '''    @JvmStatic\n    external fun isOverlayDebugEnabled(): Boolean\n'''
    insert = '''    @JvmStatic\n    external fun isOverlayVRAMUsageEnabled(): Boolean\n\n    @JvmStatic\n    external fun setOverlayVRAMUsageEnabled(value: Boolean)\n\n'''
    if marker not in s:
        raise SystemExit("Could not locate debug overlay declarations")
    s = s.replace(marker, insert + marker, 1)

p.write_text(s)
print("Wudroid performance overlay JNI declarations enabled")
