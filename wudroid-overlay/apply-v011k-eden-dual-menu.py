#!/usr/bin/env python3
from pathlib import Path
import re

path = Path("cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationScreen.kt")
if not path.exists():
    raise SystemExit("EmulationScreen.kt not found")

s = path.read_text()
marker = "WUDROID_EDEN_DUAL_MENU_TEST3"
if marker in s:
    print("Wudroid Eden Dual Menu Test3 already applied")
    raise SystemExit(0)

if "WUDROID_SIDEBAR_INTERACTION_TEST2" not in s:
    raise SystemExit("Interaction Test2 must be applied before Eden Dual Menu Test3")

# Imports required by the second (right-side) drawer and quick settings UI.
imports = [
    "import androidx.compose.material3.HorizontalDivider",
    "import androidx.compose.material3.Slider",
    "import androidx.compose.material3.Switch",
    "import androidx.compose.ui.platform.LocalContext",
    "import androidx.compose.runtime.mutableFloatStateOf",
    "import androidx.compose.runtime.mutableIntStateOf",
    "import info.cemu.cemu.nativeinterface.NativeSettings",
]
for imp in imports:
    if imp not in s:
        package = "package info.cemu.cemu.emulation\n"
        s = s.replace(package, package + imp + "\n", 1)

# State: original left drawer + new right Quick Settings drawer + pause state.
state_anchor = "    val drawerState = rememberDrawerState(initialValue = DrawerValue.Closed)\n"
if state_anchor not in s:
    raise SystemExit("drawerState anchor missing")
s = s.replace(
    state_anchor,
    state_anchor
    + "    val quickDrawerState = rememberDrawerState(initialValue = DrawerValue.Closed) // WUDROID_EDEN_DUAL_MENU_TEST3\n"
    + "    var isWudroidPaused by remember { mutableStateOf(false) }\n",
    1,
)

# Remove the old proof/test state.
s = s.replace(
    "    var showWudroidTestDialog by remember { mutableStateOf(false) } // WUDROID_SIDEBAR_INTERACTION_TEST2\n",
    "",
    1,
)

# Drawer helper for the right side.
close_anchor = '''    fun closeDrawer() {
        scope.launch {
            drawerState.close()
        }
    }
'''
if close_anchor not in s:
    raise SystemExit("closeDrawer helper anchor missing")
s = s.replace(
    close_anchor,
    close_anchor + '''
    fun closeQuickDrawer() {
        scope.launch { quickDrawerState.close() }
    }

    fun openQuickDrawer() {
        scope.launch {
            drawerState.close()
            quickDrawerState.open()
        }
    }
''',
    1,
)

# Back: close right, then left, then ask to leave the game.
back_start = s.find("    BackHandler {")
back_end = s.find("    LaunchedEffect(", back_start)
if back_start < 0 or back_end < 0:
    raise SystemExit("BackHandler region missing")
new_back = '''    BackHandler {
        if (drawerState.isAnimationRunning || quickDrawerState.isAnimationRunning) {
            return@BackHandler
        }

        when {
            quickDrawerState.isOpen -> closeQuickDrawer()
            drawerState.isOpen -> closeDrawer()
            else -> showQuitConfirmationDialog = true
        }
    }
'''
s = s[:back_start] + new_back + s[back_end:]

# Input should be disabled whenever either in-game menu is open.
old_effect = '''    LaunchedEffect(drawerState.isClosed) {
        setInputListeningEnabled(drawerState.isClosed)
    }
'''
new_effect = '''    LaunchedEffect(drawerState.isClosed, quickDrawerState.isClosed) {
        setInputListeningEnabled(drawerState.isClosed && quickDrawerState.isClosed)
    }
'''
if old_effect not in s:
    raise SystemExit("input-listening LaunchedEffect anchor missing")
s = s.replace(old_effect, new_effect, 1)

