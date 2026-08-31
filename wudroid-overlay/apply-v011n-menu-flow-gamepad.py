#!/usr/bin/env python3
from pathlib import Path
import re

screen_path = Path("cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationScreen.kt")
activity_path = Path("cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationActivity.kt")
overlay_path = Path("cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/inputoverlay/InputOverlaySurfaceView.kt")

for p in (screen_path, activity_path, overlay_path):
    if not p.exists():
        raise SystemExit(f"Required source not found: {p}")

screen = screen_path.read_text()
activity = activity_path.read_text()
overlay = overlay_path.read_text()
marker = "WUDROID_MENU_FLOW_GAMEPAD_TEST6"

if marker in screen:
    print("Wudroid Menu Flow + Gamepad Test6 already applied")
    raise SystemExit(0)

if "WUDROID_EDEN_DUAL_MENU_TEST3" not in screen:
    raise SystemExit("Eden Dual Menu Test3 must be applied before Test6")

# ---------------------------------------------------------------------------
# 1) No global swipe while playing. Menus are opened by Back only.
#    This prevents any edge detector from stealing touches from the gamepad.
# ---------------------------------------------------------------------------
activity = re.sub(
    r'''\n    override fun dispatchTouchEvent\(event: MotionEvent\): Boolean \{.*?\n    \}\n(?=\n    private fun configureRightEdgeGestureExclusion\(\))''',
    "\n",
    activity,
    count=1,
    flags=re.S,
)
activity = re.sub(
    r'''\n    private fun configureRightEdgeGestureExclusion\(\) \{.*?\n    \}\n(?=\n    override fun onGenericMotionEvent\(event: MotionEvent\): Boolean \{)''',
    "\n",
    activity,
    count=1,
    flags=re.S,
)
activity = activity.replace("        configureRightEdgeGestureExclusion()\n", "", 1)

# The old token remains harmless at 0 and keeps Test5's compiled API stable,
# but there is no longer any touch listener that can increment it.

# ---------------------------------------------------------------------------
# 2) Back opens the MAIN menu and pauses emulation.
#    Closing the final menu automatically resumes only when the menu caused
#    the pause. Moving left <-> right never resumes in the middle.
# ---------------------------------------------------------------------------
imports = [
    "import androidx.compose.foundation.gestures.detectHorizontalDragGestures",
    "import androidx.compose.ui.input.pointer.pointerInput",
    "import androidx.compose.material3.SwitchDefaults",
]
for imp in imports:
    if imp not in screen:
        screen = screen.replace(
            "package info.cemu.cemu.emulation\n",
            "package info.cemu.cemu.emulation\n" + imp + "\n",
            1,
        )

state_anchor = "    var isWudroidPaused by remember { mutableStateOf(false) }\n"
if state_anchor not in screen:
    raise SystemExit("isWudroidPaused state anchor missing")
state_extra = '''    var isWudroidPaused by remember { mutableStateOf(false) }
    var pausedByMenu by remember { mutableStateOf(false) } // WUDROID_MENU_FLOW_GAMEPAD_TEST6
    var menuTransitionInProgress by remember { mutableStateOf(false) }
    var leftMenuDragX by remember { mutableFloatStateOf(0f) }
    var quickMenuDragX by remember { mutableFloatStateOf(0f) }
'''
screen = screen.replace(state_anchor, state_extra, 1)

# Replace the Quick drawer helpers with cross-slide transitions.
helper_re = re.compile(
    r'''    fun closeQuickDrawer\(\) \{.*?\n    \}\n\n    fun openQuickDrawer\(\) \{.*?\n    \}\n''',
    re.S,
)
helpers = '''    fun closeQuickDrawer() {
        scope.launch { quickDrawerState.close() }
    }

    fun transitionToQuickDrawer() {
        if (menuTransitionInProgress) return
        menuTransitionInProgress = true
        // Run both animations together so one panel leaves while the other enters.
        scope.launch { drawerState.close() }
        scope.launch {
            quickDrawerState.open()
            menuTransitionInProgress = false
        }
    }

    fun transitionToMainDrawer() {
        if (menuTransitionInProgress) return
        menuTransitionInProgress = true
        scope.launch { quickDrawerState.close() }
        scope.launch {
            drawerState.open()
            menuTransitionInProgress = false
        }
    }

    fun openQuickDrawer() {
        transitionToQuickDrawer()
    }
'''
screen, helper_count = helper_re.subn(helpers, screen, count=1)
if helper_count != 1:
    raise SystemExit("Quick drawer helper region missing")

