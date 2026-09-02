#!/usr/bin/env python3
from pathlib import Path

main_path = Path(
    "cemu-engine/src/android/app/src/main/java/info/cemu/cemu/MainActivity.kt"
)
manifest_path = Path(
    "cemu-engine/src/android/app/src/main/AndroidManifest.xml"
)

if not main_path.exists():
    raise SystemExit("MainActivity.kt missing")
if not manifest_path.exists():
    raise SystemExit("AndroidManifest.xml missing")

main = main_path.read_text()
manifest = manifest_path.read_text()

main = main.replace(
    "Wudroid 0.1.2 • multiplayer local Test6",
    "Wudroid 0.1.2 • multiplayer local Test7",
)
main = main.replace(
    "multiplayer local Test6",
    "multiplayer local Test7",
)

if "WUDROID_012_LOCAL_MULTIPLAYER_TEST7" not in main:
    main += "\n// WUDROID_012_LOCAL_MULTIPLAYER_TEST7\n"

for required in (
    "android.permission.ACCESS_WIFI_STATE",
    "android.permission.CHANGE_WIFI_STATE",
    "android.permission.NEARBY_WIFI_DEVICES",
):
    if required not in manifest:
        raise SystemExit(
            f"Test7 hotspot permission missing: {required}"
        )

main_path.write_text(main)

print("Wudroid 0.1.2 Local Multiplayer Test7 applied")
print("- Host Wi-Fi lifecycle belongs to multiplayer session")
print("- Android 16 custom SSID/security")
print("- Public=open / Private=room password")
