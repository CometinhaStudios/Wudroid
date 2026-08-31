#!/usr/bin/env python3
from pathlib import Path

path = Path("cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationScreen.kt")
if not path.exists():
    raise SystemExit("EmulationScreen.kt not found")

s = path.read_text()
marker = "WUDROID_RIGHT_QUICK_SWIPE_FIX_TEST4"
if marker in s:
    print("Wudroid right Quick Settings swipe fix already applied")
    raise SystemExit(0)

if "WUDROID_EDEN_DUAL_MENU_TEST3" not in s:
    raise SystemExit("Eden Dual Menu Test3 must be applied before Right Swipe Fix Test4")

# Explicit edge gesture detector. The nested left Material drawer can win the
# horizontal-drag competition, so relying only on the outer RTL drawer's
# built-in gesture is not reliable. This detector observes the physical right
# edge and opens the existing Quick Settings drawer after a deliberate
# right-to-left swipe.
imports = [
    "import androidx.compose.foundation.gestures.awaitEachGesture",
    "import androidx.compose.foundation.gestures.awaitFirstDown",
    "import androidx.compose.ui.input.pointer.pointerInput",
]
for imp in imports:
    if imp not in s:
        package = "package info.cemu.cemu.emulation\n"
        s = s.replace(package, package + imp + "\n", 1)

old = '''        ModalNavigationDrawer(
            drawerState = quickDrawerState,
            gesturesEnabled = true,
            drawerContent = {
'''
new = '''        ModalNavigationDrawer(
            drawerState = quickDrawerState,
            // WUDROID_RIGHT_QUICK_SWIPE_FIX_TEST4
            // Built-in dragging stays active while open for natural closing.
            // Opening is handled by the explicit physical-right-edge detector
            // below so the nested left drawer cannot steal the gesture.
            gesturesEnabled = quickDrawerState.isOpen,
            modifier = Modifier.pointerInput(quickDrawerState.isClosed, drawerState.isClosed) {
                val rightEdgeWidth = 40.dp.toPx()
                val openThreshold = 56.dp.toPx()

                awaitEachGesture {
                    val down = awaitFirstDown(requireUnconsumed = false)
                    if (!quickDrawerState.isClosed || !drawerState.isClosed) {
                        return@awaitEachGesture
                    }

                    // Physical right edge; LayoutDirection does not affect pointer coordinates.
                    if (down.position.x < size.width.toFloat() - rightEdgeWidth) {
                        return@awaitEachGesture
                    }

                    val pointerId = down.id
                    var dragX = 0f

                    while (true) {
                        val event = awaitPointerEvent()
                        val change = event.changes.firstOrNull { it.id == pointerId } ?: break
                        if (!change.pressed) break

                        dragX += change.position.x - change.previousPosition.x

                        // Right -> left opens Quick Settings.
                        if (dragX <= -openThreshold) {
                            change.consume()
                            openQuickDrawer()
                            break
                        }

                        // If the user clearly moves the wrong way, give up quickly.
                        if (dragX >= openThreshold) {
                            break
                        }
                    }
                }
            },
            drawerContent = {
'''
if old not in s:
    raise SystemExit("Right-side ModalNavigationDrawer anchor missing")
s = s.replace(old, new, 1)

path.write_text(s)

check = path.read_text()
required = [
    marker,
    "awaitEachGesture",
    "awaitFirstDown(requireUnconsumed = false)",
    "rightEdgeWidth = 40.dp.toPx()",
    "openThreshold = 56.dp.toPx()",
    "openQuickDrawer()",
    "gesturesEnabled = quickDrawerState.isOpen",
]
missing = [x for x in required if x not in check]
if missing:
    raise SystemExit("Right Quick Settings swipe fix verification failed: " + ", ".join(missing))

print("Wudroid 0.1.1 Eden Dual Menu Right Swipe Fix Test4 applied")
print("- physical right-edge swipe detector added")
print("- swipe direction: right edge -> center")
print("- existing Quick Settings button preserved")
print("- existing left drawer gesture preserved")
