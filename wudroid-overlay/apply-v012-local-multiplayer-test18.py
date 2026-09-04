#!/usr/bin/env python3
from pathlib import Path

main_path = Path(
    "cemu-engine/src/android/app/src/main/java/info/cemu/cemu/MainActivity.kt"
)
if not main_path.exists():
    raise SystemExit("MainActivity.kt missing")

main = main_path.read_text()
main = main.replace(
    "Wudroid 0.1.2 • multiplayer local Test17",
    "Wudroid 0.1.2 • multiplayer local Test18",
)
main = main.replace(
    "multiplayer local Test17",
    "multiplayer local Test18",
)
main = main.replace(
    "Streaming H.264 360p60 game-only crop • Test17",
    "Streaming H.264 360p60 Player 2 overlay • Test18",
)

marker = "WUDROID_012_LOCAL_MULTIPLAYER_TEST18"
if marker not in main:
    start = main.find(
        '    if (joinedHost != null && fullscreenMonitor) {\n'
        '        WudroidLanFullscreenMonitor(\n'
    )
    end_token = '        return\n    }\n\n    ScreenScaffold("Multiplayer", ::leaveMultiplayer) {'
    end = main.find(end_token, start)
    if start < 0 or end < 0:
        raise SystemExit("Test18 fullscreen monitor block missing")

    new_block = '''    if (joinedHost != null && fullscreenMonitor) {
        WudroidLanFullscreenMonitor(
            controllerKind = joinedControllerKind,
            onControllerKindChange = { kind ->
                joinedControllerKind = kind
                WudroidLanMultiplayer.sendRemoteControllerKind(kind)
            },
            onLeave = {
                leaveMultiplayer()
            },
        )
        return
    }

    ScreenScaffold("Multiplayer", ::leaveMultiplayer) {'''

    main = main[:start] + new_block + main[end + len(end_token):]
    main += "\n// " + marker + "\n"

main_path.write_text(main)

for required in (
    marker,
    "controllerKind = joinedControllerKind",
    "WudroidLanMultiplayer.sendRemoteControllerKind(kind)",
    "leaveMultiplayer()",
):
    if required not in main:
        raise SystemExit("Test18 verification failed: " + required)

print("Wudroid 0.1.2 Local Multiplayer Test18 applied")
print("- Player 2 controls overlay the streamed game")
print("- BACK opens centered Player 2 menu")
print("- Wii Remote / GamePad can switch live")
print("- Edit Controller keeps the selected controller type")
print("- Exit disconnects Player 2")
