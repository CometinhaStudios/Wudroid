#!/usr/bin/env python3
from pathlib import Path
import re

screen_path = Path("cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationScreen.kt")
manifest_path = Path("cemu-engine/src/android/app/src/main/AndroidManifest.xml")
gradle_path = Path("cemu-engine/src/android/app/build.gradle.kts")

for path, label in [
    (screen_path, "EmulationScreen.kt"),
    (manifest_path, "AndroidManifest.xml"),
    (gradle_path, "build.gradle.kts"),
]:
    if not path.exists():
        raise SystemExit(f"TV CastStream1: {label} missing")

s = screen_path.read_text()
marker = "WUDROID_TV_CAST_STREAM1"
if marker in s:
    print("Wudroid TV CastStream1 already applied")
    raise SystemExit(0)

required = [
    "WUDROID_TV_DIRECT_LINK1",
    "WUDROID_TV_MODE_TEST1_RUNTIMEFIX1",
    "WudroidTvDirectHost.disconnect()",
    "scanWudroidTvReceivers()",
    "WudroidTvPickerDialog(",
    "connectedName = wudroidTvConnectedName",
    "MainSurface(Modifier.fillMaxSize())",
]
missing = [x for x in required if x not in s]
if missing:
    raise SystemExit("TV CastStream1: DirectLink1 base missing: " + ", ".join(missing))


def ensure_import(text: str, imp: str) -> str:
    line = imp + "\n"
    if line in text:
        return text
    return text.replace("package info.cemu.cemu.emulation\n", "package info.cemu.cemu.emulation\n" + line, 1)

for imp in [
    "import info.cemu.cemu.WudroidCastController",
    "import info.cemu.cemu.WudroidCastState",
]:
    s = ensure_import(s, imp)

# ---------------------------------------------------------------------------
# Transport: replace the custom TV receiver with the real Google Cast session.
# ---------------------------------------------------------------------------
s = s.replace(
    "        WudroidTvDirectHost.disconnect()\n",
    "        WudroidCastController.stopCasting() // WUDROID_TV_CAST_STREAM1\n",
    1,
)

# DirectLink's LAN scan effect is replaced by the official CAF picker. The
# MediaRouteButton inside WudroidCastController opens Google's own device list;
# the TV requires no Wudroid installation.
old_effect = '''    LaunchedEffect(showWudroidTvPickerDialog) {
        if (showWudroidTvPickerDialog) {
            scanWudroidTvReceivers()
        }
    }

    DisposableEffect(Unit) {'''
new_effect = '''    LaunchedEffect(showWudroidTvPickerDialog) {
        if (showWudroidTvPickerDialog) {
            showWudroidTvPickerDialog = false
            val castActivity = wudroidQuickStateContext as? Activity
            if (castActivity != null) {
                WudroidCastController.openDevicePicker(
                    castActivity,
                    wudroidTvMode ?: "GAME",
                )
            } else {
                snackbarHostState.showSnackbar("Não foi possível abrir o seletor da TV")
            }
        }
    }

    DisposableEffect("WUDROID_TV_CAST_STREAM1") {
        val castActivity = wudroidQuickStateContext as? Activity
        if (castActivity != null) {
            WudroidCastController.initialize(castActivity)
        }

        WudroidCastController.setStateListener { castState: WudroidCastState ->
            wudroidTvConnectedName = castState.deviceName

            if (castState.connected && !wudroidTvActive) {
                val selectedMode = wudroidTvMode ?: "GAME"
                if (selectedMode == "MOTION") {
                    if (wudroidTvPreviousControllerType < 0) {
                        wudroidTvPreviousControllerType = runCatching {
                            NativeInput.getControllerType(0)
                        }.getOrDefault(NativeInput.EmulatedControllerType.WIIMOTE)
                    }
                    runCatching {
                        NativeInput.setControllerType(0, NativeInput.EmulatedControllerType.WIIMOTE)
                    }
                    setMotionSensorEnabled(true)
                    castActivity?.requestedOrientation = ActivityInfo.SCREEN_ORIENTATION_PORTRAIT
                } else {
                    if (wudroidTvPreviousControllerType >= 0) {
                        runCatching {
                            NativeInput.setControllerType(0, wudroidTvPreviousControllerType)
                        }
                        wudroidTvPreviousControllerType = -1
                    }
                    castActivity?.requestedOrientation = ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED
                    setMotionSensorEnabled(sideMenuState.isMotionEnabled)
                }

                wudroidTvActive = true
                scope.launch {
                    snackbarHostState.showSnackbar(
                        "Transmitindo para ${castState.deviceName ?: "TV"}"
                    )
                }
            } else if (!castState.connected && !castState.loading && wudroidTvActive) {
                // Session was stopped from Google's Cast UI / TV.
                wudroidTvActive = false
                wudroidTvConnectedName = null
                if (wudroidTvPreviousControllerType >= 0) {
                    runCatching {
                        NativeInput.setControllerType(0, wudroidTvPreviousControllerType)
                    }
                    wudroidTvPreviousControllerType = -1
                }
                castActivity?.requestedOrientation = ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED
                setMotionSensorEnabled(sideMenuState.isMotionEnabled)
            }

            val castError = castState.error
            if (!castError.isNullOrBlank()) {
                scope.launch { snackbarHostState.showSnackbar(castError) }
            }
        }

        onDispose {
            WudroidCastController.setStateListener(null)
        }
    }

    DisposableEffect(Unit) {'''
