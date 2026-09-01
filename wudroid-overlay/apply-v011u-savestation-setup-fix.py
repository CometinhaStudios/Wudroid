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
marker = 'WUDROID_SAVESTATION_TEST12_BUILDFIX3'

if marker in screen and marker in main:
    print('Wudroid Save Station Test12 BuildFix3 already applied')
    raise SystemExit(0)

if 'WUDROID_SAVESTATION_TEST12' not in screen:
    raise SystemExit('Save Station Test12 must be applied before BuildFix3')

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
        if 'WUDROID_SAVESTATION_TEST12_BUILDFIX3_QUICK' in block:
            return text, 1
        return text, 0
    new = '''                                // WUDROID_SAVESTATION_TEST12_BUILDFIX3_QUICK
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
    raise SystemExit('BuildFix3 QuickSave callback anchor missing')
if quick_load_count != 1:
    raise SystemExit('BuildFix3 QuickLoad callback anchor missing')

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
                            // BuildFix3: an unusable previous-process state is shown as
                            // an empty/reusable slot instead of blocking the whole test.
                            val filled = hasStateFile && sameSession
                            val dateLabel = if (filled) {
'''
if old_slot_meta in screen:
    screen = screen.replace(old_slot_meta, new_slot_meta, 1)
elif 'val hasStateFile = stateFile.isFile' not in screen:
    raise SystemExit('BuildFix3 Save Station slot metadata anchor missing')

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
        raise SystemExit('BuildFix3 stale Save Station branch anchor missing')

# Mark the screen patch explicitly.
screen = screen.replace(
    'var wudroidMainSurfaceView by remember { mutableStateOf<SurfaceView?>(null) } // WUDROID_SAVESTATION_TEST12',
    'var wudroidMainSurfaceView by remember { mutableStateOf<SurfaceView?>(null) } // WUDROID_SAVESTATION_TEST12 // WUDROID_SAVESTATION_TEST12_BUILDFIX3',
    1,
)

