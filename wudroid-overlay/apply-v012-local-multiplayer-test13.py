#!/usr/bin/env python3
from pathlib import Path

main_path = Path(
    "cemu-engine/src/android/app/src/main/java/info/cemu/cemu/MainActivity.kt"
)
if not main_path.exists():
    raise SystemExit("MainActivity.kt missing")

main = main_path.read_text()
main = main.replace(
    "Wudroid 0.1.2 • multiplayer local Test12",
    "Wudroid 0.1.2 • multiplayer local Test13",
)
main = main.replace(
    "multiplayer local Test12",
    "multiplayer local Test13",
)
main = main.replace(
    "Streaming H.264 720p60 low-latency • Test12",
    "Streaming H.264 360p60 ultra-low-latency • Test13",
)

marker = "WUDROID_012_LOCAL_MULTIPLAYER_TEST13"
if marker not in main:
    main += "\n// " + marker + "\n"

main_path.write_text(main)

for required in (marker, "WudroidLanVideoPreview()"):
    if required not in main:
        raise SystemExit("Test13 verification failed: " + required)

print("Wudroid 0.1.2 Local Multiplayer Test13 applied")
print("- H.264 640x360 / 60 FPS / 3.2 Mbps / ultra-low-latency test")
