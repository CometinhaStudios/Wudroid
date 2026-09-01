#!/usr/bin/env python3
from pathlib import Path
import re

screen_path = Path('cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationScreen.kt')
activity_path = Path('cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationActivity.kt')
viewmodel_path = Path('cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationViewModel.kt')
native_kt_path = Path('cemu-engine/src/android/app/src/main/java/info/cemu/cemu/nativeinterface/NativeEmulation.kt')
native_cpp_path = Path('cemu-engine/src/android/app/src/main/cpp/NativeEmulation.cpp')

for p in (screen_path, activity_path, viewmodel_path, native_kt_path, native_cpp_path):
    if not p.exists():
        raise SystemExit(f'Required source not found: {p}')

screen = screen_path.read_text()
activity = activity_path.read_text()
viewmodel = viewmodel_path.read_text()
native_kt = native_kt_path.read_text()
native_cpp = native_cpp_path.read_text()

marker = 'WUDROID_SAVESTATION_TEST12'
if marker in screen:
    print('Wudroid Save Station Test12 already applied')
    raise SystemExit(0)
if 'WUDROID_SAVESTATION_TEST11' not in screen:
    raise SystemExit('Save Station Test11 must be applied before Test12')

# ---------------------------------------------------------------------------
# 1) Quick State stays disposable. Old quick states should look empty instead
#    of exposing the internal process/session limitation to the user.
# ---------------------------------------------------------------------------
screen = screen.replace(
    '4 -> "Nenhum estado rápido encontrado"\n                                        5 -> "Este estado pertence a outra sessão do Wudroid"',
    '4 -> "Ainda não tem nada salvo"\n                                        5 -> "Ainda não tem nada salvo"',
    1,
)

# ---------------------------------------------------------------------------
# 2) Keep the native Cemu title alive when leaving emulation for the library.
#    The old build called exitProcess(0), guaranteeing that every slot became
#    "previous session". Test12 pauses + finishes only. Reopening the same game
#    reattaches to the same native title; opening a different game shuts down
#    the old title cleanly and launches the requested one in the same process.
# ---------------------------------------------------------------------------
if 'import info.cemu.cemu.nativeinterface.NativeEmulation' not in activity:
    activity = activity.replace(
        'import info.cemu.cemu.emulation.input.NativeInputDeviceListener\n',
        'import info.cemu.cemu.emulation.input.NativeInputDeviceListener\nimport info.cemu.cemu.nativeinterface.NativeEmulation\n',
        1,
    )
activity = activity.replace('import kotlin.system.exitProcess\n', '', 1)
old_quit = '''    private fun onQuit() {
        WudroidKeyboardMouse.reset()
        finish()
        exitProcess(0)
    }
'''
new_quit = '''    private fun onQuit() {
        WudroidKeyboardMouse.reset()
        // WUDROID_SAVESTATION_TEST12: leaving emulation no longer kills the
        // process. Keeping Cemu alive preserves the exact native session so a
        // Save Station slot can still be loaded after returning from library.
        if (runCatching { NativeEmulation.isTitleRunning() }.getOrDefault(false)) {
            NativeEmulation.pauseTitle()
            WudroidEmulationSession.markSuspended(getGamePath())
        }
        finish()
    }
'''
if old_quit not in activity:
    raise SystemExit('EmulationActivity onQuit anchor missing')
activity = activity.replace(old_quit, new_quit, 1)

# Native lifecycle JNI bridge.
kt_anchor = '''    @JvmStatic
    external fun resumeTitle()
'''
if kt_anchor not in native_kt:
    raise SystemExit('NativeEmulation.kt resumeTitle anchor missing')
if 'external fun isTitleRunning()' not in native_kt:
    native_kt = native_kt.replace(
        kt_anchor,
        kt_anchor + '''
    // WUDROID_SAVESTATION_TEST12
    @JvmStatic
    external fun isTitleRunning(): Boolean

    @JvmStatic
    external fun shutdownTitle()
''',
        1,
    )

