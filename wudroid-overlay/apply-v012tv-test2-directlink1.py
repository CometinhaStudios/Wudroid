#!/usr/bin/env python3
from pathlib import Path
import re

screen_path = Path("cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationScreen.kt")
manifest_path = Path("cemu-engine/src/android/app/src/main/AndroidManifest.xml")

if not screen_path.exists():
    raise SystemExit("TV DirectLink1: EmulationScreen.kt missing")
if not manifest_path.exists():
    raise SystemExit("TV DirectLink1: AndroidManifest.xml missing")

s = screen_path.read_text()
marker = "WUDROID_TV_DIRECT_LINK1"
if marker in s:
    print("Wudroid TV DirectLink1 already applied")
    raise SystemExit(0)

required = [
    "WUDROID_TV_MODE_TEST1",
    "WUDROID_TV_MODE_TEST1_RUNTIMEFIX1",
    "WudroidTvPickerDialog(",
    "tvOutputActive = wudroidTvActive",
    "WudroidMotionWiimoteOverlay(controllerIndex = 0)",
]
missing = [x for x in required if x not in s]
if missing:
    raise SystemExit("TV DirectLink1: required TV Test1 base missing: " + ", ".join(missing))


def ensure_import(text: str, imp: str) -> str:
    line = imp + "\n"
    if line in text:
        return text
    return text.replace("package info.cemu.cemu.emulation\n", "package info.cemu.cemu.emulation\n" + line, 1)

for imp in [
    "import info.cemu.cemu.WudroidTvDirectHost",
    "import info.cemu.cemu.WudroidTvReceiverDevice",
    "import androidx.compose.material3.ButtonDefaults",
    "import kotlinx.coroutines.Dispatchers",
    "import kotlinx.coroutines.withContext",
]:
    s = ensure_import(s, imp)

# ---------------------------------------------------------------------------
# Direct receiver state: no Android cast/external-display preselection.
# ---------------------------------------------------------------------------
state_anchor = "    var wudroidTvDisplays by remember { mutableStateOf<List<Display>>(emptyList()) }\n"
if state_anchor not in s:
    raise SystemExit("TV DirectLink1: TV display state anchor missing")
s = s.replace(
    state_anchor,
    state_anchor + '''    var wudroidTvReceivers by remember { mutableStateOf<List<WudroidTvReceiverDevice>>(emptyList()) } // WUDROID_TV_DIRECT_LINK1\n    var wudroidTvScanning by remember { mutableStateOf(false) }\n    var wudroidTvConnectedName by remember { mutableStateOf<String?>(null) }\n''',
    1,
)

# RuntimeFix1 stop() assumes the TV owns Cemu's main Surface. DirectLink does
# NOT move Cemu's renderer: the multiplayer PixelCopy source stays alive on the
# phone and is encoded to the TV receiver. Replace stop() with transport-safe
# cleanup while leaving the old external-display start function unused.
stop_re = re.compile(
    r'''    // WUDROID_TV_MODE_TEST1_RUNTIMEFIX1\n    fun stopWudroidTvMode\(\) \{.*?\n    \}\n\n    fun startWudroidTvMode\(mode: String, display: Display\) \{''',
    re.S,
)
stop_new = '''    // WUDROID_TV_MODE_TEST1_RUNTIMEFIX1\n    // WUDROID_TV_DIRECT_LINK1: the phone keeps the Cemu main Surface alive\n    // because the existing LAN H.264 encoder captures it with PixelCopy.\n    fun stopWudroidTvMode() {\n        WudroidTvDirectHost.disconnect()\n        wudroidTvConnectedName = null\n        runCatching { wudroidTvPresentation?.dismiss() }\n        wudroidTvPresentation = null\n        wudroidTvActive = false\n        wudroidTvSelectedDisplayId = -1\n        if (wudroidTvPreviousControllerType >= 0) {\n            runCatching { NativeInput.setControllerType(0, wudroidTvPreviousControllerType) }\n            wudroidTvPreviousControllerType = -1\n        }\n        (wudroidQuickStateContext as? Activity)?.requestedOrientation = ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED\n        setMotionSensorEnabled(sideMenuState.isMotionEnabled)\n    }\n\n    fun startWudroidTvMode(mode: String, display: Display) {'''
s, n = stop_re.subn(stop_new, s, count=1)
if n != 1:
    raise SystemExit("TV DirectLink1: RuntimeFix1 stop block not found")

