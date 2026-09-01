#!/usr/bin/env python3
from pathlib import Path
import re

screen_path = Path('cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationScreen.kt')
main_path = Path('cemu-engine/src/android/app/src/main/java/info/cemu/cemu/MainActivity.kt')

for p in (screen_path, main_path):
    if not p.exists():
        raise SystemExit(f'Required source not found: {p}')

screen = screen_path.read_text()
main = main_path.read_text()
marker = 'WUDROID_SAVESTATION_TEST12_BUILDFIX2'

if marker in screen and marker in main:
    print('Wudroid Save Station Test12 BuildFix2 already applied')
    raise SystemExit(0)

if 'WUDROID_SAVESTATION_TEST12' not in screen:
    raise SystemExit('Save Station Test12 must be applied before BuildFix2')

# ---------------------------------------------------------------------------
# 1) Quick Save / Quick Load: JNI intentionally pauses the title while RAM is
#    copied. Never depend on a drawer animation/effect to resume afterwards.
#    This makes the quick actions self-contained and prevents the reported
#    "fechou/travou" behavior after pressing Salvar rápido.
# ---------------------------------------------------------------------------
def patch_quick_action(text: str, action: str) -> tuple[str, int]:
    start = text.find(f'                        on{action} = {{')
    if start < 0:
        return text, 0
    next_cb = text.find('\n                        on', start + 20)
    if next_cb < 0:
        return text, 0
    block = text[start:next_cb]
    old = '                                if (result == 0) closeDrawer()'
    if old not in block:
        # Already fixed or source changed.
        if 'WUDROID_SAVESTATION_TEST12_BUILDFIX2_QUICK' in block:
            return text, 1
        return text, 0
    new = '''                                // WUDROID_SAVESTATION_TEST12_BUILDFIX2_QUICK
                                // saveQuickState/loadQuickState pause CafeSystem internally.
                                // Resume explicitly; drawer state must never decide native state.
                                runCatching { NativeEmulation.resumeTitle() }
                                isWudroidPaused = false
                                pausedByMenu = false
                                if (result == 0) closeDrawer()'''
    block = block.replace(old, new, 1)
    return text[:start] + block + text[next_cb:], 1

screen, quick_save_count = patch_quick_action(screen, 'QuickSave')
screen, quick_load_count = patch_quick_action(screen, 'QuickLoad')
if quick_save_count != 1:
    raise SystemExit('BuildFix2 QuickSave callback anchor missing')
if quick_load_count != 1:
    raise SystemExit('BuildFix2 QuickLoad callback anchor missing')

# If an old quick state belongs to a dead process, remove it after the attempt
# so the user sees a clean "nothing saved" state next time.
quick_load_start = screen.find('                        onQuickLoad = {')
if quick_load_start >= 0:
    quick_load_end = screen.find('\n                        on', quick_load_start + 20)
    qblock = screen[quick_load_start:quick_load_end]
    needle = '''                                val result = withContext(Dispatchers.IO) {
                                    NativeEmulation.loadQuickState(statePath)
                                }
'''
    if needle in qblock and 'java.io.File(statePath).delete()' not in qblock:
        replacement = needle + '''                                if (result == 5) {
                                    runCatching { java.io.File(statePath).delete() }
                                }
'''
        qblock = qblock.replace(needle, replacement, 1)
        screen = screen[:quick_load_start] + qblock + screen[quick_load_end:]

# ---------------------------------------------------------------------------
# 2) Save Station cards from a dead Android process cannot be restored by the
#    Test10 RAM-only engine. Do not block the user with the old-session toast.
#    Present them as free slots so a tap safely replaces them in the new live
#    session. Same-process/library-return slots remain loadable as before.
# ---------------------------------------------------------------------------
old_slot_meta = '''                            val filled = stateFile.isFile
                            val sameSession = filled && sessionFile.isFile && runCatching {
                                sessionFile.readText().trim() == currentPid
                            }.getOrDefault(false)
                            val dateLabel = if (filled) {
'''
new_slot_meta = '''                            val hasStateFile = stateFile.isFile
                            val sameSession = hasStateFile && sessionFile.isFile && runCatching {
                                sessionFile.readText().trim() == currentPid
                            }.getOrDefault(false)
                            // BuildFix2: an unusable previous-process state is shown as
                            // an empty/reusable slot instead of blocking the whole test.
                            val filled = hasStateFile && sameSession
                            val dateLabel = if (filled) {
'''
if old_slot_meta in screen:
    screen = screen.replace(old_slot_meta, new_slot_meta, 1)
elif 'val hasStateFile = stateFile.isFile' not in screen:
    raise SystemExit('BuildFix2 Save Station slot metadata anchor missing')

