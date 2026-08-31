#!/usr/bin/env python3
from pathlib import Path
import re

screen_path = Path("cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationScreen.kt")
activity_path = Path("cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationActivity.kt")

if not screen_path.exists():
    raise SystemExit("EmulationScreen.kt not found")
if not activity_path.exists():
    raise SystemExit("EmulationActivity.kt not found")

screen = screen_path.read_text()
activity = activity_path.read_text()
marker = "WUDROID_RIGHT_EDGE_ACTIVITY_BRIDGE_TEST5"

if "WUDROID_EDEN_DUAL_MENU_TEST3" not in screen:
    raise SystemExit("Eden Dual Menu Test3 must be applied before Test5")

# ---------------------------------------------------------------------------
# EmulationScreen: receive a Compose state token from EmulationActivity.
# The Activity sees touch events before SurfaceView/InputOverlay and increments
# this token after a deliberate right-edge -> center gesture.
# ---------------------------------------------------------------------------
sig_old = '''    setInputListeningEnabled: (Boolean) -> Unit,\n    onQuit: () -> Unit,\n    viewModel: EmulationViewModel = viewModel(\n'''
sig_new = '''    setInputListeningEnabled: (Boolean) -> Unit,\n    onQuit: () -> Unit,\n    quickSettingsRequestToken: Int = 0, // WUDROID_RIGHT_EDGE_ACTIVITY_BRIDGE_TEST5\n    viewModel: EmulationViewModel = viewModel(\n'''
if sig_old in screen:
    screen = screen.replace(sig_old, sig_new, 1)
elif "quickSettingsRequestToken: Int" not in screen:
    raise SystemExit("EmulationScreen signature anchor missing")

helper = '''    fun openQuickDrawer() {\n        scope.launch {\n            drawerState.close()\n            quickDrawerState.open()\n        }\n    }\n'''
bridge_effect = '''    fun openQuickDrawer() {\n        scope.launch {\n            drawerState.close()\n            quickDrawerState.open()\n        }\n    }\n\n    // WUDROID_RIGHT_EDGE_ACTIVITY_BRIDGE_TEST5\n    // Activity-level gesture bridge. This bypasses SurfaceView and the touch\n    // controller overlay, both of which may consume pointer events before a\n    // Compose pointerInput detector sees them.\n    LaunchedEffect(quickSettingsRequestToken) {\n        if (quickSettingsRequestToken > 0) {\n            if (drawerState.isOpen) drawerState.close()\n            if (quickDrawerState.isClosed) quickDrawerState.open()\n        }\n    }\n'''
if "LaunchedEffect(quickSettingsRequestToken)" not in screen:
    if helper not in screen:
        raise SystemExit("openQuickDrawer helper anchor missing")
    screen = screen.replace(helper, bridge_effect, 1)

# Test4 used Compose pointerInput on the nested right drawer. Remove that
# detector so there is only one owner of the opening gesture. Keep built-in
# gestures while the Quick drawer is open so it can still be dragged closed.
pattern = re.compile(
    r'''        ModalNavigationDrawer\(\n'''
    r'''            drawerState = quickDrawerState,\n'''
    r'''            // WUDROID_RIGHT_QUICK_SWIPE_FIX_TEST4.*?'''
    r'''            drawerContent = \{\n''',
    re.S,
)
replacement = '''        ModalNavigationDrawer(\n            drawerState = quickDrawerState,\n            // Opening comes from EmulationActivity; dragging stays enabled\n            // while open so the panel can still be swiped away.\n            gesturesEnabled = quickDrawerState.isOpen,\n            drawerContent = {\n'''
screen, count = pattern.subn(replacement, screen, count=1)
if count == 0 and "WUDROID_RIGHT_QUICK_SWIPE_FIX_TEST4" in screen:
    raise SystemExit("Could not remove Test4 Compose right-edge detector")

screen_path.write_text(screen)

