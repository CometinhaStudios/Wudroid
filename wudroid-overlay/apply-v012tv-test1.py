#!/usr/bin/env python3
from pathlib import Path
import re

screen_path = Path("cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationScreen.kt")
if not screen_path.exists():
    raise SystemExit("TV Test1: EmulationScreen.kt missing")

s = screen_path.read_text()
marker = "WUDROID_TV_MODE_TEST1"
if marker in s:
    print("Wudroid 0.1.2TV Test1 already applied")
    raise SystemExit(0)

required_before = [
    "WUDROID_LAYOUT14_RUNTIMEFIX1",
    "WUDROID_LAYOUT14_RUNTIMEFIX2",
    'text = "WUDROID"',
    'text = "Menu rápido"',
    "wudroidMainSurfaceView",
]
missing = [x for x in required_before if x not in s]
if missing:
    raise SystemExit("TV Test1: required current base missing: " + ", ".join(missing))


def ensure_import(text: str, imp: str) -> str:
    if imp in text:
        return text
    return text.replace("package info.cemu.cemu.emulation\n", "package info.cemu.cemu.emulation\n" + imp + "\n", 1)

for imp in [
    "import android.app.Activity",
    "import android.content.Intent",
    "import android.content.pm.ActivityInfo",
    "import android.hardware.display.DisplayManager",
    "import android.provider.Settings",
    "import android.view.Display",
    "import androidx.compose.foundation.BorderStroke",
    "import androidx.compose.foundation.layout.size",
    "import androidx.compose.material3.IconButton",
    "import androidx.compose.material3.Surface",
    "import androidx.compose.runtime.DisposableEffect",
    "import androidx.compose.ui.graphics.Color",
    "import androidx.compose.ui.unit.dp",
    "import kotlinx.coroutines.delay",
]:
    s = ensure_import(s, imp)

# ---------------------------------------------------------------------------
# State and runtime bridge.
# ---------------------------------------------------------------------------
state_anchor = "    val wudroidQuickStateContext = LocalContext.current // WUDROID_QUICKSTATE_ENGINE_TEST10\n"
if state_anchor not in s:
    raise SystemExit("TV Test1: QuickState context anchor missing")
state_block = state_anchor + '''    var showWudroidTvModeDialog by remember { mutableStateOf(false) } // WUDROID_TV_MODE_TEST1
    var showWudroidTvPickerDialog by remember { mutableStateOf(false) }
    var wudroidTvMode by rememberSaveable { mutableStateOf<String?>(null) }
    var wudroidTvActive by rememberSaveable { mutableStateOf(false) }
    var wudroidTvSelectedDisplayId by rememberSaveable { mutableStateOf(-1) }
    var wudroidTvPresentation by remember { mutableStateOf<WudroidTvPresentation?>(null) }
    var wudroidTvPreviousControllerType by rememberSaveable { mutableStateOf(-1) }
    var wudroidTvDisplays by remember { mutableStateOf<List<Display>>(emptyList()) }
    val wudroidTvDisplayManager = remember {
        wudroidQuickStateContext.getSystemService(android.content.Context.DISPLAY_SERVICE) as DisplayManager
    }
'''
s = s.replace(state_anchor, state_block, 1)

settings_anchor_candidates = [
    "    val inputOverlaySettings by viewModel.inputOverlaySettings.collectAsState()\n",
    "    val inputOverlaySettings by viewModel.inputOverlaySettings.collectAsState()\r\n",
]
settings_anchor = next((a for a in settings_anchor_candidates if a in s), None)
if settings_anchor is None:
    raise SystemExit("TV Test1: inputOverlaySettings anchor missing")

