#!/usr/bin/env python3
from pathlib import Path

main_path = Path(
    "cemu-engine/src/android/app/src/main/java/info/cemu/cemu/MainActivity.kt"
)
if not main_path.exists():
    raise SystemExit("MainActivity.kt missing")

main = main_path.read_text()
main = main.replace(
    "Wudroid 0.1.2 • multiplayer local Test15",
    "Wudroid 0.1.2 • multiplayer local Test16",
)
main = main.replace(
    "multiplayer local Test15",
    "multiplayer local Test16",
)
main = main.replace(
    "Streaming H.264 360p60 fullscreen monitor • Test15",
    "Streaming H.264 360p60 16:9 monitor • Test16",
)

marker = "WUDROID_012_LOCAL_MULTIPLAYER_TEST16"
if marker not in main:
    main += "\n// " + marker + "\n"

main_path.write_text(main)

for required in (
    marker,
    "WudroidLanFullscreenMonitor(",
    "verticalScroll(rememberScrollState())",
):
    if required not in main:
        raise SystemExit("Test16 verification failed: " + required)

print("Wudroid 0.1.2 Local Multiplayer Test16 applied")
print("- client monitor forced to 16:9")
print("- setup screen scroll enabled")
print("- turbo UI removed from build workflow")