# The stale-session branch is now defensive only (for a race between render
# and tap); simplify its message and free the stale files instead of blocking.
old_stale = '''                        if (!sameSession) {
                            snackbarHostState.showSnackbar(
                                "Esse slot foi salvo antes do Wudroid ser fechado completamente"
                            )
                        } else {
'''
new_stale = '''                        if (!sameSession) {
                            withContext(Dispatchers.IO) {
                                stateFile.delete()
                                sessionFile.delete()
                                slotDirectory.resolve("slot_$slot.jpg").delete()
                            }
                            wudroidSaveStationRevision++
                            snackbarHostState.showSnackbar("Ainda não tem nada salvo")
                        } else {
'''
if old_stale in screen:
    screen = screen.replace(old_stale, new_stale, 1)
else:
    # Accept the Test11 wording too, in case a source branch did not receive
    # the Test12 message replacement byte-for-byte.
    alt_stale = '''                        if (!sameSession) {
                            snackbarHostState.showSnackbar(
                                "Slot $slot pertence a outra sessão. Segure para apagar e reutilizar."
                            )
                        } else {
'''
    if alt_stale in screen:
        screen = screen.replace(alt_stale, new_stale, 1)
    elif 'snackbarHostState.showSnackbar("Ainda não tem nada salvo")' not in screen:
        raise SystemExit('BuildFix2 stale Save Station branch anchor missing')

# Mark the screen patch explicitly.
screen = screen.replace(
    'var wudroidMainSurfaceView by remember { mutableStateOf<SurfaceView?>(null) } // WUDROID_SAVESTATION_TEST12',
    'var wudroidMainSurfaceView by remember { mutableStateOf<SurfaceView?>(null) } // WUDROID_SAVESTATION_TEST12 // WUDROID_SAVESTATION_TEST12_BUILDFIX2',
    1,
)

