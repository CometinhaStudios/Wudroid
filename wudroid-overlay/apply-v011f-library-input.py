#!/usr/bin/env python3
from pathlib import Path
import re

root = Path("cemu-engine/src/android/app/src/main/java/info/cemu/cemu")

# ---------------------------------------------------------------------------
# 1) Game-folder crash fix
# ---------------------------------------------------------------------------
screen = root / "games/list/GamesListScreen.kt"
vm = root / "games/list/GamesListViewModel.kt"

if not screen.exists() or not vm.exists():
    raise SystemExit("Games list source files not found")

s = screen.read_text()

# Wudroid's Add Folder launcher used to start a native scan immediately. The
# screen also scans again on RESUMED because gamePathsHaveChanged() is true.
# Remove the first scan and let the lifecycle path perform one serialized load.
s = s.replace(
    "NativeSettings.addGamesPath(gamesPath)\n                NativeGameTitles.reloadGameTitles()",
    "NativeSettings.addGamesPath(gamesPath)\n"
    "                // Wudroid: the RESUMED lifecycle performs the single game scan.",
)

# Give SAF a short moment to settle after returning from the document picker.
old = '''LaunchedEffect(lifecycleState) {
        if (lifecycleState == Lifecycle.State.RESUMED && gamesListViewModel.gamePathsHaveChanged())
            gamesListViewModel.refreshGames()
    }'''
new = '''LaunchedEffect(lifecycleState) {
        if (lifecycleState == Lifecycle.State.RESUMED && gamesListViewModel.gamePathsHaveChanged()) {
            // Wudroid: wait for the persisted SAF permission before starting native I/O.
            delay(300)
            gamesListViewModel.refreshGames()
        }
    }'''
if old in s:
    s = s.replace(old, new, 1)

screen.write_text(s)

v = vm.read_text()
if "import kotlinx.coroutines.Job" not in v:
    anchor = "import kotlinx.coroutines.flow.MutableStateFlow"
    if anchor not in v:
        raise SystemExit("GamesListViewModel import anchor missing")
    v = v.replace(anchor, "import kotlinx.coroutines.Job\nimport kotlinx.coroutines.delay\nimport kotlinx.coroutines.launch\n" + anchor, 1)

if "private var refreshJob: Job? = null" not in v:
    anchor = "private var gamePaths = NativeSettings.getGamesPaths().toSet()"
    if anchor not in v:
        raise SystemExit("GamesListViewModel gamePaths anchor missing")
    v = v.replace(anchor, anchor + "\n    private var refreshJob: Job? = null", 1)

old_refresh = '''fun refreshGames() {
        _games.value = emptySet()
        NativeGameTitles.reloadGameTitles()
    }'''
new_refresh = '''fun refreshGames() {
        // Coalesce multiple requests caused by SAF -> onResume -> pull-to-refresh.
        // The newest request wins, so a newly added folder is never lost.
        refreshJob?.cancel()
        refreshJob = viewModelScope.launch {
            delay(250)
            _games.value = emptySet()
            NativeGameTitles.reloadGameTitles()
        }
    }'''
if old_refresh in v:
    v = v.replace(old_refresh, new_refresh, 1)
elif "refreshJob?.cancel()" not in v:
    raise SystemExit("GamesListViewModel refreshGames anchor missing")

vm.write_text(v)

# ---------------------------------------------------------------------------
# 2) Keyboard + mouse inside the real emulation Activity
# ---------------------------------------------------------------------------
activity = root / "emulation/EmulationActivity.kt"
if not activity.exists():
    raise SystemExit("EmulationActivity.kt not found")
a = activity.read_text()

