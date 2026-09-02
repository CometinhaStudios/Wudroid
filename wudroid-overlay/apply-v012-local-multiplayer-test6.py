#!/usr/bin/env python3
from pathlib import Path
import re
import xml.etree.ElementTree as ET

manifest_path = Path("cemu-engine/src/android/app/src/main/AndroidManifest.xml")
main_path = Path("cemu-engine/src/android/app/src/main/java/info/cemu/cemu/MainActivity.kt")

if not manifest_path.exists():
    raise SystemExit("AndroidManifest.xml missing")
if not main_path.exists():
    raise SystemExit("MainActivity.kt missing")

manifest = manifest_path.read_text()
main = main_path.read_text()
marker = "WUDROID_012_LOCAL_MULTIPLAYER_TEST6"
# WUDROID_012_LOCAL_MULTIPLAYER_TEST6_BUILDFIX2

permissions = [
    '    <uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />',
    '    <uses-permission android:name="android.permission.CHANGE_WIFI_STATE" />',
    '    <uses-permission android:name="android.permission.NEARBY_WIFI_DEVICES" android:usesPermissionFlags="neverForLocation" />',
    '    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" android:maxSdkVersion="32" />',
]

# Test6 BuildFix1:
# Never use the first ">" in the file: it normally belongs to <?xml ...?>.
# Find the complete real <manifest ...> opening tag, which contains xmlns:android.
manifest_open = re.search(r"<manifest\b[^>]*>", manifest, flags=re.DOTALL)
if manifest_open is None:
    raise SystemExit("Manifest opening tag malformed")

insert_at = manifest_open.end()

for permission in permissions:
    permission_name = re.search(r'android:name="([^"]+)"', permission).group(1)
    if permission_name not in manifest:
        manifest = manifest[:insert_at] + "\n" + permission + manifest[insert_at:]
        insert_at += len(permission) + 1

# Fail during Apply instead of wasting the full Gradle build if XML is malformed.
try:
    ET.fromstring(manifest)
except ET.ParseError as exc:
    raise SystemExit(f"Test6 manifest XML validation failed: {exc}")

main = main.replace(
    "Wudroid 0.1.2 • multiplayer local Test5",
    "Wudroid 0.1.2 • multiplayer local Test6"
)
main = main.replace("multiplayer local Test5", "multiplayer local Test6")

if marker not in main:
    main += f"\n// {marker}\n"

for required in (
    "android.permission.ACCESS_WIFI_STATE",
    "android.permission.CHANGE_WIFI_STATE",
    "android.permission.NEARBY_WIFI_DEVICES",
):
    if required not in manifest:
        raise SystemExit(f"Test6 permission verification failed: {required}")

manifest_path.write_text(manifest)
main_path.write_text(main)

print("Wudroid 0.1.2 Local Multiplayer Test6 applied")
print("- LocalOnlyHotspot permissions")
print("- Test6 visible version marker")