# The Test2 callback is removed. Replace it with real Pause and Quick Settings callbacks.
old_test_cb = '''                        onWudroidTest = {
                            showWudroidTestDialog = true
                            closeDrawer()
                        },
'''
if old_test_cb not in s:
    raise SystemExit("old test callback missing")
s = s.replace(
    old_test_cb,
    '''                        isPaused = isWudroidPaused,
                        onPauseToggle = {
                            if (isWudroidPaused) {
                                NativeEmulation.resumeTitle()
                            } else {
                                NativeEmulation.pauseTitle()
                            }
                            isWudroidPaused = !isWudroidPaused
                            closeDrawer()
                        },
                        onQuickSettings = {
                            openQuickDrawer()
                        },
''',
    1,
)

# Replace the original menu content with an Eden-like compact Wudroid menu.
menu_start = s.find("@Composable\nprivate fun EmulationSideMenuContent(")
menu_end = s.find("@Composable\nprivate fun CheckboxItem(", menu_start)
if menu_start < 0 or menu_end < 0:
    raise SystemExit("EmulationSideMenuContent function region missing")

new_menu = r'''@Composable
private fun EmulationSideMenuContent(
    sideMenuState: SideMenuState,
    updateState: (SideMenuState) -> Unit,
    onShowEmulatedUSBDevices: () -> Unit,
    onEditInputOverlay: () -> Unit,
    onResetInputOverlay: () -> Unit,
    isPaused: Boolean,
    onPauseToggle: () -> Unit,
    onQuickSettings: () -> Unit,
    onQuit: () -> Unit,
) {
    TextButtonItem(
        label = if (isPaused) "Retomar emulação" else "Pausar emulação",
        onClick = onPauseToggle,
    )
    TextButtonItem(
        label = if (sideMenuState.isInputOverlayVisible) "Ocultar controle" else "Mostrar controle",
        onClick = { updateState(sideMenuState.copy(isInputOverlayVisible = !sideMenuState.isInputOverlayVisible)) },
    )
    TextButtonItem(
        label = "Quick Settings",
        onClick = onQuickSettings,
    )
    TextButtonItem(
        label = "Controles",
        enabled = sideMenuState.isInputOverlayVisible,
        onClick = onEditInputOverlay,
    )
    TextButtonItem(
        label = tr("Emulated USB Devices"),
        onClick = onShowEmulatedUSBDevices,
    )

    Text(
        text = "Recursos Wii U",
        color = WudroidCyan,
        fontWeight = FontWeight.Bold,
        fontSize = 12.sp,
        modifier = Modifier.padding(start = 12.dp, top = 12.dp, bottom = 4.dp),
    )
    CheckboxItem(
        label = tr("Enable motion"),
        checked = sideMenuState.isMotionEnabled,
        onCheckedChange = { updateState(sideMenuState.copy(isMotionEnabled = it)) },
    )
    CheckboxItem(
        label = tr("Replace TV with PAD"),
        checked = sideMenuState.isTVReplacedWithPad,
        onCheckedChange = { updateState(sideMenuState.copy(isTVReplacedWithPad = it)) },
    )
    CheckboxItem(
        label = tr("Show PAD"),
        checked = sideMenuState.isPadVisible,
        onCheckedChange = { updateState(sideMenuState.copy(isPadVisible = it)) },
    )
    TextButtonItem(
        label = tr("Reset input overlay"),
        enabled = sideMenuState.isInputOverlayVisible,
        onClick = onResetInputOverlay,
    )

    HorizontalDivider(
        color = WudroidDrawerOutline,
        modifier = Modifier.padding(vertical = 8.dp),
    )
    TextButtonItem(
        label = "Sair da emulação",
        onClick = onQuit,
    )
}

'''
s = s[:menu_start] + new_menu + s[menu_end:]