# Back behavior: closed -> pause + open main; open -> close current menu.
back_re = re.compile(
    r'''    BackHandler \{.*?\n    \}\n(?=    LaunchedEffect\()''',
    re.S,
)
new_back = '''    BackHandler {
        if (drawerState.isAnimationRunning || quickDrawerState.isAnimationRunning) {
            return@BackHandler
        }

        when {
            quickDrawerState.isOpen -> closeQuickDrawer()
            drawerState.isOpen -> closeDrawer()
            else -> {
                if (!isWudroidPaused) {
                    NativeEmulation.pauseTitle()
                    isWudroidPaused = true
                    pausedByMenu = true
                }
                scope.launch {
                    if (quickDrawerState.isOpen) quickDrawerState.close()
                    drawerState.open()
                }
            }
        }
    }
'''
screen, back_count = back_re.subn(new_back, screen, count=1)
if back_count != 1:
    raise SystemExit("BackHandler region missing")

# Input enable + automatic resume after the final menu closes.
effect_re = re.compile(
    r'''    LaunchedEffect\(drawerState\.isClosed, quickDrawerState\.isClosed\) \{\n        setInputListeningEnabled\(drawerState\.isClosed && quickDrawerState\.isClosed\)\n    \}\n'''
)
new_effect = '''    LaunchedEffect(drawerState.isClosed, quickDrawerState.isClosed, menuTransitionInProgress) {
        val menusClosed = drawerState.isClosed && quickDrawerState.isClosed
        setInputListeningEnabled(menusClosed)
        if (menusClosed && pausedByMenu && !menuTransitionInProgress) {
            NativeEmulation.resumeTitle()
            isWudroidPaused = false
            pausedByMenu = false
        }
    }
'''
screen, effect_count = effect_re.subn(new_effect, screen, count=1)
if effect_count != 1:
    raise SystemExit("dual-drawer input LaunchedEffect anchor missing")

# Manual pause/resume is no longer considered a menu-owned pause.
pause_cb_old = '''                            if (isWudroidPaused) {
                                NativeEmulation.resumeTitle()
                            } else {
                                NativeEmulation.pauseTitle()
                            }
                            isWudroidPaused = !isWudroidPaused
                            closeDrawer()
'''
pause_cb_new = '''                            if (isWudroidPaused) {
                                NativeEmulation.resumeTitle()
                            } else {
                                NativeEmulation.pauseTitle()
                            }
                            isWudroidPaused = !isWudroidPaused
                            pausedByMenu = false
                            closeDrawer()
'''
if pause_cb_old in screen:
    screen = screen.replace(pause_cb_old, pause_cb_new, 1)

# Closed left drawer must NOT listen for drag gestures over the game.
screen = screen.replace(
    "        gesturesEnabled = true, // Wudroid: swipe to open/close original drawer\n",
    "        gesturesEnabled = drawerState.isOpen, // Test6: no game-screen swipe interception\n",
    1,
)

# ---------------------------------------------------------------------------
# 3) Horizontal gestures exist only INSIDE an already-open menu.
#    Main: swipe left -> Quick Settings. Quick: swipe right -> Main.
# ---------------------------------------------------------------------------
def add_sheet_modifier(text: str, drawer_state_name: str, modifier_code: str) -> str:
    state_pos = text.find(f"drawerState = {drawer_state_name}")
    if state_pos < 0:
        raise SystemExit(f"drawer state not found: {drawer_state_name}")
    sheet_pos = text.find("ModalDrawerSheet(\n", state_pos)
    if sheet_pos < 0:
        raise SystemExit(f"ModalDrawerSheet not found after {drawer_state_name}")
    insert_pos = sheet_pos + len("ModalDrawerSheet(\n")
    if "WUDROID_MENU_FLOW_GAMEPAD_TEST6" in text[insert_pos:insert_pos + 900]:
        return text
    return text[:insert_pos] + modifier_code + text[insert_pos:]