if old_effect not in s:
    raise SystemExit("TV CastStream1: DirectLink picker effect not found")
s = s.replace(old_effect, new_effect, 1)

# Remove the custom receiver picker call completely. The official Google Cast
# chooser is launched automatically by the LaunchedEffect above.
picker_call_re = re.compile(
    r'''    if \(showWudroidTvPickerDialog\) \{\n        WudroidTvPickerDialog\(\n            receivers = wudroidTvReceivers,.*?\n        \)\n    \}\n''',
    re.S,
)
s, n = picker_call_re.subn("", s, count=1)
if n != 1:
    raise SystemExit("TV CastStream1: DirectLink picker invocation not found")

# Update active-session wording. The actual Cast device friendly name now comes
# from CastSession instead of the Wudroid receiver discovery packet.
s = s.replace(
    '"Transmitindo para ${connectedName ?: "Wudroid TV"}"',
    '"Transmitindo para ${connectedName ?: "TV"}"',
    1,
)

# Keep DirectLink helper code harmlessly present (unused) so this patch remains
# robust against source drift, but mark the effective path explicitly.
state_anchor = '''    var wudroidTvConnectedName by remember { mutableStateOf<String?>(null) }
'''
if state_anchor not in s:
    raise SystemExit("TV CastStream1: connected state anchor missing")
s = s.replace(
    state_anchor,
    state_anchor + '    // WUDROID_TV_CAST_STREAM1: connectedName now follows Google CastSession.\n',
    1,
)

checks = [
    marker,
    "WudroidCastController.openDevicePicker",
    "WudroidCastController.setStateListener",
    "WudroidCastController.stopCasting()",
    "Transmitindo para ${connectedName ?: \"TV\"}",
]
missing = [x for x in checks if x not in s]
if missing:
    raise SystemExit("TV CastStream1 verification failed: " + ", ".join(missing))

screen_path.write_text(s)

# ---------------------------------------------------------------------------
# Google Cast sender configuration. Default Media Receiver = no app on TV.
# ---------------------------------------------------------------------------
g = gradle_path.read_text()
dep = 'implementation("com.google.android.gms:play-services-cast-framework:22.3.1")'
if dep not in g:
    if "dependencies {" not in g:
        raise SystemExit("TV CastStream1: dependencies block missing")
    g = g.replace(
        "dependencies {",
        "dependencies {\n    // WUDROID_TV_CAST_STREAM1 - Google Cast sender / Default Media Receiver\n    " + dep,
        1,
    )
gradle_path.write_text(g)

m = manifest_path.read_text()

# Remove the old DirectLink Android-TV receiver registration. The TV no longer
# needs to install Wudroid at all.
m = re.sub(
    r'''\n\s*<!-- WUDROID_TV_DIRECT_LINK1_RECEIVER -->\s*\n\s*<activity\s+android:name="\.WudroidTvReceiverActivity".*?</activity>\s*\n''',
    "\n",
    m,
    count=1,
    flags=re.S,
)
m = re.sub(
    r'''\n\s*<uses-feature\s+android:name="android\.software\.leanback"\s+android:required="false"\s*/>\s*\n''',
    "\n",
    m,
    count=1,
    flags=re.S,
)

# Required/safe networking permissions for Cast discovery and the local HLS
# HTTP endpoint fetched by the Google TV.
permissions = [
    '<uses-permission android:name="android.permission.INTERNET" />',
    '<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />',
    '<uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />',
    '<uses-permission android:name="android.permission.CHANGE_WIFI_MULTICAST_STATE" />',
]
for perm in permissions:
    name = re.search(r'android:name="([^"]+)"', perm).group(1)
    if name not in m:
        match = re.search(r'<manifest\b[^>]*>', m)
        if not match:
            raise SystemExit("TV CastStream1: manifest tag missing")
        m = m[:match.end()] + "\n    " + perm + m[match.end():]

meta_name = "com.google.android.gms.cast.framework.OPTIONS_PROVIDER_CLASS_NAME"
if meta_name not in m:
    if "</application>" not in m:
        raise SystemExit("TV CastStream1: application closing tag missing")
    meta = '''\n        <!-- WUDROID_TV_CAST_STREAM1: sender only, uses Google's Default Media Receiver -->\n        <meta-data\n            android:name="com.google.android.gms.cast.framework.OPTIONS_PROVIDER_CLASS_NAME"\n            android:value="info.cemu.cemu.WudroidCastOptionsProvider" />\n'''
    m = m.replace("    </application>", meta + "    </application>", 1)

manifest_path.write_text(m)

print("Wudroid 0.1.2TV Test3 CastStream1 applied")
print("- Google Cast official device picker (TV appears like YouTube/Netflix)")
print("- no Wudroid installation required on Google TV")
print("- existing H.264 encoder feeds a local live-HLS stream")
print("- Google Default Media Receiver fetches the stream from the phone")
print("- phone remains Wii / GamePad / Motion controller")
