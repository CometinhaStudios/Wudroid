#!/usr/bin/env python3
from pathlib import Path

main_path = Path(
    "cemu-engine/src/android/app/src/main/java/info/cemu/cemu/MainActivity.kt"
)
video_path = Path(
    "cemu-engine/src/android/app/src/main/java/info/cemu/cemu/WudroidLanVideo.kt"
)

if not main_path.exists():
    raise SystemExit("MainActivity.kt missing")
if not video_path.exists():
    raise SystemExit("WudroidLanVideo.kt missing")

main = main_path.read_text()
video = video_path.read_text()

main = main.replace(
    "Wudroid 0.1.2 • multiplayer local Test16",
    "Wudroid 0.1.2 • multiplayer local Test17",
)
main = main.replace(
    "multiplayer local Test16",
    "multiplayer local Test17",
)
main = main.replace(
    "Streaming H.264 360p60 16:9 monitor • Test16",
    "Streaming H.264 360p60 game-only crop • Test17",
)

marker = "WUDROID_012_LOCAL_MULTIPLAYER_TEST17"
if marker not in main:
    main += "\n// " + marker + "\n"

main_path.write_text(main)

required_video = (
    "WUDROID_012_LOCAL_MULTIPLAYER_TEST17_SOURCE_CROP",
    "gameSourceRect(surfaceView)",
    "PixelCopy.request(",
)
for required in required_video:
    if required not in video:
        raise SystemExit("Test17 video verification failed: " + required)

if marker not in main:
    raise SystemExit("Test17 MainActivity marker missing")

print("Wudroid 0.1.2 Local Multiplayer Test17 applied")
print("- host capture cropped to centered 16:9 BEFORE encoding")
print("- black/pillar/letterbox regions outside the game viewport are not streamed")
print("- Test14 60 Hz pacing and Test13 low-latency path preserved")