quick_modifier = '''                        modifier = Modifier.pointerInput(quickDrawerState.isOpen) { // WUDROID_MENU_FLOW_GAMEPAD_TEST6
                            if (quickDrawerState.isOpen) {
                                detectHorizontalDragGestures(
                                    onDragStart = { quickMenuDragX = 0f },
                                    onHorizontalDrag = { _, dragAmount -> quickMenuDragX += dragAmount },
                                    onDragEnd = {
                                        if (quickMenuDragX > 70f) transitionToMainDrawer()
                                        quickMenuDragX = 0f
                                    },
                                    onDragCancel = { quickMenuDragX = 0f },
                                )
                            }
                        },
'''
left_modifier = '''                modifier = Modifier.pointerInput(drawerState.isOpen) { // WUDROID_MENU_FLOW_GAMEPAD_TEST6
                    if (drawerState.isOpen) {
                        detectHorizontalDragGestures(
                            onDragStart = { leftMenuDragX = 0f },
                            onHorizontalDrag = { _, dragAmount -> leftMenuDragX += dragAmount },
                            onDragEnd = {
                                if (leftMenuDragX < -70f) transitionToQuickDrawer()
                                leftMenuDragX = 0f
                            },
                            onDragCancel = { leftMenuDragX = 0f },
                        )
                    }
                },
'''
screen = add_sheet_modifier(screen, "quickDrawerState", quick_modifier)
screen = add_sheet_modifier(screen, "drawerState", left_modifier)

# ---------------------------------------------------------------------------
# 4) Make Quick Settings visually identical to the main Wudroid drawer.
# ---------------------------------------------------------------------------
quick_start = screen.find("@Composable\nprivate fun WudroidQuickSettingsContent")
quick_end = screen.find("@Composable\nprivate fun EmulationSurfaces", quick_start)
if quick_start < 0 or quick_end < 0:
    raise SystemExit("Quick Settings region missing")
quick_region = screen[quick_start:quick_end]
quick_region = quick_region.replace('text = "Quick Settings",', 'text = "WUDROID",', 1)
quick_region = quick_region.replace('text = "Wudroid • ajustes durante o jogo",', 'text = "Quick Settings",', 1)
screen = screen[:quick_start] + quick_region + screen[quick_end:]

# Replace Quick rows with the same surface/card language used by the main menu.
qt_start = screen.find("@Composable\nprivate fun QuickToggleRow(")
qv_start = screen.find("@Composable\nprivate fun QuickValueRow(", qt_start)
emu_surface_start = screen.find("@Composable\nprivate fun EmulationSurfaces(", qv_start)
if min(qt_start, qv_start, emu_surface_start) < 0:
    raise SystemExit("Quick row renderer anchors missing")

quick_toggle_fn = r'''@Composable
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
            .padding(vertical = 3.dp)
            .background(WudroidDrawerSurface, RoundedCornerShape(14.dp))
            .padding(horizontal = 12.dp, vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(modifier = Modifier.weight(1f).padding(end = 10.dp)) {
            Text(title, color = if (enabled) WudroidDrawerText else WudroidDrawerMuted, fontSize = 15.sp)
            subtitle?.let { Text(it, color = WudroidDrawerMuted, fontSize = 11.sp) }
        }
        Switch(
            checked = checked,
            onCheckedChange = onCheckedChange,
            enabled = enabled,
            colors = SwitchDefaults.colors(
                checkedThumbColor = WudroidDrawerBackground,
                checkedTrackColor = WudroidCyan,
                uncheckedThumbColor = WudroidDrawerMuted,
                uncheckedTrackColor = WudroidDrawerOutline,
            ),
        )
    }
}

'''

quick_value_fn = r'''@Composable
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
            .padding(vertical = 3.dp)
            .background(WudroidDrawerSurface, RoundedCornerShape(14.dp))
            .clickable(enabled = enabled, onClick = onClick)
            .padding(horizontal = 12.dp, vertical = 8.dp)
            .heightIn(min = 48.dp),
    ) {
        Text(title, color = if (enabled) WudroidDrawerText else WudroidDrawerMuted, fontSize = 15.sp)
        Text(value, color = WudroidCyan, fontSize = 13.sp, fontWeight = FontWeight.Bold)
        subtitle?.let { Text(it, color = WudroidDrawerMuted, fontSize = 11.sp) }
    }
}

'''
screen = screen[:qt_start] + quick_toggle_fn + quick_value_fn + screen[emu_surface_start:]