# Remove old Test2 dialog invocation.
s = re.sub(
    r'''\n    if \(showWudroidTestDialog\) \{\n        WudroidTestDialog\(\n            onDismiss = \{ showWudroidTestDialog = false \},\n        \)\n    \}\n''',
    "\n",
    s,
    count=1,
)

# Remove old Test2 dialog composable if present.
test_fn_start = s.find("@Composable\nprivate fun WudroidTestDialog(")
if test_fn_start >= 0:
    loading_start = s.find("@Composable\nprivate fun EmulationLoadingDialog()", test_fn_start)
    if loading_start < 0:
        raise SystemExit("Could not remove WudroidTestDialog cleanly")
    s = s[:test_fn_start] + s[loading_start:]

# Create a true right-side drawer by making Material's start edge RTL.
main_drawer_anchor = "    ModalNavigationDrawer(\n"
main_drawer_pos = s.find(main_drawer_anchor)
if main_drawer_pos < 0:
    raise SystemExit("main ModalNavigationDrawer anchor missing")

right_open = '''    // WUDROID_EDEN_DUAL_MENU_TEST3: outer RTL drawer = right-side Quick Settings.
    CompositionLocalProvider(LocalLayoutDirection provides LayoutDirection.Rtl) {
        ModalNavigationDrawer(
            drawerState = quickDrawerState,
            gesturesEnabled = true,
            drawerContent = {
                CompositionLocalProvider(LocalLayoutDirection provides LayoutDirection.Ltr) {
                    ModalDrawerSheet(
                        drawerContainerColor = WudroidDrawerBackground,
                        drawerContentColor = WudroidDrawerText,
                    ) {
                        WudroidQuickSettingsContent(
                            onClose = { closeQuickDrawer() },
                        )
                    }
                }
            },
        ) {
            CompositionLocalProvider(LocalLayoutDirection provides LayoutDirection.Ltr) {
'''
s = s[:main_drawer_pos] + right_open + s[main_drawer_pos:]

# Close the new right drawer wrappers immediately after the original left drawer.
post_drawer_anchor = "    Box(modifier = Modifier.fillMaxSize()) {\n"
post_pos = s.find(post_drawer_anchor)
if post_pos < 0:
    raise SystemExit("post-drawer Box anchor missing")
s = s[:post_pos] + "            }\n        }\n    }\n" + s[post_pos:]