# ---------------------------------------------------------------------------
# EmulationActivity: observe touchscreen events before Compose/SurfaceView.
# ---------------------------------------------------------------------------
imports = [
    "import android.graphics.Rect",
    "import android.os.Build",
    "import android.view.InputDevice",
    "import androidx.compose.runtime.mutableIntStateOf",
    "import kotlin.math.abs",
]
for imp in imports:
    if imp not in activity:
        activity = activity.replace("package info.cemu.cemu.emulation\n", "package info.cemu.cemu.emulation\n" + imp + "\n", 1)

field_anchor = '''    private lateinit var inputManager: InputDelegateManager\n    private var processInputEvents = true\n'''
field_replacement = '''    private lateinit var inputManager: InputDelegateManager\n    private var processInputEvents = true\n\n    // WUDROID_RIGHT_EDGE_ACTIVITY_BRIDGE_TEST5\n    private val quickSettingsRequestToken = mutableIntStateOf(0)\n    private var rightEdgeSwipeTracking = false\n    private var rightEdgeSwipeTriggered = false\n    private var rightEdgeDownX = 0f\n    private var rightEdgeDownY = 0f\n'''
if "private val quickSettingsRequestToken = mutableIntStateOf(0)" not in activity:
    if field_anchor not in activity:
        raise SystemExit("EmulationActivity fields anchor missing")
    activity = activity.replace(field_anchor, field_replacement, 1)

method_anchor = '''    override fun onGenericMotionEvent(event: MotionEvent): Boolean {\n'''
new_methods = '''    override fun dispatchTouchEvent(event: MotionEvent): Boolean {\n        // WUDROID_RIGHT_EDGE_ACTIVITY_BRIDGE_TEST5\n        // Observe touchscreen events before SurfaceView/InputOverlay receives them.\n        val isTouchscreen =\n            (event.source and InputDevice.SOURCE_TOUCHSCREEN) == InputDevice.SOURCE_TOUCHSCREEN\n\n        if (isTouchscreen) {\n            val density = resources.displayMetrics.density\n            val edgeWidthPx = 24f * density\n            val openThresholdPx = 60f * density\n            val decorWidth = window.decorView.width.toFloat()\n\n            when (event.actionMasked) {\n                MotionEvent.ACTION_DOWN -> {\n                    rightEdgeSwipeTriggered = false\n                    rightEdgeDownX = event.x\n                    rightEdgeDownY = event.y\n                    rightEdgeSwipeTracking =\n                        decorWidth > 0f && event.x >= decorWidth - edgeWidthPx\n                }\n\n                MotionEvent.ACTION_MOVE -> {\n                    if (rightEdgeSwipeTriggered) {\n                        return true\n                    }\n\n                    if (rightEdgeSwipeTracking) {\n                        val inwardDx = rightEdgeDownX - event.x\n                        val verticalDy = abs(event.y - rightEdgeDownY)\n\n                        if (inwardDx >= openThresholdPx && inwardDx > verticalDy * 1.15f) {\n                            rightEdgeSwipeTriggered = true\n                            rightEdgeSwipeTracking = false\n                            quickSettingsRequestToken.intValue++\n\n                            // The game/overlay may already have seen ACTION_DOWN. Send CANCEL\n                            // so it does not treat the menu gesture as a button/joystick input.\n                            val cancelEvent = MotionEvent.obtain(event)\n                            cancelEvent.action = MotionEvent.ACTION_CANCEL\n                            super.dispatchTouchEvent(cancelEvent)\n                            cancelEvent.recycle()\n                            return true\n                        }\n\n                        // Abandon clearly vertical or outward gestures and let the game keep them.\n                        if (verticalDy > openThresholdPx * 1.5f || inwardDx <= -openThresholdPx) {\n                            rightEdgeSwipeTracking = false\n                        }\n                    }\n                }\n\n                MotionEvent.ACTION_UP, MotionEvent.ACTION_CANCEL -> {\n                    val consume = rightEdgeSwipeTriggered\n                    rightEdgeSwipeTracking = false\n                    rightEdgeSwipeTriggered = false\n                    if (consume) return true\n                }\n            }\n        }\n\n        return super.dispatchTouchEvent(event)\n    }\n\n    private fun configureRightEdgeGestureExclusion() {\n        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q) return\n\n        val decor = window.decorView\n        decor.addOnLayoutChangeListener { view, _, _, _, _, _, _, _, _ ->\n            if (view.width <= 0 || view.height <= 0) return@addOnLayoutChangeListener\n\n            val density = resources.displayMetrics.density\n            val edgeWidth = (24f * density).toInt().coerceAtLeast(1)\n            // Android limits gesture exclusion per edge. Keep this centered and\n            // below the platform cap so the right-edge swipe reaches Wudroid.\n            val exclusionHeight = minOf(view.height, (196f * density).toInt())\n            val top = ((view.height - exclusionHeight) / 2).coerceAtLeast(0)\n\n            view.systemGestureExclusionRects = listOf(\n                Rect(\n                    (view.width - edgeWidth).coerceAtLeast(0),\n                    top,\n                    view.width,\n                    (top + exclusionHeight).coerceAtMost(view.height),\n                )\n            )\n        }\n    }\n\n    override fun onGenericMotionEvent(event: MotionEvent): Boolean {\n'''
if "override fun dispatchTouchEvent(event: MotionEvent): Boolean" not in activity:
    if method_anchor not in activity:
        raise SystemExit("onGenericMotionEvent anchor missing")
    activity = activity.replace(method_anchor, new_methods, 1)