jni_lifecycle = r'''

// WUDROID_SAVESTATION_TEST12
extern "C" [[maybe_unused]] JNIEXPORT jboolean JNICALL
Java_info_cemu_cemu_nativeinterface_NativeEmulation_isTitleRunning(
    [[maybe_unused]] JNIEnv* env, [[maybe_unused]] jclass clazz)
{
    return CafeSystem::IsTitleRunning();
}

extern "C" [[maybe_unused]] JNIEXPORT void JNICALL
Java_info_cemu_cemu_nativeinterface_NativeEmulation_shutdownTitle(
    [[maybe_unused]] JNIEnv* env, [[maybe_unused]] jclass clazz)
{
    if (CafeSystem::IsTitleRunning())
        CafeSystem::ShutdownTitle();
}
'''
if 'Java_info_cemu_cemu_nativeinterface_NativeEmulation_isTitleRunning' not in native_cpp:
    native_cpp = native_cpp.rstrip() + jni_lifecycle + '\n'

# ViewModel initialization becomes process-session aware. Systems/renderer are
# initialized once; same-game return only reuses and resumes the live title.
old_init = '''    fun initializeEmulation() {
        if (_isEmulationInitialized.value || emulationInitializationJob != null) {
            return
        }
        emulationInitializationJob = viewModelScope.launch {
            prepareTitle()
                .bind { initializeSystems() }
                .bind { initializeRenderer() }
                .bind { launchTitle() }
                .onError { _emulationError.value = it }

            _isEmulationInitialized.value = true
        }
    }
'''
new_init = '''    private suspend fun initializeWudroidSystemsOnce(): Either<Unit, NativeError> {
        if (WudroidEmulationSession.systemsInitialized) return Success(Unit)
        return initializeSystems().fold(
            onSuccess = {
                WudroidEmulationSession.systemsInitialized = true
                Success(Unit)
            },
            onError = { Error(it) },
        )
    }

    private suspend fun initializeWudroidRendererOnce(): Either<Unit, NativeError> {
        if (WudroidEmulationSession.rendererInitialized) return Success(Unit)
        return initializeRenderer().fold(
            onSuccess = {
                WudroidEmulationSession.rendererInitialized = true
                Success(Unit)
            },
            onError = { Error(it) },
        )
    }

    fun initializeEmulation() {
        if (_isEmulationInitialized.value || emulationInitializationJob != null) {
            return
        }
        emulationInitializationJob = viewModelScope.launch {
            val canResume = WudroidEmulationSession.canResume(launchPath) &&
                NativeEmulation.isTitleRunning()

            if (canResume) {
                NativeEmulation.resumeTitle()
                WudroidEmulationSession.markResumed()
                _isEmulationInitialized.value = true
                return@launch
            }

            // A different game was left suspended. Cemu supports shutting down
            // a foreground title without destroying the whole process/renderer.
            if (NativeEmulation.isTitleRunning()) {
                NativeEmulation.shutdownTitle()
                WudroidEmulationSession.clearTitle()
            }

            val result = prepareTitle()
                .bind { initializeWudroidSystemsOnce() }
                .bind { initializeWudroidRendererOnce() }
                .bind { launchTitle() }

            var launchedSuccessfully = false
            result.fold(
                onSuccess = { launchedSuccessfully = true },
                onError = { _emulationError.value = it },
            )
            if (launchedSuccessfully) {
                WudroidEmulationSession.markLaunched(launchPath)
                _isEmulationInitialized.value = true
            }
        }
    }
'''
if old_init not in viewmodel:
    raise SystemExit('EmulationViewModel initializeEmulation anchor missing')
viewmodel = viewmodel.replace(old_init, new_init, 1)

# ---------------------------------------------------------------------------
# 3) Capture the actual game SurfaceView for slot thumbnails.
#    PixelCopy reads the SurfaceView itself, so the Save Station dialog and
#    touch overlay are not baked into the preview image.
# ---------------------------------------------------------------------------
imports = [
    'import android.graphics.Bitmap',
    'import android.graphics.BitmapFactory',
    'import android.os.Handler',
    'import android.os.Looper',
    'import android.view.PixelCopy',
    'import androidx.compose.foundation.Image',
    'import androidx.compose.ui.graphics.asImageBitmap',
    'import androidx.compose.ui.layout.ContentScale',
    'import androidx.compose.ui.window.DialogProperties',
    'import kotlinx.coroutines.suspendCancellableCoroutine',
    'import kotlin.coroutines.resume',
]
for imp in imports:
    if imp not in screen:
        screen = screen.replace('package info.cemu.cemu.emulation\n', 'package info.cemu.cemu.emulation\n' + imp + '\n', 1)

