#!/usr/bin/env python3
from pathlib import Path

main_path = Path(
    "cemu-engine/src/android/app/src/main/java/info/cemu/cemu/MainActivity.kt"
)

if not main_path.exists():
    raise SystemExit("MainActivity.kt missing")

main = main_path.read_text()

main = main.replace(
    "Wudroid 0.1.2 • multiplayer local Test8",
    "Wudroid 0.1.2 • multiplayer local Test9",
)
main = main.replace(
    "multiplayer local Test8",
    "multiplayer local Test9",
)
main = main.replace(
    "Streaming LAN experimental • vídeo apenas neste Test8",
    "Streaming H.264 experimental • Test9",
)

marker = "WUDROID_012_LOCAL_MULTIPLAYER_TEST9"

if marker not in main:
    main += "\n// " + marker + "\n"

main_path.write_text(main)

for required in (
    marker,
    "WudroidLanVideoPreview()",
):
    if required not in main:
        raise SystemExit(
            "Test9 verification failed: " + required
        )

print("Wudroid 0.1.2 Local Multiplayer Test9 applied")
print("- MediaCodec H.264 enabled")
print("- 640x360 / 24 FPS / 1.8 Mbps baseline")
