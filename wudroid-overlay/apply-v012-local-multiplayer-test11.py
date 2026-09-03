#!/usr/bin/env python3
from pathlib import Path

main_path = Path(
    "cemu-engine/src/android/app/src/main/java/info/cemu/cemu/MainActivity.kt"
)
if not main_path.exists():
    raise SystemExit("MainActivity.kt missing")

main = main_path.read_text()
main = main.replace(
    "Wudroid 0.1.2 • multiplayer local Test10",
    "Wudroid 0.1.2 • multiplayer local Test11",
)
main = main.replace(
    "multiplayer local Test10",
    "multiplayer local Test11",
)
main = main.replace(
    "Streaming H.264 720p experimental • Test10",
    "Streaming H.264 720p low-latency • Test11",
)

marker = "WUDROID_012_LOCAL_MULTIPLAYER_TEST11"
if marker not in main:
    main += "\n// " + marker + "\n"

main_path.write_text(main)

for required in (marker, "WudroidLanVideoPreview()"):
    if required not in main:
        raise SystemExit("Test11 verification failed: " + required)

print("Wudroid 0.1.2 Local Multiplayer Test11 applied")