# ---------------------------------------------------------------------------
# 3) First-run setup: expose BOTH selectors directly on the welcome page.
#    We deliberately reuse the existing launchers/copy/permission logic rather
#    than replacing MainActivity, so library/settings behavior stays intact.
# ---------------------------------------------------------------------------
if marker not in main:
    # Find the existing launchers by their ActivityResult contracts.
    def find_launcher(text: str, contract: str):
        # Handles both `val foo = rememberLauncherForActivityResult(` and named
        # contract arguments over multiple lines.
        pat = re.compile(
            r'(?s)(?:val|var)\s+(\w+)\s*=\s*rememberLauncherForActivityResult\s*\(.*?'
            + re.escape(contract) + r'.*?\)\s*\{\s*(\w+)\s*->'
        )
        m = pat.search(text)
        return m

    keys_match = find_launcher(main, 'ActivityResultContracts.OpenDocument')
    folder_match = find_launcher(main, 'ActivityResultContracts.OpenDocumentTree')
    if not keys_match:
        raise SystemExit('BuildFix2 could not locate keys OpenDocument launcher in MainActivity.kt')
    if not folder_match:
        raise SystemExit('BuildFix2 could not locate game-folder OpenDocumentTree launcher in MainActivity.kt')

    keys_launcher, keys_uri = keys_match.group(1), keys_match.group(2)
    folder_launcher, folder_uri = folder_match.group(1), folder_match.group(2)

    # State lives in the same composable scope as the launchers.
    declaration_pos = min(keys_match.start(), folder_match.start())
    line_pos = main.rfind('\n', 0, declaration_pos) + 1
    state_decl = '''    // WUDROID_SAVESTATION_TEST12_BUILDFIX2
    var wudroidSetupKeysSelected by remember { mutableStateOf(false) }
    var wudroidSetupFolderSelected by remember { mutableStateOf(false) }

'''
    main = main[:line_pos] + state_decl + main[line_pos:]

    # Re-find after insertion and set the visual state when the picker returns
    # a real URI. Existing code still performs validation/copy/persisted SAF.
    keys_match = find_launcher(main, 'ActivityResultContracts.OpenDocument')
    folder_match = find_launcher(main, 'ActivityResultContracts.OpenDocumentTree')
    if not keys_match or not folder_match:
        raise SystemExit('BuildFix2 launcher re-scan failed after state insertion')

    keys_arrow = keys_match.end()
    main = main[:keys_arrow] + f'''\n        if ({keys_uri} != null) wudroidSetupKeysSelected = true''' + main[keys_arrow:]

    folder_match = find_launcher(main, 'ActivityResultContracts.OpenDocumentTree')
    folder_arrow = folder_match.end()
    main = main[:folder_arrow] + f'''\n        if ({folder_uri} != null) wudroidSetupFolderSelected = true''' + main[folder_arrow:]

    # Find the welcome description Text(...) and insert compact selectors right
    # under it. The fully-qualified Compose calls avoid import churn.
    welcome_needles = [
        'Antes da primeira inicialização',
        'Bem-vindo ao Wudroid',
    ]
    welcome_pos = -1
    for n in welcome_needles:
        p = main.find(n)
        if p >= 0:
            welcome_pos = p
            if n.startswith('Antes'):
                break
    if welcome_pos < 0:
        raise SystemExit('BuildFix2 welcome screen text anchor missing in MainActivity.kt')

    # Nearest Text( call before the chosen string.
    text_open = main.rfind('Text(', 0, welcome_pos)
    if text_open < 0:
        raise SystemExit('BuildFix2 welcome description Text() anchor missing')

    def match_paren(text: str, open_pos: int) -> int:
        paren = text.find('(', open_pos)
        if paren < 0:
            return -1
        depth = 0
        i = paren
        in_string = False
        escape = False
        while i < len(text):
            ch = text[i]
            if in_string:
                if escape:
                    escape = False
                elif ch == '\\':
                    escape = True
                elif ch == '"':
                    in_string = False
            else:
                if ch == '"':
                    in_string = True
                elif ch == '(':
                    depth += 1
                elif ch == ')':
                    depth -= 1
                    if depth == 0:
                        return i + 1
            i += 1
        return -1

    insert_pos = match_paren(main, text_open)
    if insert_pos < 0:
        raise SystemExit('BuildFix2 could not close welcome Text() call')

    setup_ui = f'''

                // WUDROID_SAVESTATION_TEST12_BUILDFIX2: first-run selectors
                androidx.compose.foundation.layout.Spacer(
                    modifier = androidx.compose.ui.Modifier.height(22.dp)
                )
                androidx.compose.material3.OutlinedButton(
                    onClick = {{ {keys_launcher}.launch(arrayOf("text/plain", "*/*")) }},
                    modifier = androidx.compose.ui.Modifier.fillMaxWidth(),
                ) {{
                    androidx.compose.material3.Text(
                        if (wudroidSetupKeysSelected) "✓ keys.txt selecionado" else "Selecionar keys.txt"
                    )
                }}
                androidx.compose.foundation.layout.Spacer(
                    modifier = androidx.compose.ui.Modifier.height(12.dp)
                )
                androidx.compose.material3.OutlinedButton(
                    onClick = {{ {folder_launcher}.launch(null) }},
                    modifier = androidx.compose.ui.Modifier.fillMaxWidth(),
                ) {{
                    androidx.compose.material3.Text(
                        text = if (wudroidSetupFolderSelected) "✓ Pasta de jogos selecionada" else "Selecionar pasta de jogos",
                        color = if (wudroidSetupFolderSelected)
                            androidx.compose.ui.graphics.Color(0xFF43D17B)
                        else
                            androidx.compose.material3.MaterialTheme.colorScheme.onSurface,
                    )
                }}
'''
    main = main[:insert_pos] + setup_ui + main[insert_pos:]

# Write files.
screen_path.write_text(screen)
main_path.write_text(main)

# ---------------------------------------------------------------------------
# Verification: fail early with precise messages.
# ---------------------------------------------------------------------------
screen_check = screen_path.read_text()
main_check = main_path.read_text()
for needle in (
    'WUDROID_SAVESTATION_TEST12_BUILDFIX2',
    'WUDROID_SAVESTATION_TEST12_BUILDFIX2_QUICK',
    'runCatching { NativeEmulation.resumeTitle() }',
    'val hasStateFile = stateFile.isFile',
    'snackbarHostState.showSnackbar("Ainda não tem nada salvo")',
):
    if needle not in screen_check:
        raise SystemExit(f'BuildFix2 EmulationScreen verification failed: {needle}')

for needle in (
    'WUDROID_SAVESTATION_TEST12_BUILDFIX2',
    'wudroidSetupKeysSelected',
    'wudroidSetupFolderSelected',
    'Selecionar keys.txt',
    'Selecionar pasta de jogos',
    'Pasta de jogos selecionada',
):
    if needle not in main_check:
        raise SystemExit(f'BuildFix2 MainActivity verification failed: {needle}')

print('Wudroid 0.1.1 Save Station Test12 BuildFix2 applied')
print('- Quick Save/Load explicitly resume native title after RAM snapshot operation')
print('- stale previous-process Save Station slots no longer block testing')
print('- welcome screen exposes keys.txt + game-folder selectors together')
print('- folder selector gets immediate green selected feedback')