# Mouse: consume mouse motion first, then fall back to Cemu's normal devices.
if "WudroidKeyboardMouse.onMouseMotion(event)" not in a:
    pattern = re.compile(
        r'(override fun onGenericMotionEvent\(event: MotionEvent\): Boolean \{\s*)'
        r'(if \(processInputEvents && InputHandler\.onMotionEvent\(event\)\) \{)',
        re.S,
    )
    repl = (
        r'\1if (processInputEvents && WudroidKeyboardMouse.onMouseMotion(event)) {\n'
        r'            if (android.os.Build.VERSION.SDK_INT >= 26 && !window.decorView.hasPointerCapture()) {\n'
        r'                window.decorView.requestPointerCapture()\n'
        r'            }\n'
        r'            return true\n'
        r'        }\n\n        \2'
    )
    a, n = pattern.subn(repl, a, count=1)
    if n == 0:
        raise SystemExit("EmulationActivity onGenericMotionEvent anchor missing")

# Keyboard: WASD -> left stick. Other keys keep going to InputHandler so the
# existing controller mapping can bind them to A/B/X/Y/L/R/etc.
if "WudroidKeyboardMouse.onKeyEvent(event)" not in a:
    pattern = re.compile(
        r'(override fun dispatchKeyEvent\(event: KeyEvent\): Boolean \{\s*HotkeyManager\.onKeyEvent\(event\)\s*)'
        r'(if \(processInputEvents && InputHandler\.onKeyEvent\(event\)\) \{)',
        re.S,
    )
    repl = (
        r'\1\n        if (event.keyCode == KeyEvent.KEYCODE_ESCAPE && event.action == KeyEvent.ACTION_DOWN) {\n'
        r'            if (android.os.Build.VERSION.SDK_INT >= 26 && window.decorView.hasPointerCapture()) {\n'
        r'                window.decorView.releasePointerCapture()\n'
        r'                WudroidKeyboardMouse.reset()\n'
        r'                return true\n'
        r'            }\n'
        r'        }\n\n'
        r'        if (processInputEvents && WudroidKeyboardMouse.onKeyEvent(event)) {\n'
        r'            return true\n'
        r'        }\n\n        \2'
    )
    a, n = pattern.subn(repl, a, count=1)
    if n == 0:
        raise SystemExit("EmulationActivity dispatchKeyEvent anchor missing")

# Captured pointer events are delivered straight to the decor view.
if "setOnCapturedPointerListener" not in a:
    anchor = "inputManager = InputDelegateManager(this)"
    if anchor not in a:
        raise SystemExit("EmulationActivity inputManager anchor missing")
    addition = '''inputManager = InputDelegateManager(this)

        if (android.os.Build.VERSION.SDK_INT >= 26) {
            window.decorView.setOnCapturedPointerListener { _, event ->
                if (processInputEvents) WudroidKeyboardMouse.onMouseMotion(event) else false
            }
        }'''
    a = a.replace(anchor, addition, 1)

# Always clear virtual axes when the activity loses focus.
if "WudroidKeyboardMouse.reset()" not in a.split("override fun onPause()", 1)[-1][:250]:
    anchor = '''override fun onPause() {
        super.onPause()'''
    if anchor in a:
        a = a.replace(anchor, '''override fun onPause() {
        WudroidKeyboardMouse.reset()
        super.onPause()''', 1)

activity.write_text(a)

# Verification
checks = {
    screen: ["delay(300)", "RESUMED lifecycle performs the single game scan"],
    vm: ["refreshJob?.cancel()", "delay(250)", "NativeGameTitles.reloadGameTitles()"],
    activity: ["WudroidKeyboardMouse.onMouseMotion(event)", "WudroidKeyboardMouse.onKeyEvent(event)", "setOnCapturedPointerListener"],
}
for file, needles in checks.items():
    text = file.read_text()
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"Verification failed in {file}: {needle}")

print("Wudroid 0.1.1 LibraryFix + KeyboardMouse Test1 applied")
print("- game folder scan: single/debounced native reload")
print("- WASD: left analog stick")
print("- mouse: right analog stick with pointer capture")
print("- other keyboard keys: passed to Cemu InputHandler for mapping")