state_anchor = '''    val wudroidSaveStationGameKey = remember(gamePath) {
        java.lang.Integer.toHexString(gamePath.hashCode())
    }
'''
if state_anchor not in screen:
    raise SystemExit('Save Station game-key state anchor missing')
screen = screen.replace(
    state_anchor,
    state_anchor + '    var wudroidMainSurfaceView by remember { mutableStateOf<SurfaceView?>(null) } // WUDROID_SAVESTATION_TEST12\n',
    1,
)

# Wire SurfaceView reference out of EmulationSurfaces.
call_anchor = '            onInitializeEmulation = viewModel::initializeEmulation,\n'
if call_anchor not in screen:
    raise SystemExit('EmulationSurfaces call anchor missing')
screen = screen.replace(
    call_anchor,
    call_anchor + '            onMainSurfaceViewReady = { wudroidMainSurfaceView = it },\n',
    1,
)

sig_old = '''    padHolderCallback: SurfaceHolder.Callback,
    onInitializeEmulation: () -> Unit
) {
'''
sig_new = '''    padHolderCallback: SurfaceHolder.Callback,
    onInitializeEmulation: () -> Unit,
    onMainSurfaceViewReady: (SurfaceView) -> Unit,
) {
'''
if sig_old not in screen:
    raise SystemExit('EmulationSurfaces signature anchor missing')
screen = screen.replace(sig_old, sig_new, 1)

main_surface_old = '''            holderCallback = mainHolderCallback,
            afterInit = { onInitializeEmulation() },
        )
'''
main_surface_new = '''            holderCallback = mainHolderCallback,
            afterInit = { onInitializeEmulation() },
            onSurfaceViewReady = onMainSurfaceViewReady,
        )
'''
if main_surface_old not in screen:
    raise SystemExit('MainSurface callback anchor missing')
screen = screen.replace(main_surface_old, main_surface_new, 1)

surface_sig_old = '''    holderCallback: SurfaceHolder.Callback,
    afterInit: () -> Unit = {}
) {
'''
surface_sig_new = '''    holderCallback: SurfaceHolder.Callback,
    afterInit: () -> Unit = {},
    onSurfaceViewReady: (SurfaceView) -> Unit = {},
) {
'''
if surface_sig_old not in screen:
    raise SystemExit('EmulationSurface signature anchor missing')
screen = screen.replace(surface_sig_old, surface_sig_new, 1)

factory_anchor = '''            SurfaceView(context).apply {
                var firstChange = true
'''
if factory_anchor not in screen:
    raise SystemExit('SurfaceView factory anchor missing')
screen = screen.replace(
    factory_anchor,
    '''            SurfaceView(context).apply {
                onSurfaceViewReady(this)
                var firstChange = true
''',
    1,
)

# Save operation: capture thumbnail from the TV SurfaceView alongside state.
old_save_body = '''                        val stateFile = slotDirectory.resolve("slot_$slot.wstate")
                        val sessionFile = slotDirectory.resolve("slot_$slot.session")
                        val result = withContext(Dispatchers.IO) {
                            slotDirectory.mkdirs()
                            val code = NativeEmulation.saveQuickState(stateFile.absolutePath)
                            if (code == 0) {
                                sessionFile.writeText(android.os.Process.myPid().toString())
                            }
                            code
                        }
'''
new_save_body = '''                        val stateFile = slotDirectory.resolve("slot_$slot.wstate")
                        val sessionFile = slotDirectory.resolve("slot_$slot.session")
                        val thumbnailFile = slotDirectory.resolve("slot_$slot.jpg")
                        slotDirectory.mkdirs()
                        val thumbnailSaved = captureWudroidSaveThumbnail(
                            wudroidMainSurfaceView,
                            thumbnailFile,
                        )
                        val result = withContext(Dispatchers.IO) {
                            val code = NativeEmulation.saveQuickState(stateFile.absolutePath)
                            if (code == 0) {
                                sessionFile.writeText(android.os.Process.myPid().toString())
                            } else if (thumbnailSaved) {
                                thumbnailFile.delete()
                            }
                            code
                        }
'''
if old_save_body not in screen:
    raise SystemExit('Save Station save operation anchor missing')
