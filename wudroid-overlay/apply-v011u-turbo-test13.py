#!/usr/bin/env python3
from pathlib import Path

screen_path = Path('cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationScreen.kt')
native_kt_path = Path('cemu-engine/src/android/app/src/main/java/info/cemu/cemu/nativeinterface/NativeEmulation.kt')
native_cpp_path = Path('cemu-engine/src/android/app/src/main/cpp/NativeEmulation.cpp')

for p in (screen_path, native_kt_path, native_cpp_path):
    if not p.exists():
        raise SystemExit(f'Required source not found: {p}')

screen = screen_path.read_text()
native_kt = native_kt_path.read_text()
native_cpp = native_cpp_path.read_text()
marker = 'WUDROID_TURBO_TEST13'

if marker in screen:
    print('Wudroid Turbo Test13 already applied')
    raise SystemExit(0)

if 'WUDROID_SAVESTATION_TEST12' not in screen:
    raise SystemExit('Save Station Test12 must be applied before Turbo Test13')

# ---------------------------------------------------------------------------
# 1) Native bridge. Cemu already has a desktop fast-forward implementation:
#    ActiveSettings::TimerShiftFactor = 3 for fast-forward, 1 for normal.
#    Reuse the emulator's own timing control instead of faking frame skipping.
# ---------------------------------------------------------------------------
kt_anchor = '    external fun loadQuickState(path: String): Int\n'
if kt_anchor not in native_kt:
    raise SystemExit('NativeEmulation.kt quick-state anchor missing')

kt_insert = '''    // WUDROID_TURBO_TEST13\n    @JvmStatic\n    external fun setFastForwardEnabled(enabled: Boolean)\n\n'''
native_kt = native_kt.replace(kt_anchor, kt_anchor + '\n' + kt_insert, 1)

if '#include "config/ActiveSettings.h"' not in native_cpp:
    # Insert next to the Test10 standard-library block so include ordering stays simple.
    include_anchor = '// WUDROID_QUICKSTATE_ENGINE_TEST10\n'
    if include_anchor not in native_cpp:
        raise SystemExit('NativeEmulation.cpp Test10 include anchor missing')
    native_cpp = native_cpp.replace(
        include_anchor,
        include_anchor + '#include "config/ActiveSettings.h"\n',
        1,
    )

jni_marker = 'Java_info_cemu_cemu_nativeinterface_NativeEmulation_setFastForwardEnabled'
if jni_marker not in native_cpp:
    native_cpp = native_cpp.rstrip() + r'''

// WUDROID_TURBO_TEST13
extern "C" [[maybe_unused]] JNIEXPORT void JNICALL
Java_info_cemu_cemu_nativeinterface_NativeEmulation_setFastForwardEnabled(
    [[maybe_unused]] JNIEnv* env,
    [[maybe_unused]] jclass clazz,
    jboolean enabled)
{
    // Match Cemu's native desktop fast-forward behavior: 3x while enabled,
    // normal 1x timing otherwise.
    ActiveSettings::TimerShiftFactor = enabled == JNI_TRUE ? 3 : 1;
}
''' + '\n'

# ---------------------------------------------------------------------------
# 2) Compose floating lightning control over the touch gamepad.
#    Normal mode: tap toggles 1x <-> 3x.
#    Gamepad editor: drag the lightning button; position persists via prefs.
# ---------------------------------------------------------------------------
imports = [
    'import androidx.compose.foundation.gestures.detectDragGestures',
    'import androidx.compose.runtime.DisposableEffect',
    'import androidx.compose.foundation.layout.size',
    'import androidx.compose.foundation.layout.offset',
    'import androidx.compose.ui.unit.IntOffset',
    'import kotlin.math.roundToInt',
]
# WUDROID_TURBO_TEST13_BUILDFIX3
# BuildFix3: include androidx.compose.foundation.layout.offset because the
# lightning button uses Modifier.offset { IntOffset(...) }.
# Keep import insertion independent from Cemu's exact import ordering.  The previous
# Test13 BuildFix1 still assumed specific neighboring imports and therefore stopped
# before compilation when layout.size was absent.  Kotlin accepts imports in any
# order, so append each missing import to the existing import block.
def ensure_import(source: str, imp: str) -> str:
    if imp in source:
        return source

    lines = source.splitlines(keepends=True)
    import_indexes = [
        i for i, line in enumerate(lines)
        if line.startswith('import ')
    ]
    if not import_indexes:
        raise SystemExit('EmulationScreen.kt import block missing')

    insert_at = import_indexes[-1] + 1
    lines.insert(insert_at, imp + '\n')
    return ''.join(lines)

for imp in imports:
    screen = ensure_import(screen, imp)

state_anchor = '    val wudroidQuickStateContext = LocalContext.current // WUDROID_QUICKSTATE_ENGINE_TEST10\n'
if state_anchor not in screen:
    raise SystemExit('Quick State context state anchor missing')

state_block = state_anchor + '''    // WUDROID_TURBO_TEST13\n    val wudroidTurboPrefs = remember(wudroidQuickStateContext) {\n        wudroidQuickStateContext.getSharedPreferences("wudroid_turbo", android.content.Context.MODE_PRIVATE)\n    }\n    var wudroidTurboEnabled by rememberSaveable { mutableStateOf(false) }\n    var wudroidTurboOffsetX by rememberSaveable {\n        mutableFloatStateOf(wudroidTurboPrefs.getFloat("offset_x", 0f))\n    }\n    var wudroidTurboOffsetY by rememberSaveable {\n        mutableFloatStateOf(wudroidTurboPrefs.getFloat("offset_y", -84f))\n    }\n\n    DisposableEffect(Unit) {\n        onDispose {\n            // Never leave another title/game running at 3x after this screen is gone.\n            NativeEmulation.setFastForwardEnabled(false)\n        }\n    }\n'''
screen = screen.replace(state_anchor, state_block, 1)