# Right-side Quick Settings. TV Mode from the Switch reference is intentionally NOT included.
quick_settings = r'''@Composable
private fun WudroidQuickSettingsContent(onClose: () -> Unit) {
    var asyncShaders by remember {
        mutableStateOf(runCatching { NativeSettings.getAsyncShaderCompile() }.getOrDefault(true))
    }
    var accurateBarriers by remember {
        mutableStateOf(runCatching { NativeSettings.getAccurateBarriers() }.getOrDefault(false))
    }
    var vsync by remember {
        mutableIntStateOf(runCatching { NativeSettings.getVsyncMode() }.getOrDefault(1))
    }
    var scalingFilter by remember {
        mutableIntStateOf(runCatching { NativeSettings.getUpscalingFilter() }.getOrDefault(0))
    }
    var speedPercent by remember { mutableFloatStateOf(100f) }

    fun saveNativeSettings() {
        runCatching { NativeSettings.saveSettings() }
    }

    fun gpuModeLabel(): String = when {
        asyncShaders && !accurateBarriers -> "Fast"
        asyncShaders && accurateBarriers -> "Balanced"
        else -> "Accurate"
    }

    fun cycleGpuMode() {
        when (gpuModeLabel()) {
            "Fast" -> {
                asyncShaders = true
                accurateBarriers = true
            }
            "Balanced" -> {
                asyncShaders = false
                accurateBarriers = true
            }
            else -> {
                asyncShaders = true
                accurateBarriers = false
            }
        }
        runCatching {
            NativeSettings.setAsyncShaderCompile(asyncShaders)
            NativeSettings.setAccurateBarriers(accurateBarriers)
            NativeSettings.saveSettings()
        }
    }

    fun scalingLabel(): String = when (scalingFilter) {
        3 -> "Nearest Neighbor"
        1 -> "Bicubic"
        2 -> "Bicubic Hermite"
        else -> "Bilinear"
    }

    fun cycleScaling() {
        scalingFilter = when (scalingFilter) {
            3 -> 0
            0 -> 1
            1 -> 2
            else -> 3
        }
        runCatching {
            NativeSettings.setUpscalingFilter(scalingFilter)
            NativeSettings.saveSettings()
        }
    }

    Column(
        modifier = Modifier
            .width(360.dp)
            .padding(horizontal = 14.dp, vertical = 12.dp)
            .verticalScroll(rememberScrollState()),
    ) {
        Text(
            text = "Quick Settings",
            color = WudroidCyan,
            fontSize = 20.sp,
            fontWeight = FontWeight.Bold,
        )
        Text(
            text = "Wudroid • ajustes durante o jogo",
            color = WudroidDrawerMuted,
            fontSize = 12.sp,
            modifier = Modifier.padding(bottom = 12.dp),
        )

        QuickToggleRow(
            title = "Turbo speed",
            checked = false,
            enabled = false,
            subtitle = "Aguardando hook nativo de velocidade do Cemu",
            onCheckedChange = {},
        )
        QuickToggleRow(
            title = "Slow speed",
            checked = false,
            enabled = false,
            subtitle = "Aguardando hook nativo de velocidade do Cemu",
            onCheckedChange = {},
        )
        QuickToggleRow(
            title = "Limite de velocidade",
            checked = true,
            enabled = false,
            subtitle = "Interface pronta; controle do core entra no próximo teste",
            onCheckedChange = {},
        )

        Text(
            text = "Porcentagem do limite de velocidade",
            color = WudroidDrawerText.copy(alpha = 0.55f),
            fontSize = 14.sp,
            modifier = Modifier.padding(top = 8.dp),
        )
        Text(
            text = "${speedPercent.toInt()}%",
            color = WudroidDrawerMuted,
            fontSize = 12.sp,
        )
        Slider(
            value = speedPercent,
            onValueChange = { speedPercent = it },
            valueRange = 25f..300f,
            enabled = false,
        )

        HorizontalDivider(color = WudroidDrawerOutline, modifier = Modifier.padding(vertical = 8.dp))

        QuickValueRow(
            title = "GPU Mode",
            value = gpuModeLabel(),
            subtitle = "Fast / Balanced / Accurate",
            onClick = { cycleGpuMode() },
        )
        QuickValueRow(
            title = "Filtro de Adaptação da Janela",
            value = scalingLabel(),
            subtitle = "Toque para trocar",
            onClick = { cycleScaling() },
        )
        QuickValueRow(
            title = "Método de Anti-aliasing",
            value = "Padrão do jogo",
            subtitle = "O Cemu Wii U usa AA do jogo/Graphic Pack",
            enabled = false,
            onClick = {},
        )

        HorizontalDivider(color = WudroidDrawerOutline, modifier = Modifier.padding(vertical = 8.dp))

        QuickToggleRow(
            title = "Async shader compile",
            checked = asyncShaders,
            subtitle = "Compilação assíncrona de shaders",
            onCheckedChange = {
                asyncShaders = it
                runCatching {
                    NativeSettings.setAsyncShaderCompile(it)
                    NativeSettings.saveSettings()
                }
            },
        )
        QuickValueRow(
            title = "VSync",
            value = when (vsync) { 0 -> "Off"; 2 -> "Triple"; else -> "Double" },
            subtitle = "Toque para trocar",
            onClick = {
                vsync = when (vsync) { 0 -> 1; 1 -> 2; else -> 0 }
                runCatching {
                    NativeSettings.setVsyncMode(vsync)
                    NativeSettings.saveSettings()
                }
            },
        )
        QuickToggleRow(
            title = "Accurate barriers",
            checked = accurateBarriers,
            subtitle = "Mais precisão; pode custar desempenho",
            onCheckedChange = {
                accurateBarriers = it
                runCatching {
                    NativeSettings.setAccurateBarriers(it)
                    NativeSettings.saveSettings()
                }
            },
        )

        TextButton(
            onClick = onClose,
            modifier = Modifier.fillMaxWidth().padding(top = 10.dp),
        ) {
            Text("Fechar", color = WudroidCyan, fontWeight = FontWeight.Bold)
        }
    }
}

@Composable
private fun QuickToggleRow(
    title: String,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit,
    subtitle: String? = null,
    enabled: Boolean = true,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .alpha(if (enabled) 1f else 0.55f)
            .padding(vertical = 7.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(modifier = Modifier.weight(1f).padding(end = 10.dp)) {
            Text(title, color = WudroidDrawerText, fontSize = 15.sp)
            subtitle?.let { Text(it, color = WudroidDrawerMuted, fontSize = 11.sp) }
        }
        Switch(
            checked = checked,
            onCheckedChange = onCheckedChange,
            enabled = enabled,
        )
    }
}

@Composable
private fun QuickValueRow(
    title: String,
    value: String,
    onClick: () -> Unit,
    subtitle: String? = null,
    enabled: Boolean = true,
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .alpha(if (enabled) 1f else 0.55f)
            .clickable(enabled = enabled, onClick = onClick)
            .padding(vertical = 9.dp),
    ) {
        Text(title, color = WudroidDrawerText, fontSize = 15.sp)
        Text(value, color = WudroidCyan, fontSize = 13.sp, fontWeight = FontWeight.Bold)
        subtitle?.let { Text(it, color = WudroidDrawerMuted, fontSize = 11.sp) }
    }
}

'''
insert_anchor = "@Composable\nprivate fun EmulationSurfaces("
insert_pos = s.find(insert_anchor)
if insert_pos < 0:
    raise SystemExit("EmulationSurfaces insertion anchor missing")