# Add direct start + scan helpers before the old display polling effect.
effect_anchor = "    LaunchedEffect(showWudroidTvPickerDialog, wudroidTvActive) {\n"
if effect_anchor not in s:
    raise SystemExit("TV DirectLink1: old display polling effect missing")
helpers = r'''    fun scanWudroidTvReceivers() {
        if (wudroidTvScanning) return
        wudroidTvScanning = true
        scope.launch {
            val found = withContext(Dispatchers.IO) {
                WudroidTvDirectHost.scanReceivers(1400)
            }
            wudroidTvReceivers = found
            wudroidTvScanning = false
        }
    }

    fun startWudroidTvDirectMode(mode: String, device: WudroidTvReceiverDevice) {
        runCatching { wudroidTvPresentation?.dismiss() }
        wudroidTvPresentation = null

        if (mode == "MOTION") {
            if (wudroidTvPreviousControllerType < 0) {
                wudroidTvPreviousControllerType = runCatching { NativeInput.getControllerType(0) }
                    .getOrDefault(NativeInput.EmulatedControllerType.WIIMOTE)
            }
            runCatching { NativeInput.setControllerType(0, NativeInput.EmulatedControllerType.WIIMOTE) }
            setMotionSensorEnabled(true)
            (wudroidQuickStateContext as? Activity)?.requestedOrientation = ActivityInfo.SCREEN_ORIENTATION_PORTRAIT
        } else {
            if (wudroidTvPreviousControllerType >= 0) {
                runCatching { NativeInput.setControllerType(0, wudroidTvPreviousControllerType) }
                wudroidTvPreviousControllerType = -1
            }
            (wudroidQuickStateContext as? Activity)?.requestedOrientation = ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED
            setMotionSensorEnabled(sideMenuState.isMotionEnabled)
        }

        wudroidTvMode = mode
        wudroidTvActive = true
        wudroidTvConnectedName = device.name
        showWudroidTvPickerDialog = false
        WudroidTvDirectHost.connect(device)
        scope.launch {
            snackbarHostState.showSnackbar("Transmitindo para ${device.name}")
        }
    }

'''
s = s.replace(effect_anchor, helpers + effect_anchor, 1)

# Replace old DisplayManager polling. It would instantly disconnect DirectLink
# because there is deliberately no Android presentation display.
effect_re = re.compile(
    r'''    LaunchedEffect\(showWudroidTvPickerDialog, wudroidTvActive\) \{.*?\n    \}\n\n    DisposableEffect\(Unit\) \{''',
    re.S,
)
effect_new = '''    LaunchedEffect(showWudroidTvPickerDialog) {\n        if (showWudroidTvPickerDialog) {\n            scanWudroidTvReceivers()\n        }\n    }\n\n    DisposableEffect(Unit) {'''
s, n = effect_re.subn(effect_new, s, count=1)
if n != 1:
    raise SystemExit("TV DirectLink1: display polling block not found")

# The TV Test1 surface branch previously REMOVED MainSurface because the Cemu
# framebuffer was attached to an Android Presentation. DirectLink needs
# MainSurface alive for PixelCopy. Keep it rendered underneath; VPAD gets its
# PadSurface on top. Wii/Motion gets an opaque controller backdrop later.
old_surface_branch = '''    if (tvOutputActive) {\n        // Main/TV Surface is owned by WudroidTvPresentation now.\n        // VPAD keeps the Wii U GamePad framebuffer on the phone; Wii/Motion\n        // leaves only the touch controller visible over a dark background.\n        Box(modifier = Modifier.fillMaxSize().background(Color(0xFF0B0E12))) {\n            if (tvOutputShowPad) {\n                PadSurface(Modifier.fillMaxSize())\n            }\n        }\n        return\n    }\n'''
new_surface_branch = '''    if (tvOutputActive) {\n        // WUDROID_TV_DIRECT_LINK1: keep the TV framebuffer alive as the H.264\n        // capture source. For VPAD, put the real GamePad framebuffer on top.\n        Box(modifier = Modifier.fillMaxSize().background(Color(0xFF0B0E12))) {\n            MainSurface(Modifier.fillMaxSize())\n            if (tvOutputShowPad) {\n                PadSurface(Modifier.fillMaxSize())\n            }\n        }\n        return\n    }\n'''
if old_surface_branch not in s:
    raise SystemExit("TV DirectLink1: TV Test1 surface branch missing")