fullscreen_anchor = '''        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)\n        setFullscreen()\n\n        val gamePath = getGamePath()\n'''
fullscreen_replacement = '''        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)\n        setFullscreen()\n        configureRightEdgeGestureExclusion()\n\n        val gamePath = getGamePath()\n'''
if "        configureRightEdgeGestureExclusion()\n" not in activity:
    if fullscreen_anchor not in activity:
        raise SystemExit("setFullscreen anchor missing")
    activity = activity.replace(fullscreen_anchor, fullscreen_replacement, 1)

call_anchor = '''                        onQuit = ::onQuit,\n                        setInputListeningEnabled = { processInputEvents = it },\n'''
call_replacement = '''                        onQuit = ::onQuit,\n                        setInputListeningEnabled = { processInputEvents = it },\n                        quickSettingsRequestToken = quickSettingsRequestToken.intValue,\n'''
if call_anchor in activity:
    activity = activity.replace(call_anchor, call_replacement, 1)
elif "quickSettingsRequestToken = quickSettingsRequestToken.intValue" not in activity:
    raise SystemExit("EmulationScreen call anchor missing")

activity_path.write_text(activity)

# Verification is behavior-oriented rather than formatting-oriented.
screen_check = screen_path.read_text()
activity_check = activity_path.read_text()
required_screen = [
    marker,
    "quickSettingsRequestToken: Int",
    "LaunchedEffect(quickSettingsRequestToken)",
    "quickDrawerState.open()",
]
required_activity = [
    marker,
    "override fun dispatchTouchEvent(event: MotionEvent): Boolean",
    "SOURCE_TOUCHSCREEN",
    "quickSettingsRequestToken.intValue++",
    "systemGestureExclusionRects",
    "quickSettingsRequestToken = quickSettingsRequestToken.intValue",
]
missing = [x for x in required_screen if x not in screen_check]
missing += [x for x in required_activity if x not in activity_check]
if missing:
    raise SystemExit("Right-edge Activity bridge verification failed: " + ", ".join(missing))

print("Wudroid 0.1.1 Right-edge Activity Bridge Test5 BuildFix1 applied")
print("- right-edge swipe observed at Activity level before SurfaceView/InputOverlay")
print("- system back gesture exclusion added to center-right edge")
print("- Activity sends a Compose state token to the existing Quick Settings drawer")
print("- Quick Settings button remains unchanged")