helpers = r'''
    val wudroidTvControllerType = runCatching {
        NativeInput.getControllerType(0)
    }.getOrDefault(NativeInput.EmulatedControllerType.VPAD)

    fun stopWudroidTvMode() {
        runCatching { wudroidTvPresentation?.dismiss() }
        wudroidTvPresentation = null
        wudroidTvActive = false
        wudroidTvSelectedDisplayId = -1
        if (wudroidTvPreviousControllerType >= 0) {
            runCatching { NativeInput.setControllerType(0, wudroidTvPreviousControllerType) }
            wudroidTvPreviousControllerType = -1
        }
        (wudroidQuickStateContext as? Activity)?.requestedOrientation = ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED
        setMotionSensorEnabled(sideMenuState.isMotionEnabled)
    }

    fun startWudroidTvMode(mode: String, display: Display) {
        runCatching { wudroidTvPresentation?.dismiss() }
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
        wudroidTvSelectedDisplayId = display.displayId
        wudroidTvActive = true
        showWudroidTvPickerDialog = false

        val presentation = WudroidTvPresentation(
            wudroidQuickStateContext,
            display,
            viewModel.mainHolderCallback,
        )
        wudroidTvPresentation = presentation
        scope.launch {
            // Give Compose one frame to remove the phone TV Surface before
            // attaching Cemu's main framebuffer to the external display.
            delay(180)
            runCatching { presentation.show() }.onFailure {
                stopWudroidTvMode()
                snackbarHostState.showSnackbar("Não foi possível abrir a TV selecionada")
            }
        }
    }

    LaunchedEffect(showWudroidTvPickerDialog, wudroidTvActive) {
        while (showWudroidTvPickerDialog || wudroidTvActive) {
            wudroidTvDisplays = wudroidTvDisplayManager
                .getDisplays(DisplayManager.DISPLAY_CATEGORY_PRESENTATION)
                .toList()
            if (wudroidTvActive && wudroidTvSelectedDisplayId >= 0 &&
                wudroidTvDisplays.none { it.displayId == wudroidTvSelectedDisplayId }
            ) {
                stopWudroidTvMode()
                snackbarHostState.showSnackbar("TV desconectada")
            }
            delay(850)
        }
    }

    DisposableEffect(Unit) {
        onDispose {
            runCatching { wudroidTvPresentation?.dismiss() }
        }
    }
'''
s = s.replace(settings_anchor, settings_anchor + helpers, 1)

# ---------------------------------------------------------------------------
# Cast icon in the top-right of the existing Wudroid drawer header.
# ---------------------------------------------------------------------------
header_re = re.compile(r'''                Column\(\n                    modifier = Modifier\n                        \.fillMaxWidth\(\)\n                        \.padding\(horizontal = 10\.dp, vertical = 12\.dp\),\n                \) \{\n                    Text\(\n                        text = "WUDROID",\n                        color = WudroidCyan,\n                        fontSize = 20\.sp,\n                        fontWeight = FontWeight\.Bold,\n                    \)\n                    Text\(\n                        text = "Menu rápido",\n                        color = WudroidDrawerMuted,\n                        fontSize = 12\.sp,\n                    \)\n                \}\n''')
header_new = '''                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 10.dp, vertical = 12.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = "WUDROID",
                            color = WudroidCyan,
                            fontSize = 20.sp,
                            fontWeight = FontWeight.Bold,
                        )
                        Text(
                            text = "Menu rápido",
                            color = WudroidDrawerMuted,
                            fontSize = 12.sp,
                        )
                    }
                    IconButton(
                        onClick = { showWudroidTvModeDialog = true },
                        modifier = Modifier.size(58.dp),
                    ) {
                        Icon(
                            painter = painterResource(id = R.drawable.ic_wudroid_cast),
                            contentDescription = "Jogar na TV",
                            tint = Color.Unspecified,
                            modifier = Modifier.size(46.dp),
                        )
                    }
                } // WUDROID_TV_MODE_TEST1
'''
s, count = header_re.subn(header_new, s, count=1)
if count != 1:
    raise SystemExit("TV Test1: WUDROID/Menu rápido header block not found")

# ---------------------------------------------------------------------------
# Phone display behavior while the main TV framebuffer is on the TV.
# ---------------------------------------------------------------------------
call_anchor = "            onMainSurfaceViewReady = { wudroidMainSurfaceView = it },\n"
if call_anchor not in s:
    raise SystemExit("TV Test1: EmulationSurfaces SaveStation call anchor missing")