s = s.replace(old_surface_branch, new_surface_branch, 1)

# For Wii/Motion, hide the still-running capture Surface with an opaque Compose
# layer. The touch controller is drawn after the cover, so the phone becomes a
# controller while PixelCopy continues reading the real game SurfaceView.
overlay_anchor = '''        if (wudroidTvActive && wudroidTvMode == "MOTION") {\n            WudroidMotionWiimoteOverlay(controllerIndex = 0)\n        } else if (wudroidUsesUnifiedTouchOverlay) {\n'''
if overlay_anchor not in s:
    raise SystemExit("TV DirectLink1: motion/unified overlay anchor missing")
overlay_new = '''        if (wudroidTvActive &&\n            (wudroidTvMode == "MOTION" ||\n                wudroidPlayer1ControllerType == NativeInput.EmulatedControllerType.WIIMOTE)\n        ) {\n            Box(Modifier.fillMaxSize().background(Color(0xFF0B0E12)))\n        }\n\n        if (wudroidTvActive && wudroidTvMode == "MOTION") {\n            WudroidMotionWiimoteOverlay(controllerIndex = 0)\n        } else if (wudroidUsesUnifiedTouchOverlay) {\n'''
s = s.replace(overlay_anchor, overlay_new, 1)

# Active cast bubble: when already connected, the TV menu becomes a compact
# session card with only "Parar transmissão", matching the user's flow.
call_anchor = '''        WudroidTvModeDialog(
            isActive = wudroidTvActive,
'''
if call_anchor not in s:
    raise SystemExit("TV DirectLink1: mode dialog call anchor missing")
s = s.replace(
    call_anchor,
    '''        WudroidTvModeDialog(
            isActive = wudroidTvActive,
            connectedName = wudroidTvConnectedName,
''',
    1,
)

sig_anchor = '''private fun WudroidTvModeDialog(
    isActive: Boolean,
'''
if sig_anchor not in s:
    raise SystemExit("TV DirectLink1: mode dialog signature anchor missing")
s = s.replace(
    sig_anchor,
    '''private fun WudroidTvModeDialog(
    isActive: Boolean,
    connectedName: String?,
''',
    1,
)

