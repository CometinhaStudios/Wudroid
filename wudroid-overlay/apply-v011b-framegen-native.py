#!/usr/bin/env python3
from pathlib import Path
import re

root = Path("cemu-engine")
java = root / "src/android/app/src/main/java/info/cemu/cemu"
cpp = root / "src/android/app/src/main/cpp"

# Add JNI source to CemuAndroid.
cmake = cpp / "CMakeLists.txt"
s = cmake.read_text()
if "WudroidFrameGenerationNative.cpp" not in s:
    s = s.replace("NativeSettings.cpp", "NativeSettings.cpp WudroidFrameGenerationNative.cpp")
if "lsfg-vk-framegen" not in s:
    s = re.sub(
        r"target_link_libraries\(CemuAndroid PRIVATE ([^\)]*)\)",
        lambda m: "target_link_libraries(CemuAndroid PRIVATE " + m.group(1).strip() + " lsfg-vk-framegen )",
        s,
        count=1,
    )
if "WUDROID_LSFG_LINKED" not in s:
    s += "\ntarget_compile_definitions(CemuAndroid PRIVATE WUDROID_LSFG_LINKED=1)\n"
cmake.write_text(s)

# Pull the MIT framegen library into the same CMake build. The workflow copies
# the checked-out dependency under cemu-engine/dependencies/lsfg-vk-android.
top = root / "CMakeLists.txt"
s = top.read_text()
marker = 'add_subdirectory("dependencies/ih264d" EXCLUDE_FROM_ALL)'
block = '''\nif(ANDROID AND EXISTS "${CMAKE_SOURCE_DIR}/dependencies/lsfg-vk-android/framegen/CMakeLists.txt")\n    add_subdirectory("dependencies/lsfg-vk-android/thirdparty/volk" EXCLUDE_FROM_ALL)\n    add_subdirectory("dependencies/lsfg-vk-android/framegen" EXCLUDE_FROM_ALL)\nendif()\n'''
if "dependencies/lsfg-vk-android/framegen" not in s:
    if marker not in s:
        raise SystemExit("Could not locate Cemu dependency insertion point")
    s = s.replace(marker, block + "\n" + marker, 1)
top.write_text(s)

# Version text in Wudroid frontend.
main = java / "MainActivity.kt"
if main.exists():
    s = main.read_text()
    s = s.replace("Wudroid 0.1.1 • frontend independente", "Wudroid 0.1.1b • frontend independente")
    s = s.replace('InfoRow("Wudroid", "0.1.1")', 'InfoRow("Wudroid", "0.1.1b")')
    s = s.replace('Text("0.1.1", color = WBlue', 'Text("0.1.1b", color = WBlue')
    main.write_text(s)

print("Wudroid 0.1.1b FrameGen native preparation applied")
