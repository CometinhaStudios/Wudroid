#!/usr/bin/env python3
from pathlib import Path

root = Path("cemu-engine")
java = root / "src/android/app/src/main/java/info/cemu/cemu"
cpp = root / "src/android/app/src/main/cpp"

# Compile the tiny Android/JNI bridge into CemuAndroid.
# Test9's real frame generation state/functions live in Cemu's Vulkan renderer;
# this file only exposes those native controls/status values to Kotlin.
cmake = cpp / "CMakeLists.txt"
s = cmake.read_text()
if "WudroidFrameGenerationNative.cpp" not in s:
    s = s.replace("NativeSettings.cpp", "NativeSettings.cpp\n        WudroidFrameGenerationNative.cpp")
cmake.write_text(s)

# Keep the public Wudroid version at 0.1.1. Test suffixes are build labels,
# not new feature versions.
main = java / "MainActivity.kt"
if main.exists():
    s = main.read_text()
    s = s.replace("Wudroid 0.1.1b • frontend independente", "Wudroid 0.1.1 • frontend independente")
    s = s.replace('InfoRow("Wudroid", "0.1.1b")', 'InfoRow("Wudroid", "0.1.1")')
    s = s.replace('Text("0.1.1b", color = WBlue', 'Text("0.1.1", color = WBlue')
    main.write_text(s)

print("Wudroid 0.1.1 Android capability bridge applied")