screen = screen.replace(old_save_body, new_save_body, 1)

# Load operation: stale PID still cannot be restored after actual Android
# process death, but normal exit-to-library now preserves PID/native title.
# Most importantly, successful load explicitly resumes the title instead of
# depending on a Compose effect race (the freeze reported in Test11).
old_load_tail = '''                            if (result == 0) showWudroidSaveStation = false
'''
new_load_tail = '''                            if (result == 0) {
                                showWudroidSaveStation = false
                                pausedByMenu = false
                                isWudroidPaused = false
                                NativeEmulation.resumeTitle()
                            }
'''
if old_load_tail not in screen:
    raise SystemExit('Save Station successful-load anchor missing')
screen = screen.replace(old_load_tail, new_load_tail, 1)

old_other_session = '''                            snackbarHostState.showSnackbar(
                                "Slot $slot pertence a outra sessão. Segure para apagar e reutilizar."
                            )
'''
new_other_session = '''                            snackbarHostState.showSnackbar(
                                "Esse slot foi salvo antes do Wudroid ser fechado completamente"
                            )
'''
if old_other_session in screen:
    screen = screen.replace(old_other_session, new_other_session, 1)

# Delete thumbnail with the state.
screen = screen.replace(
    '''                            slotDirectory.resolve("slot_$slot.session").delete()
''',
    '''                            slotDirectory.resolve("slot_$slot.session").delete()
                            slotDirectory.resolve("slot_$slot.jpg").delete()
''',
    1,
)