# ---------------------------------------------------------------------------
# 3) First-run setup BuildFix3
#
# BuildFix3 injected launcher references beside the welcome text even though
# the launchers live in WudroidRoot() and the welcome UI lives in SetupWizard().
# BuildFix3 keeps launchers/state in WudroidRoot and passes only callbacks and
# booleans to SetupWizard, which is the scope-safe design already used here.
# ---------------------------------------------------------------------------
if marker not in main:
    keys_state_anchor = '    var keysMessage by remember { mutableStateOf<String?>(null) }\n'
    keys_state_insert = '''    var keysMessage by remember { mutableStateOf<String?>(null) }
    // WUDROID_SAVESTATION_TEST12_BUILDFIX3
    var wudroidSetupKeysSelected by remember { mutableStateOf(hasImportedKeys()) }
    var wudroidSetupFolderSelected by remember { mutableStateOf(safeGamePaths().isNotEmpty()) }
'''
    if keys_state_anchor in main:
        main = main.replace(keys_state_anchor, keys_state_insert, 1)
    elif 'var wudroidSetupKeysSelected' not in main:
        raise SystemExit('BuildFix3 keys setup-state anchor missing')

    keys_callback_old = '''            val result = importKeysFile(context, uri)
            keysMessage = result.second
'''
    keys_callback_new = '''            val result = importKeysFile(context, uri)
            keysMessage = result.second
            if (result.first) wudroidSetupKeysSelected = true
'''
    if keys_callback_old in main:
        main = main.replace(keys_callback_old, keys_callback_new, 1)
    elif 'if (result.first) wudroidSetupKeysSelected = true' not in main:
        raise SystemExit('BuildFix3 keys launcher callback anchor missing')

    folder_callback_old = '''        if (uri != null && addGameFolder(context, uri)) {
            // Do not reload native titles inside the SAF callback.
            // Let the ViewModel refresh after the picker has returned.
            refreshLibraryRequest++
        }
'''
    folder_callback_new = '''        if (uri != null && addGameFolder(context, uri)) {
            // BuildFix3: update SetupWizard immediately after a valid SAF folder.
            wudroidSetupFolderSelected = true
            // Do not reload native titles inside the SAF callback.
            // Let the ViewModel refresh after the picker has returned.
            refreshLibraryRequest++
        }
'''
    if folder_callback_old in main:
        main = main.replace(folder_callback_old, folder_callback_new, 1)
    elif 'wudroidSetupFolderSelected = true' not in main:
        raise SystemExit('BuildFix3 folder launcher callback anchor missing')

    setup_args_old = '''            keysPresent = hasImportedKeys(),
            gameFolderPresent = safeGamePaths().isNotEmpty(),
'''
    setup_args_new = '''            keysPresent = wudroidSetupKeysSelected || hasImportedKeys(),
            gameFolderPresent = wudroidSetupFolderSelected || safeGamePaths().isNotEmpty(),
'''
    if setup_args_old in main:
        main = main.replace(setup_args_old, setup_args_new, 1)
    elif 'keysPresent = wudroidSetupKeysSelected || hasImportedKeys()' not in main:
        raise SystemExit('BuildFix3 SetupWizard argument anchor missing')

    welcome_cards_old = '''                        Spacer(Modifier.height(18.dp))
                        StatusPill("Emulador", true, "Core ARM64 / Vulkan pronto")
                        Spacer(Modifier.height(10.dp))
                        StatusPill("Interface", true, "Frontend Wudroid")
'''
    welcome_cards_new = '''                        Spacer(Modifier.height(18.dp))
                        SetupActionCard(
                            icon = WIcon.Key,
                            title = "Selecionar keys.txt",
                            subtitle = if (currentKeysPresent)
                                "Arquivo importado e validado"
                            else
                                "Necessário para jogos WUD/WUX",
                            good = currentKeysPresent,
                            onClick = onImportKeys
                        )
                        if (keysMessage != null) {
                            Spacer(Modifier.height(8.dp))
                            Text(
                                keysMessage,
                                color = if (currentKeysPresent) WGreen else WRed,
                                fontSize = 12.sp,
                                maxLines = 2,
                                overflow = TextOverflow.Ellipsis,
                            )
                        }
                        Spacer(Modifier.height(10.dp))
                        SetupActionCard(
                            icon = WIcon.Folder,
                            title = "Selecionar pasta de jogos",
                            subtitle = if (currentFolderPresent)
                                "Pasta de jogos selecionada"
                            else
                                "Nenhuma pasta configurada",
                            good = currentFolderPresent,
                            onClick = onChooseFolder
                        )
'''
    if welcome_cards_old in main:
        main = main.replace(welcome_cards_old, welcome_cards_new, 1)
    elif 'title = "Selecionar pasta de jogos"' not in main:
        raise SystemExit('BuildFix3 welcome selector-card anchor missing')

    next_old = '''                    onClick = {
                        if (step < 3) step++ else onFinish()
                    },
'''
    next_new = '''                    onClick = {
                        if (step == 0) step = 3 else onFinish()
                    },
'''
    if next_old in main:
        main = main.replace(next_old, next_new, 1)
    elif 'if (step == 0) step = 3 else onFinish()' not in main:
        raise SystemExit('BuildFix3 setup next-button anchor missing')

    back_old = '                        onClick = { step-- },\n'
    back_new = '                        onClick = { step = 0 },\n'
    if back_old in main:
        main = main.replace(back_old, back_new, 1)

# Write files.
screen_path.write_text(screen)
main_path.write_text(main)

# ---------------------------------------------------------------------------
# Verification: fail early with precise messages.
# ---------------------------------------------------------------------------
screen_check = screen_path.read_text()
main_check = main_path.read_text()
for needle in (
    'WUDROID_SAVESTATION_TEST12_BUILDFIX3',
    'WUDROID_SAVESTATION_TEST12_BUILDFIX3_QUICK',
    'runCatching { NativeEmulation.resumeTitle() }',
    'val hasStateFile = stateFile.isFile',
    'snackbarHostState.showSnackbar("Ainda não tem nada salvo")',
):
    if needle not in screen_check:
        raise SystemExit(f'BuildFix3 EmulationScreen verification failed: {needle}')

for needle in (
    'WUDROID_SAVESTATION_TEST12_BUILDFIX3',
    'wudroidSetupKeysSelected',
    'wudroidSetupFolderSelected',
    'Selecionar keys.txt',
    'Selecionar pasta de jogos',
    'Pasta de jogos selecionada',
):
    if needle not in main_check:
        raise SystemExit(f'BuildFix3 MainActivity verification failed: {needle}')

print('Wudroid 0.1.1 Save Station Test12 BuildFix3 applied')
print('- Quick Save/Load explicitly resume native title after RAM snapshot operation')
print('- stale previous-process Save Station slots no longer block testing')
print('- welcome screen exposes keys.txt + game-folder selectors together (scope-safe)')
print('- folder selector gets immediate green selected feedback')