# Insert just before the existing gamepad editor panel. This keeps the lightning
# above the touch surface and lets editor mode drag it without changing Wii U input.
editor_anchor = '''        if (inputOverlayInputMode != DEFAULT) {\n            EditInputsLayout(\n'''
if editor_anchor not in screen:
    raise SystemExit('Gamepad editor invocation anchor missing')

turbo_call = '''        // WUDROID_TURBO_TEST13_BUILDFIX1: explicit BoxScope for align.\n        Box(modifier = Modifier.fillMaxSize()) {\n            WudroidTurboButton(\n                modifier = Modifier\n                    .align(Alignment.BottomCenter)\n                    .offset {\n                        IntOffset(\n                            wudroidTurboOffsetX.roundToInt(),\n                            wudroidTurboOffsetY.roundToInt(),\n                        )\n                    },\n                enabled = wudroidTurboEnabled,\n                editing = inputOverlayInputMode != DEFAULT,\n                onToggle = {\n                    wudroidTurboEnabled = !wudroidTurboEnabled\n                    NativeEmulation.setFastForwardEnabled(wudroidTurboEnabled)\n                },\n                onDrag = { dx, dy ->\n                    wudroidTurboOffsetX += dx\n                    wudroidTurboOffsetY += dy\n                },\n                onDragFinished = {\n                    wudroidTurboPrefs.edit()\n                        .putFloat("offset_x", wudroidTurboOffsetX)\n                        .putFloat("offset_y", wudroidTurboOffsetY)\n                        .apply()\n                },\n            )\n        }\n\n'''
screen = screen.replace(editor_anchor, turbo_call + editor_anchor, 1)

function_anchor = '@Composable\nprivate fun EditInputsLayout('
if function_anchor not in screen:
    raise SystemExit('EditInputsLayout function anchor missing')

turbo_fn = r'''@Composable
private fun WudroidTurboButton(
    modifier: Modifier,
    enabled: Boolean,
    editing: Boolean,
    onToggle: () -> Unit,
    onDrag: (Float, Float) -> Unit,
    onDragFinished: () -> Unit,
) {
    Surface(
        modifier = modifier
            .size(58.dp)
            .pointerInput(editing, enabled) {
                if (editing) {
                    detectDragGestures(
                        onDragEnd = onDragFinished,
                        onDragCancel = onDragFinished,
                        onDrag = { change, dragAmount ->
                            change.consume()
                            onDrag(dragAmount.x, dragAmount.y)
                        },
                    )
                } else {
                    detectTapGestures(onTap = { onToggle() })
                }
            },
        shape = androidx.compose.foundation.shape.CircleShape,
        color = if (enabled) {
            WudroidCyan.copy(alpha = 0.34f)
        } else {
            WudroidDrawerBackground.copy(alpha = 0.76f)
        },
        border = BorderStroke(
            width = if (enabled || editing) 2.dp else 1.dp,
            color = if (enabled || editing) WudroidCyan else WudroidDrawerOutline,
        ),
        shadowElevation = 7.dp,
    ) {
        Box(contentAlignment = Alignment.Center) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(
                    text = "⚡",
                    color = if (enabled || editing) WudroidCyan else WudroidDrawerText,
                    fontSize = 23.sp,
                    fontWeight = FontWeight.Bold,
                )
                Text(
                    text = if (enabled) "3×" else "1×",
                    color = if (enabled) WudroidCyan else WudroidDrawerMuted,
                    fontSize = 8.sp,
                    fontWeight = FontWeight.Bold,
                )
            }
        }
    }
}

'''
screen = screen.replace(function_anchor, turbo_fn + function_anchor, 1)

native_kt_path.write_text(native_kt)
native_cpp_path.write_text(native_cpp)
screen_path.write_text(screen)

checks = {
    native_kt_path: [
        marker,
        'external fun setFastForwardEnabled(enabled: Boolean)',
    ],
    native_cpp_path: [
        marker,
        '#include "config/ActiveSettings.h"',
        'ActiveSettings::TimerShiftFactor = enabled == JNI_TRUE ? 3 : 1;',
        jni_marker,
    ],
    screen_path: [
        marker,
        'WudroidTurboButton(',
        'import androidx.compose.foundation.layout.size',
        'import androidx.compose.foundation.layout.offset',
        'Box(modifier = Modifier.fillMaxSize())',
        'text = "⚡"',
        'text = if (enabled) "3×" else "1×"',
        'NativeEmulation.setFastForwardEnabled(wudroidTurboEnabled)',
        'detectDragGestures(',
        'getSharedPreferences("wudroid_turbo"',
    ],
}
for path, needles in checks.items():
    text = path.read_text()
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise SystemExit(f'Test13 verification failed for {path}: {missing}')

print('Wudroid 0.1.1 Turbo Test13 applied')
print('- floating lightning button added above the touch gamepad')
print('- tap toggles Cemu native fast-forward: 1x <-> 3x')
print('- editor mode drags the lightning button and persists its position')
print('- turbo automatically returns to 1x when the emulation screen is disposed')