screen_path.write_text(screen)
activity_path.write_text(activity)

# ---------------------------------------------------------------------------
# 5) Increase the REAL Cemu touch gamepad at runtime, including already saved
#    layouts. Landscape receives a stronger scale because that is the normal
#    gameplay orientation.
# ---------------------------------------------------------------------------
rect_re = re.compile(
    r'''    private fun getBoundingRectangleForInput\(input: OverlayInput\): Rect \{.*?\n    \}\n(?=\n    private fun MutableList<Pair<OverlayInput, Input>>\.addRoundButton)''',
    re.S,
)
rect_fn = r'''    // WUDROID_MENU_FLOW_GAMEPAD_TEST6
    // Scale both saved and default Cemu touch rectangles around their centers.
    private fun wudroidScaleOverlayRect(source: Rect): Rect {
        if (width <= 0 || height <= 0 || source.width() <= 0 || source.height() <= 0) return source

        val scale = if (width >= height) 1.60f else 1.35f
        val targetWidth = (source.width() * scale).roundToInt().coerceIn(1, width)
        val targetHeight = (source.height() * scale).roundToInt().coerceIn(1, height)
        val centerX = source.centerX()
        val centerY = source.centerY()
        val maxLeft = (width - targetWidth).coerceAtLeast(0)
        val maxTop = (height - targetHeight).coerceAtLeast(0)
        val left = (centerX - targetWidth / 2).coerceIn(0, maxLeft)
        val top = (centerY - targetHeight / 2).coerceIn(0, maxTop)

        return Rect(left, top, left + targetWidth, top + targetHeight)
    }

    private fun getBoundingRectangleForInput(input: OverlayInput): Rect {
        val rect = settings.inputOverlayRectMap[input.toConfig()]
        val source = if (rect != null) {
            Rect(rect.left, rect.top, rect.right, rect.bottom)
        } else {
            getDefaultRectangle(input.toConfig(), width, height, pixelDensity)
        }
        return wudroidScaleOverlayRect(source)
    }
'''
overlay, rect_count = rect_re.subn(rect_fn, overlay, count=1)
if rect_count != 1:
    raise SystemExit("InputOverlay getBoundingRectangleForInput region missing")
overlay_path.write_text(overlay)

# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------
screen_check = screen_path.read_text()
activity_check = activity_path.read_text()
overlay_check = overlay_path.read_text()
required = [
    marker,
    "gesturesEnabled = drawerState.isOpen",
    "detectHorizontalDragGestures",
    "transitionToQuickDrawer()",
    "transitionToMainDrawer()",
    "pausedByMenu",
    'text = "WUDROID"',
    'text = "Quick Settings"',
    "SwitchDefaults.colors",
]
missing = [x for x in required if x not in screen_check]
if missing:
    raise SystemExit("Test6 screen verification failed: " + ", ".join(missing))

if "override fun dispatchTouchEvent(event: MotionEvent): Boolean" in activity_check:
    raise SystemExit("Test6 failed: right-edge dispatchTouchEvent still intercepts game touches")
if "configureRightEdgeGestureExclusion()" in activity_check:
    raise SystemExit("Test6 failed: system gesture exclusion call still active")

for x in ["WUDROID_MENU_FLOW_GAMEPAD_TEST6", "wudroidScaleOverlayRect", "1.60f"]:
    if x not in overlay_check:
        raise SystemExit("Test6 gamepad verification failed: " + x)

print("Wudroid 0.1.1 Menu Flow + Gamepad Test6 applied")
print("- game screen has zero menu swipe interception")
print("- Back pauses emulation and opens the main Wudroid menu")
print("- swipe left inside main menu -> Quick Settings")
print("- swipe right inside Quick Settings -> main menu")
print("- both menu animations run as a cross-slide")
print("- Quick Settings uses the same Wudroid cards/colors as main menu")
print("- real Cemu touch controls enlarged 1.60x in landscape")