# ---------------------------------------------------------------------------
# 4) Replace Test11 placeholder UI with the wider Test12 dialog + real image.
# ---------------------------------------------------------------------------
functions_re = re.compile(
    r'@Composable\nprivate fun WudroidSaveStationDialog\(.*?(?=@Composable\nprivate fun EmulationQuitConfirmationDialog\()',
    re.S,
)
new_functions = r'''private suspend fun captureWudroidSaveThumbnail(
    surfaceView: SurfaceView?,
    outputFile: java.io.File,
): Boolean {
    if (surfaceView == null || !surfaceView.isAttachedToWindow ||
        surfaceView.width <= 0 || surfaceView.height <= 0 ||
        android.os.Build.VERSION.SDK_INT < android.os.Build.VERSION_CODES.N
    ) {
        return false
    }

    val source = Bitmap.createBitmap(
        surfaceView.width,
        surfaceView.height,
        Bitmap.Config.ARGB_8888,
    )
    val copied = suspendCancellableCoroutine<Boolean> { continuation ->
        PixelCopy.request(
            surfaceView,
            source,
            { result ->
                if (continuation.isActive) {
                    continuation.resume(result == PixelCopy.SUCCESS)
                }
            },
            Handler(Looper.getMainLooper()),
        )
    }
    if (!copied) {
        source.recycle()
        return false
    }

    return withContext(Dispatchers.IO) {
        runCatching {
            outputFile.parentFile?.mkdirs()
            val targetWidth = 480
            val targetHeight = (source.height.toFloat() / source.width.toFloat() * targetWidth)
                .toInt()
                .coerceAtLeast(1)
            val scaled = Bitmap.createScaledBitmap(source, targetWidth, targetHeight, true)
            outputFile.outputStream().buffered().use { output ->
                scaled.compress(Bitmap.CompressFormat.JPEG, 82, output)
            }
            if (scaled !== source) scaled.recycle()
            source.recycle()
            true
        }.getOrElse {
            source.recycle()
            false
        }
    }
}

@Composable
private fun WudroidSaveStationDialog(
    directory: java.io.File,
    revision: Int,
    busy: Boolean,
    onDismiss: () -> Unit,
    onSaveSlot: (Int) -> Unit,
    onLoadSlot: (Int) -> Unit,
    onDeleteSlot: (Int) -> Unit,
) {
    val refreshRevision = revision
    val currentPid = android.os.Process.myPid().toString()
    val formatter = remember(refreshRevision) {
        java.text.SimpleDateFormat("dd/MM/yyyy  HH:mm", java.util.Locale.getDefault())
    }

    Dialog(
        onDismissRequest = onDismiss,
        properties = DialogProperties(usePlatformDefaultWidth = false),
    ) {
        Surface(
            modifier = Modifier
                .fillMaxWidth(0.60f)
                .widthIn(max = 980.dp),
            shape = RoundedCornerShape(22.dp),
            color = WudroidDrawerBackground,
            border = BorderStroke(1.dp, WudroidDrawerOutline),
            shadowElevation = 14.dp,
        ) {
            Column(modifier = Modifier.padding(horizontal = 20.dp, vertical = 16.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = "SAVE STATION",
                            color = WudroidCyan,
                            fontSize = 20.sp,
                            fontWeight = FontWeight.Bold,
                        )
                        Text(
                            text = "6 slots • 3 × 2",
                            color = WudroidDrawerMuted,
                            fontSize = 11.sp,
                        )
                    }
                    TextButton(onClick = onDismiss, enabled = !busy) {
                        Text("Fechar", color = WudroidDrawerText)
                    }
                }

                Text(
                    text = if (busy) {
                        "Processando estado..."
                    } else {
                        "Vazio: toque para salvar • Salvo: toque para carregar • Segure para apagar"
                    },
                    color = if (busy) WudroidCyan else WudroidDrawerMuted,
                    fontSize = 10.sp,
                    modifier = Modifier.padding(top = 4.dp, bottom = 12.dp),
                )

                for (row in 0 until 2) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(12.dp),
                    ) {
                        for (column in 0 until 3) {
                            val slot = row * 3 + column + 1
                            val stateFile = directory.resolve("slot_$slot.wstate")
                            val sessionFile = directory.resolve("slot_$slot.session")
                            val thumbnailFile = directory.resolve("slot_$slot.jpg")
                            val filled = stateFile.isFile
                            val sameSession = filled && sessionFile.isFile && runCatching {
                                sessionFile.readText().trim() == currentPid
                            }.getOrDefault(false)
                            val dateLabel = if (filled) {
                                formatter.format(java.util.Date(stateFile.lastModified()))
                            } else {
                                "Slot vazio"
                            }
                            val thumbnail = remember(
                                refreshRevision,
                                thumbnailFile.absolutePath,
                                thumbnailFile.lastModified(),
                            ) {
                                if (thumbnailFile.isFile) {
                                    BitmapFactory.decodeFile(thumbnailFile.absolutePath)?.asImageBitmap()
                                } else {
                                    null
                                }
                            }

                            WudroidSaveSlotCard(
                                modifier = Modifier.weight(1f),
                                slot = slot,
                                filled = filled,
                                sameSession = sameSession,
                                dateLabel = dateLabel,
                                thumbnail = thumbnail,
                                busy = busy,
                                onTap = {
                                    if (!busy) {
                                        if (filled) onLoadSlot(slot) else onSaveSlot(slot)
                                    }
                                },
                                onLongPress = {
                                    if (!busy && filled) onDeleteSlot(slot)
                                },
                            )
                        }
                    }
                    if (row == 0) {
                        androidx.compose.foundation.layout.Spacer(
                            modifier = Modifier.padding(top = 12.dp)
                        )
                    }
                }

                Text(
                    text = "Os slots continuam disponíveis ao sair da emulação e voltar ao mesmo jogo.",
                    color = WudroidDrawerMuted,
                    fontSize = 9.sp,
                    modifier = Modifier.padding(top = 10.dp),
                )
            }
        }
    }
}

@Composable
private fun WudroidSaveSlotCard(
    modifier: Modifier,
    slot: Int,
    filled: Boolean,
    sameSession: Boolean,
    dateLabel: String,
    thumbnail: androidx.compose.ui.graphics.ImageBitmap?,
    busy: Boolean,
    onTap: () -> Unit,
    onLongPress: () -> Unit,
) {
    Surface(
        modifier = modifier
            .aspectRatio(1.45f)
            .pointerInput(slot, filled, busy) {
                detectTapGestures(
                    onTap = { if (!busy) onTap() },
                    onLongPress = { if (!busy && filled) onLongPress() },
                )
            },
        shape = RoundedCornerShape(15.dp),
        color = if (filled) WudroidDrawerSurfacePressed else WudroidDrawerSurface,
        border = BorderStroke(
            width = if (filled) 1.5.dp else 1.dp,
            color = if (filled && sameSession) WudroidCyan else WudroidDrawerOutline,
        ),
    ) {
        Column(
            modifier = Modifier.padding(9.dp),
            verticalArrangement = Arrangement.SpaceBetween,
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    text = "SLOT $slot",
                    color = if (filled) WudroidCyan else WudroidDrawerText,
                    fontWeight = FontWeight.Bold,
                    fontSize = 12.sp,
                    modifier = Modifier.weight(1f),
                )
                Text(
                    text = if (filled) "●" else "+",
                    color = if (filled && sameSession) WudroidCyan else WudroidDrawerMuted,
                    fontSize = 13.sp,
                )
            }

            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f)
                    .padding(vertical = 6.dp)
                    .background(WudroidDrawerBackground, RoundedCornerShape(9.dp)),
                contentAlignment = Alignment.Center,
            ) {
                if (filled && thumbnail != null) {
                    Image(
                        bitmap = thumbnail,
                        contentDescription = "Captura do slot $slot",
                        modifier = Modifier.fillMaxSize(),
                        contentScale = ContentScale.Crop,
                    )
                } else {
                    Text(
                        text = if (filled) "SALVO" else "SALVAR",
                        color = if (filled && sameSession) WudroidCyan else WudroidDrawerMuted,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                    )
                }
            }

            Text(
                text = dateLabel,
                color = WudroidDrawerMuted,
                fontSize = 8.sp,
                maxLines = 1,
            )
        }
    }
}

'''
screen, count = functions_re.subn(new_functions, screen, count=1)
if count != 1:
    raise SystemExit('Save Station function region replacement failed')

