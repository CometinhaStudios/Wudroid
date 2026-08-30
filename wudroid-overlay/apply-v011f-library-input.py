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

def ensure_import(text: str, import_line: str) -> str:
    if import_line in text:
        return text
    imports = list(re.finditer(r"^import .+$", text, re.M))
    if not imports:
        raise SystemExit(f"No import block found while adding {import_line}")
    pos = imports[-1].end()
    return text[:pos] + "\n" + import_line + text[pos:]

# Wudroid's Add Folder launcher used to start a native scan immediately. The
# screen also scans again on RESUMED because gamePathsHaveChanged() is true.
# Remove ONLY the immediate reload after addGamesPath. This is intentionally
# idempotent because older Wudroid test builds may have already removed it.
s = re.sub(
    r"(NativeSettings\.addGamesPath\(gamesPath\)\s*)NativeGameTitles\.reloadGameTitles\(\)",
    r"\1// Wudroid: game scan is deferred to the RESUMED lifecycle.",
    s,
    count=1,
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

# delay(300) lives in GamesListScreen, so guarantee its import too.
if "delay(300)" in s:
    s = ensure_import(s, "import kotlinx.coroutines.delay")

screen.write_text(s)

v = vm.read_text()
for imp in (
    "import kotlinx.coroutines.Job",
    "import kotlinx.coroutines.delay",
    "import kotlinx.coroutines.launch",
):
    v = ensure_import(v, imp)

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
    if n == 0 and "WudroidKeyboardMouse.onMouseMotion(event)" not in a:
        raise SystemExit("EmulationActivity mouse hook anchor missing")

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
    if n == 0 and "WudroidKeyboardMouse.onKeyEvent(event)" not in a:
        raise SystemExit("EmulationActivity keyboard hook anchor missing")

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
# Do not verify comments/formatting: previous Wudroid builds can already have
# equivalent code. Verify behavior instead.
screen_text = screen.read_text()
vm_text = vm.read_text()
activity_text = activity.read_text()

# There must not be an immediate native reload right after adding the folder.
if re.search(
    r"NativeSettings\.addGamesPath\(gamesPath\)[\s\S]{0,220}?NativeGameTitles\.reloadGameTitles\(\)",
    screen_text,
):
    raise SystemExit("Verification failed: Add Folder still performs an immediate native game scan")

if "gamesListViewModel.refreshGames()" not in screen_text:
    raise SystemExit("Verification failed: GamesListScreen has no lifecycle refresh path")

for needle in ("refreshJob?.cancel()", "delay(250)", "NativeGameTitles.reloadGameTitles()"):
    if needle not in vm_text:
        raise SystemExit(f"Verification failed in {vm}: {needle}")

for needle in (
    "WudroidKeyboardMouse.onMouseMotion(event)",
    "WudroidKeyboardMouse.onKeyEvent(event)",
    "setOnCapturedPointerListener",
):
    if needle not in activity_text:
        raise SystemExit(f"Verification failed in {activity}: {needle}")

print("Wudroid 0.1.1 LibraryFix + KeyboardMouse BuildFix2 applied")
print("- game folder scan: single/debounced native reload")
print("- WASD: left analog stick")
print("- mouse: right analog stick with pointer capture")
print("- other keyboard keys: passed to Cemu InputHandler for mapping")
