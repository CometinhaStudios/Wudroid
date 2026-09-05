#!/usr/bin/env python3
from pathlib import Path

screen_path = Path("cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationScreen.kt")
if not screen_path.exists():
    raise SystemExit("TV RuntimeFix1: EmulationScreen.kt missing")

s = screen_path.read_text()
marker = "WUDROID_TV_MODE_TEST1_RUNTIMEFIX1"
if marker in s:
    print("Wudroid TV Test1 RuntimeFix1 already applied")
    raise SystemExit(0)

required = [
    "WUDROID_TV_MODE_TEST1",
    "fun stopWudroidTvMode()",
    "fun startWudroidTvMode(mode: String, display: Display)",
    "viewModel.mainHolderCallback",
]
missing = [x for x in required if x not in s]
if missing:
    raise SystemExit("TV RuntimeFix1: required TV Test1 base missing: " + ", ".join(missing))

old = r'''    fun stopWudroidTvMode() {
        runCatching { wudroidTvPresentation?.dismiss() }
        wudroidTvPresentation = null
        wudroidTvActive = false
        wudroidTvSelectedDisplayId = -1
        if (wudroidTvPreviousControllerType >= 0) {
            runCatching { NativeInput.setControllerType(0, wudroidTvPreviousControllerType) }
            wudroidTvPreviousControllerType = -1
        }
        (wudroidQuickStateContext as? Activity)?.requestedOrientation = ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED
        setMotionSensorEnabled(sideMenuState.isMotionEnabled)
    }

    fun startWudroidTvMode(mode: String, display: Display) {
        runCatching { wudroidTvPresentation?.dismiss() }
        if (mode == "MOTION") {
            if (wudroidTvPreviousControllerType < 0) {
                wudroidTvPreviousControllerType = runCatching { NativeInput.getControllerType(0) }
                    .getOrDefault(NativeInput.EmulatedControllerType.WIIMOTE)
            }
            runCatching { NativeInput.setControllerType(0, NativeInput.EmulatedControllerType.WIIMOTE) }
            setMotionSensorEnabled(true)
            (wudroidQuickStateContext as? Activity)?.requestedOrientation = ActivityInfo.SCREEN_ORIENTATION_PORTRAIT
        } else {
            if (wudroidTvPreviousControllerType >= 0) {
                runCatching { NativeInput.setControllerType(0, wudroidTvPreviousControllerType) }
                wudroidTvPreviousControllerType = -1
            }
            (wudroidQuickStateContext as? Activity)?.requestedOrientation = ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED
            setMotionSensorEnabled(sideMenuState.isMotionEnabled)
        }

        wudroidTvMode = mode
        wudroidTvSelectedDisplayId = display.displayId
        wudroidTvActive = true
        showWudroidTvPickerDialog = false

        val presentation = WudroidTvPresentation(
            wudroidQuickStateContext,
            display,
            viewModel.mainHolderCallback,
        )
        wudroidTvPresentation = presentation
        scope.launch {
            // Give Compose one frame to remove the phone TV Surface before
            // attaching Cemu's main framebuffer to the external display.
            delay(180)
            runCatching { presentation.show() }.onFailure {
                stopWudroidTvMode()
                snackbarHostState.showSnackbar("Não foi possível abrir a TV selecionada")
            }
        }
    }
'''