s = s.replace(
    call_anchor,
    call_anchor + '''            tvOutputActive = wudroidTvActive,
            tvOutputShowPad = wudroidTvActive && wudroidTvMode == "GAME" &&
                wudroidTvControllerType == NativeInput.EmulatedControllerType.VPAD,
''',
    1,
)

sig_anchor = '''    onInitializeEmulation: () -> Unit,
    onMainSurfaceViewReady: (SurfaceView) -> Unit,
) {
'''
if sig_anchor not in s:
    raise SystemExit("TV Test1: EmulationSurfaces signature anchor missing")
s = s.replace(
    sig_anchor,
    '''    onInitializeEmulation: () -> Unit,
    onMainSurfaceViewReady: (SurfaceView) -> Unit,
    tvOutputActive: Boolean = false,
    tvOutputShowPad: Boolean = false,
) {
''',
    1,
)

layout_anchor = '''    LinearLayout(isVertical) { itemModifier ->
        SurfacesInOrder(itemModifier)
    }
'''
if layout_anchor not in s:
    raise SystemExit("TV Test1: EmulationSurfaces final layout anchor missing")
s = s.replace(
    layout_anchor,
    '''    if (tvOutputActive) {
        // Main/TV Surface is owned by WudroidTvPresentation now.
        // VPAD keeps the Wii U GamePad framebuffer on the phone; Wii/Motion
        // leaves only the touch controller visible over a dark background.
        Box(modifier = Modifier.fillMaxSize().background(Color(0xFF0B0E12))) {
            if (tvOutputShowPad) {
                PadSurface(Modifier.fillMaxSize())
            }
        }
        return
    }

    LinearLayout(isVertical) { itemModifier ->
        SurfacesInOrder(itemModifier)
    }
''',
    1,
)

# Motion mode owns the on-phone Wii overlay and uses literal portrait D-pad mapping.
local_marker = "        if (wudroidUsesUnifiedTouchOverlay) {\n            WudroidLocalControllerOverlay("
if local_marker not in s:
    raise SystemExit("TV Test1: Test19 unified overlay branch missing")
s = s.replace(
    local_marker,
    '''        if (wudroidTvActive && wudroidTvMode == "MOTION") {
            WudroidMotionWiimoteOverlay(controllerIndex = 0)
        } else if (wudroidUsesUnifiedTouchOverlay) {
            WudroidLocalControllerOverlay(''',
    1,
)

# ---------------------------------------------------------------------------
# Dialog calls.
# ---------------------------------------------------------------------------
dialog_anchor = "    EmulationTextInputDialog()\n"
if dialog_anchor not in s:
    raise SystemExit("TV Test1: EmulationTextInputDialog anchor missing")
dialog_calls = r'''    if (showWudroidTvModeDialog) {
        WudroidTvModeDialog(
            isActive = wudroidTvActive,
            onGame = {
                if (wudroidTvActive) stopWudroidTvMode()
                wudroidTvMode = "GAME"
                showWudroidTvModeDialog = false
                showWudroidTvPickerDialog = true
            },
            onMotion = {
                if (wudroidTvActive) stopWudroidTvMode()
                wudroidTvMode = "MOTION"
                showWudroidTvModeDialog = false
                showWudroidTvPickerDialog = true
            },
            onDisconnect = {
                stopWudroidTvMode()
                showWudroidTvModeDialog = false
            },
            onDismiss = { showWudroidTvModeDialog = false },
        )
    }

    if (showWudroidTvPickerDialog) {
        WudroidTvPickerDialog(
            displays = wudroidTvDisplays,
            onChoose = { display ->
                startWudroidTvMode(wudroidTvMode ?: "GAME", display)
            },
            onOpenSystemPicker = {
                val castIntent = Intent(Settings.ACTION_CAST_SETTINGS)
                runCatching { wudroidQuickStateContext.startActivity(castIntent) }
                    .recoverCatching {
                        wudroidQuickStateContext.startActivity(Intent(Settings.ACTION_WIRELESS_SETTINGS))
                    }
            },
            onDismiss = { showWudroidTvPickerDialog = false },
        )
    }

'''
s = s.replace(dialog_anchor, dialog_calls + dialog_anchor, 1)