s = s[:insert_pos] + quick_settings + s[insert_pos:]

# No Switch-only TV Mode in the right Quick Settings menu.
# Wii U's native "Replace TV with PAD" remains on the LEFT because it is a real Wii U feature.

path.write_text(s)

check = path.read_text()
verification = [
    marker,
    "quickDrawerState",
    "LayoutDirection.Rtl",
    'text = "Quick Settings"',
    'title = "Turbo speed"',
    'title = "Slow speed"',
    'title = "GPU Mode"',
    'title = "Filtro de Adaptação da Janela"',
    'title = "Método de Anti-aliasing"',
    'label = "Sair da emulação"',
]
missing = [x for x in verification if x not in check]
if missing:
    raise SystemExit("Eden Dual Menu Test3 verification failed: " + ", ".join(missing))

if 'label = "Função teste"' in check or "WudroidTestDialog" in check:
    raise SystemExit("Old test button/dialog was not fully removed")

# The requested Switch TV Mode must not exist in the new right quick settings.
quick_region = check[check.find("private fun WudroidQuickSettingsContent"):check.find("private fun EmulationSurfaces")]
if 'Modo TV' in quick_region or 'TV Mode' in quick_region:
    raise SystemExit("Switch TV Mode leaked into Wudroid Quick Settings")

print("Wudroid 0.1.1 Eden Dual Menu Test3 applied")
print("- original left in-game drawer kept and redesigned as main menu")
print("- right-side Quick Settings drawer added with RTL start-edge gesture")
print("- old test function removed")
print("- Switch TV Mode omitted")
print("- GPU Mode / scaling / async shaders / VSync / barriers are wired to Cemu settings")
print("- speed controls are visibly disabled until a safe native Cemu speed hook is added")