old_mode_body = '''            Column {
                Text(
                    "Escolha como o celular vai funcionar enquanto o jogo fica na TV.",
                    color = WudroidDrawerMuted,
                    fontSize = 13.sp,
                )
                Row(
                    modifier = Modifier.fillMaxWidth().padding(top = 18.dp),
                    horizontalArrangement = Arrangement.spacedBy(14.dp),
                ) {
                    Surface(
                        modifier = Modifier.weight(1f).heightIn(min = 112.dp).clickable(onClick = onGame),
                        color = WudroidDrawerSurface,
                        shape = RoundedCornerShape(20.dp),
                        border = BorderStroke(1.dp, WudroidDrawerOutline),
                    ) {
                        Column(Modifier.padding(16.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                            Text("Game", color = WudroidCyan, fontWeight = FontWeight.Bold, fontSize = 23.sp)
                            Text("Wii ou GamePad", color = WudroidDrawerMuted, fontSize = 11.sp)
                        }
                    }
                    Surface(
                        modifier = Modifier.weight(1f).heightIn(min = 112.dp).clickable(onClick = onMotion),
                        color = WudroidDrawerSurface,
                        shape = RoundedCornerShape(20.dp),
                        border = BorderStroke(1.dp, WudroidDrawerOutline),
                    ) {
                        Column(Modifier.padding(16.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                            Text("Motion Game", color = Color(0xFF45D28B), fontWeight = FontWeight.Bold, fontSize = 20.sp)
                            Text("Wii Remote + sensores", color = WudroidDrawerMuted, fontSize = 11.sp)
                        }
                    }
                }
                if (isActive) {
                    TextButton(onClick = onDisconnect, modifier = Modifier.align(Alignment.End).padding(top = 8.dp)) {
                        Text("Parar transmissão", color = Color(0xFFFF7777))
                    }
                }
            }
'''
new_mode_body = '''            Column {
                if (isActive) {
                    Surface(
                        modifier = Modifier.fillMaxWidth(),
                        color = WudroidDrawerSurface,
                        shape = RoundedCornerShape(18.dp),
                        border = BorderStroke(1.dp, WudroidDrawerOutline),
                    ) {
                        Column(Modifier.padding(16.dp)) {
                            Text(
                                "Transmitindo para ${connectedName ?: "Wudroid TV"}",
                                color = WudroidCyan,
                                fontWeight = FontWeight.Bold,
                                fontSize = 17.sp,
                            )
                            Text(
                                "O celular continua como controle.",
                                color = WudroidDrawerMuted,
                                fontSize = 12.sp,
                                modifier = Modifier.padding(top = 4.dp),
                            )
                            Button(
                                onClick = onDisconnect,
                                modifier = Modifier.align(Alignment.End).padding(top = 14.dp),
                                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF5A2328)),
                            ) {
                                Text("Parar transmissão", color = Color.White)
                            }
                        }
                    }
                } else {
                    Text(
                        "Escolha como o celular vai funcionar enquanto o jogo fica na TV.",
                        color = WudroidDrawerMuted,
                        fontSize = 13.sp,
                    )
                    Row(
                        modifier = Modifier.fillMaxWidth().padding(top = 18.dp),
                        horizontalArrangement = Arrangement.spacedBy(14.dp),
                    ) {
                        Surface(
                            modifier = Modifier.weight(1f).heightIn(min = 112.dp).clickable(onClick = onGame),
                            color = WudroidDrawerSurface,
                            shape = RoundedCornerShape(20.dp),
                            border = BorderStroke(1.dp, WudroidDrawerOutline),
                        ) {
                            Column(Modifier.padding(16.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                                Text("Game", color = WudroidCyan, fontWeight = FontWeight.Bold, fontSize = 23.sp)
                                Text("Wii ou GamePad", color = WudroidDrawerMuted, fontSize = 11.sp)
                            }
                        }
                        Surface(
                            modifier = Modifier.weight(1f).heightIn(min = 112.dp).clickable(onClick = onMotion),
                            color = WudroidDrawerSurface,
                            shape = RoundedCornerShape(20.dp),
                            border = BorderStroke(1.dp, WudroidDrawerOutline),
                        ) {
                            Column(Modifier.padding(16.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                                Text("Motion Game", color = Color(0xFF45D28B), fontWeight = FontWeight.Bold, fontSize = 20.sp)
                                Text("Wii Remote + sensores", color = WudroidDrawerMuted, fontSize = 11.sp)
                            }
                        }
                    }
                }
            }
'''
if old_mode_body not in s:
    raise SystemExit("TV DirectLink1: mode dialog body not found")
s = s.replace(old_mode_body, new_mode_body, 1)

# Replace picker invocation: in-app LAN discovery, no Settings.ACTION_CAST_SETTINGS.
old_picker_call = re.compile(
    r'''    if \(showWudroidTvPickerDialog\) \{\n        WudroidTvPickerDialog\(\n            displays = wudroidTvDisplays,.*?\n        \)\n    \}\n''',
    re.S,
)
new_picker_call = '''    if (showWudroidTvPickerDialog) {\n        WudroidTvPickerDialog(\n            receivers = wudroidTvReceivers,\n            scanning = wudroidTvScanning,\n            onChoose = { device ->\n                startWudroidTvDirectMode(wudroidTvMode ?: "GAME", device)\n            },\n            onRefresh = { scanWudroidTvReceivers() },\n            onDismiss = { showWudroidTvPickerDialog = false },\n        )\n    }\n'''
s, n = old_picker_call.subn(new_picker_call, s, count=1)
if n != 1:
    raise SystemExit("TV DirectLink1: old TV picker call not found")