# ---------------------------------------------------------------------------
# Dialog UI, deliberately matching the dark two-choice Wudroid menu language.
# ---------------------------------------------------------------------------
quit_pos = s.find("@Composable\nprivate fun EmulationQuitConfirmationDialog(")
if quit_pos < 0:
    raise SystemExit("TV Test1: quit function insertion anchor missing")
ui = r'''@Composable
private fun WudroidTvModeDialog(
    isActive: Boolean,
    onGame: () -> Unit,
    onMotion: () -> Unit,
    onDisconnect: () -> Unit,
    onDismiss: () -> Unit,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = WudroidDrawerBackground,
        shape = RoundedCornerShape(26.dp),
        title = {
            Text("Jogar na TV", color = WudroidDrawerText, fontWeight = FontWeight.Bold, fontSize = 24.sp)
        },
        text = {
            Column {
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
                        Text("Desconectar TV", color = Color(0xFFFF7777))
                    }
                }
            }
        },
        confirmButton = {},
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancelar") } },
    )
}

@Composable
private fun WudroidTvPickerDialog(
    displays: List<Display>,
    onChoose: (Display) -> Unit,
    onOpenSystemPicker: () -> Unit,
    onDismiss: () -> Unit,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = WudroidDrawerBackground,
        shape = RoundedCornerShape(26.dp),
        title = { Text("Escolha a TV", color = WudroidDrawerText, fontWeight = FontWeight.Bold) },
        text = {
            Column {
                if (displays.isEmpty()) {
                    Text(
                        "Nenhuma tela externa apareceu ainda. Toque em Procurar TV, conecte pela tela do Android e volte ao Wudroid.",
                        color = WudroidDrawerMuted,
                        fontSize = 13.sp,
                    )
                } else {
                    displays.forEach { display ->
                        Surface(
                            modifier = Modifier.fillMaxWidth().padding(vertical = 5.dp).clickable { onChoose(display) },
                            color = WudroidDrawerSurface,
                            shape = RoundedCornerShape(16.dp),
                            border = BorderStroke(1.dp, WudroidDrawerOutline),
                        ) {
                            Column(Modifier.padding(14.dp)) {
                                Text(display.name, color = WudroidDrawerText, fontWeight = FontWeight.Bold)
                                Text("Tela externa ${display.displayId}", color = WudroidDrawerMuted, fontSize = 11.sp)
                            }
                        }
                    }
                }
            }
        },
        confirmButton = {
            TextButton(onClick = onOpenSystemPicker) { Text("Procurar TV", color = WudroidCyan) }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("Cancelar") } },
    )
}

'''
s = s[:quit_pos] + ui + s[quit_pos:]

# Verification.
checks = [
    marker,
    "R.drawable.ic_wudroid_cast",
    "WudroidTvModeDialog(",
    "WudroidTvPickerDialog(",
    "WudroidTvPresentation(",
    "DisplayManager.DISPLAY_CATEGORY_PRESENTATION",
    "WudroidMotionWiimoteOverlay(controllerIndex = 0)",
    "tvOutputActive = wudroidTvActive",
    'wudroidTvMode == "MOTION"',
]
missing = [x for x in checks if x not in s]
if missing:
    raise SystemExit("TV Test1 verification failed: " + ", ".join(missing))

screen_path.write_text(s)
print("Wudroid 0.1.2TV Test1 applied")
print("- cast icon in top-right of WUDROID quick menu")
print("- Game / Motion Game selector")
print("- Android TV/external-display picker flow")
print("- external TV framebuffer uses a dedicated Presentation SurfaceView")
print("- Wii: phone keeps controller only; VPAD: phone keeps GamePad framebuffer")
print("- Motion Game forces portrait Wii Remote and enables device motion sensor")