# Marker near state block for quick verification.
screen = screen.replace(
    'var wudroidMainSurfaceView by remember { mutableStateOf<SurfaceView?>(null) } // WUDROID_SAVESTATION_TEST12',
    'var wudroidMainSurfaceView by remember { mutableStateOf<SurfaceView?>(null) } // WUDROID_SAVESTATION_TEST12',
    1,
)

screen_path.write_text(screen)
activity_path.write_text(activity)
viewmodel_path.write_text(viewmodel)
native_kt_path.write_text(native_kt)
native_cpp_path.write_text(native_cpp)

# Fail in Apply if any important Test12 piece did not land.
checks = {
    screen_path: [
        marker,
        'properties = DialogProperties(usePlatformDefaultWidth = false)',
        '.fillMaxWidth(0.60f)',
        'captureWudroidSaveThumbnail(',
        'PixelCopy.request(',
        'BitmapFactory.decodeFile(',
        'contentDescription = "Captura do slot $slot"',
        'NativeEmulation.resumeTitle()',
        '4 -> "Ainda não tem nada salvo"',
        '5 -> "Ainda não tem nada salvo"',
    ],
    activity_path: [
        'NativeEmulation.isTitleRunning()',
        'WudroidEmulationSession.markSuspended(getGamePath())',
    ],
    viewmodel_path: [
        'WudroidEmulationSession.canResume(launchPath)',
        'NativeEmulation.shutdownTitle()',
        'initializeWudroidRendererOnce()',
        'WudroidEmulationSession.markLaunched(launchPath)',
    ],
    native_kt_path: [
        'external fun isTitleRunning(): Boolean',
        'external fun shutdownTitle()',
    ],
    native_cpp_path: [
        'CafeSystem::IsTitleRunning()',
        'CafeSystem::ShutdownTitle()',
    ],
}
for path, needles in checks.items():
    text = path.read_text()
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise SystemExit(f'Test12 verification failed for {path}: {missing}')

if 'exitProcess(0)' in activity_path.read_text():
    raise SystemExit('Test12 regression: EmulationActivity still kills process on normal quit')

print('Wudroid 0.1.1 Save Station Test12 applied')
print('- quick load old-session message simplified to Ainda não tem nada salvo')
print('- leaving emulation preserves the native Cemu session instead of killing process')
print('- returning to same game reattaches/resumes live title')
print('- switching games shuts down previous title without killing the app process')
print('- successful slot load explicitly resumes title (Test11 freeze fix)')
print('- Save Station widened for landscape')
print('- real gameplay thumbnails captured from SurfaceView using PixelCopy')