# Replace the picker composable only; keep the Game/Motion menu unchanged.
picker_re = re.compile(
    r'''@Composable\nprivate fun WudroidTvPickerDialog\(.*?\n\}\n\n(?=@Composable\nprivate fun EmulationQuitConfirmationDialog)''',
    re.S,
)
picker_ui = r'''@Composable
private fun WudroidTvPickerDialog(
    receivers: List<WudroidTvReceiverDevice>,
    scanning: Boolean,
    onChoose: (WudroidTvReceiverDevice) -> Unit,
    onRefresh: () -> Unit,
    onDismiss: () -> Unit,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = WudroidDrawerBackground,
        shape = RoundedCornerShape(26.dp),
        title = { Text("Escolha a TV", color = WudroidDrawerText, fontWeight = FontWeight.Bold) },
        text = {
            Column {
                if (receivers.isEmpty()) {
                    Text(
                        if (scanning)
                            "Procurando Wudroid TV na rede…"
                        else
                            "Nenhum receptor apareceu. Abra o Wudroid TV Receiver na TV e toque em Procurar novamente.",
                        color = WudroidDrawerMuted,
                        fontSize = 13.sp,
                    )
                } else {
                    receivers.forEach { device ->
                        Surface(
                            modifier = Modifier.fillMaxWidth().padding(vertical = 5.dp).clickable { onChoose(device) },
                            color = WudroidDrawerSurface,
                            shape = RoundedCornerShape(16.dp),
                            border = BorderStroke(1.dp, WudroidDrawerOutline),
                        ) {
                            Column(Modifier.padding(14.dp)) {
                                Text(device.name, color = WudroidDrawerText, fontWeight = FontWeight.Bold)
                                Text(device.address, color = WudroidDrawerMuted, fontSize = 11.sp)
                            }
                        }
                    }
                }
            }
        },
        confirmButton = {
            TextButton(enabled = !scanning, onClick = onRefresh) {
                Text(if (scanning) "Procurando…" else "Procurar novamente", color = WudroidCyan)
            }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancelar") } },
    )
}

'''
s, n = picker_re.subn(picker_ui, s, count=1)
if n != 1:
    raise SystemExit("TV DirectLink1: picker composable block not found")

# Make the active TV menu wording match a streaming session rather than an
# Android external display. Existing Disconnect action now stops DirectLink.
s = s.replace('Text("Desconectar TV", color = Color(0xFFFF7777))',
              'Text("Parar transmissão", color = Color(0xFFFF7777))', 1)

# Verification.
checks = [
    marker,
    "WudroidTvDirectHost.scanReceivers",
    "startWudroidTvDirectMode",
    "WudroidTvDirectHost.connect(device)",
    "MainSurface(Modifier.fillMaxSize())",
    "Parar transmissão",
    "receivers: List<WudroidTvReceiverDevice>",
]
missing = [x for x in checks if x not in s]
if missing:
    raise SystemExit("TV DirectLink1 verification failed: " + ", ".join(missing))

screen_path.write_text(s)

# ---------------------------------------------------------------------------
# Register a TV launcher activity in the SAME APK. On Android TV/Google TV the
# app can be opened as "Wudroid TV Receiver" and becomes discoverable by phone.
# ---------------------------------------------------------------------------
m = manifest_path.read_text()
if "WUDROID_TV_DIRECT_LINK1_RECEIVER" not in m:
    if "</application>" not in m:
        raise SystemExit("TV DirectLink1: application closing tag missing")

    activity = r'''
        <!-- WUDROID_TV_DIRECT_LINK1_RECEIVER -->
        <activity
            android:name=".WudroidTvReceiverActivity"
            android:exported="true"
            android:label="Wudroid TV Receiver"
            android:banner="@mipmap/ic_launcher"
            android:screenOrientation="sensorLandscape">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LEANBACK_LAUNCHER" />
            </intent-filter>
        </activity>
'''
    m = m.replace("    </application>", activity + "    </application>", 1)

    if "android.software.leanback" not in m:
        insert = '''\n    <uses-feature\n        android:name="android.software.leanback"\n        android:required="false" />\n'''
        m = m.replace("    <application", insert + "\n    <application", 1)

manifest_path.write_text(m)

print("Wudroid 0.1.2TV Test2 DirectLink1 applied")
print("- TV picker now discovers Wudroid receivers directly on LAN")
print("- reuses multiplayer H.264/UDP encoder instead of Android screen cast")
print("- same APK contains an Android TV/Google TV receiver activity")
print("- Wii/Motion phone surface is hidden while PixelCopy keeps capturing")
print("- VPAD keeps the GamePad surface on top while TV stream uses main surface")