new = r'''    // WUDROID_TV_MODE_TEST1_RUNTIMEFIX1
    fun stopWudroidTvMode() {
        // Mark the external main surface as released BEFORE the phone TV surface
        // is recreated. This lets Cemu's normal holder callback bind the phone
        // again without being blocked by setSurfaces.
        if (wudroidTvActive) {
            runCatching { NativeEmulation.pauseTitle() }
            viewModel.setSurfaces.set(isMain = true, value = false)
            viewModel.destroyedSurfaces.set(isMain = true, value = true)
        }
        runCatching { wudroidTvPresentation?.dismiss() }
        wudroidTvPresentation = null
        wudroidTvActive = false
        wudroidTvSelectedDisplayId = -1
        if (wudroidTvPreviousControllerType >= 0) {
            runCatching { NativeInput.setControllerType(0, wudroidTvPreviousControllerType) }
            wudroidTvPreviousControllerType = -1
        }
        (wudroidQuickStateContext as? Activity)?.requestedOrientation = ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED
        setMotionSensorEnabled(sideMenuState.isMotionEnabled)
    }

    fun startWudroidTvMode(mode: String, display: Display) {
        runCatching { wudroidTvPresentation?.dismiss() }
        if (mode == "MOTION") {
            if (wudroidTvPreviousControllerType < 0) {
                wudroidTvPreviousControllerType = runCatching { NativeInput.getControllerType(0) }
                    .getOrDefault(NativeInput.EmulatedControllerType.WIIMOTE)
            }
            runCatching { NativeInput.setControllerType(0, NativeInput.EmulatedControllerType.WIIMOTE) }
            setMotionSensorEnabled(true)
            (wudroidQuickStateContext as? Activity)?.requestedOrientation = ActivityInfo.SCREEN_ORIENTATION_PORTRAIT
        } else {
            if (wudroidTvPreviousControllerType >= 0) {
                runCatching { NativeInput.setControllerType(0, wudroidTvPreviousControllerType) }
                wudroidTvPreviousControllerType = -1
            }
            (wudroidQuickStateContext as? Activity)?.requestedOrientation = ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED
            setMotionSensorEnabled(sideMenuState.isMotionEnabled)
        }

        wudroidTvMode = mode
        wudroidTvSelectedDisplayId = display.displayId
        wudroidTvActive = true
        showWudroidTvPickerDialog = false

        val presentation = WudroidTvPresentation(
            context = wudroidQuickStateContext,
            display = display,
            onSurfaceReady = { holder, width, height ->
                runCatching {
                    // Bind the renderer directly to the external display. The
                    // stock mainHolderCallback has a duplicate-surface guard,
                    // which is exactly what caused the black TV in Test1.
                    NativeEmulation.setSurfaceSize(width, height, true)
                    NativeEmulation.setSurface(holder.surface, true)
                    viewModel.setSurfaces.set(isMain = true, value = true)

                    // Recreate the Wii U GamePad renderer too when its phone
                    // surface is already present; this mirrors Cemu's stock
                    // main-surface callback behavior.
                    if (viewModel.setSurfaces.get(isMain = false)) {
                        NativeEmulation.initializeSurface(isMainCanvas = false)
                    }

                    viewModel.destroyedSurfaces.set(isMain = true, value = false)
                    NativeEmulation.resumeTitle()
                }.onFailure {
                    scope.launch {
                        snackbarHostState.showSnackbar("TV conectada, mas o vídeo não pôde ser anexado")
                    }
                }
            },
        )
        wudroidTvPresentation = presentation

        scope.launch {
            // IMPORTANT: removing the phone SurfaceView is asynchronous. If the
            // Presentation is shown too early, Cemu still thinks the old main
            // surface is active and ignores/loses the external surface. Wait for
            // the stock callback to report the phone surface as destroyed first.
            var waitSteps = 0
            while (viewModel.setSurfaces.get(isMain = true) && waitSteps < 60) {
                delay(40)
                waitSteps++
            }

            if (viewModel.setSurfaces.get(isMain = true)) {
                wudroidTvActive = false
                wudroidTvPresentation = null
                snackbarHostState.showSnackbar("A tela do celular ainda estava ocupando o vídeo. Tente conectar novamente.")
                return@launch
            }

            runCatching { presentation.show() }.onFailure {
                wudroidTvActive = false
                wudroidTvPresentation = null
                snackbarHostState.showSnackbar("Não foi possível abrir a TV selecionada")
                return@launch
            }

            // Give SurfaceView time to deliver surfaceChanged/onSurfaceReady.
            delay(700)
            if (wudroidTvActive && !viewModel.setSurfaces.get(isMain = true)) {
                snackbarHostState.showSnackbar("A TV abriu, mas o Cemu ainda não recebeu a superfície de vídeo")
            }
        }
    }
'''

if old not in s:
    raise SystemExit("TV RuntimeFix1: Test1 start/stop block not found")
s = s.replace(old, new, 1)

checks = [
    marker,
    "NativeEmulation.setSurface(holder.surface, true)",
    "while (viewModel.setSurfaces.get(isMain = true)",
    "NativeEmulation.initializeSurface(isMainCanvas = false)",
]
missing = [x for x in checks if x not in s]
if missing:
    raise SystemExit("TV RuntimeFix1 verification failed: " + ", ".join(missing))

screen_path.write_text(s)
print("Wudroid 0.1.2TV Test1 RuntimeFix1 applied")
print("- waits for the phone main SurfaceView to be fully released")
print("- binds the Cemu TV framebuffer directly to the external SurfaceView")
print("- keeps Cemu surface flags synchronized for reconnect/disconnect")
print("- reinitializes the GamePad surface when needed")
