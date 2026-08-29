# Wudroid 0.1.1b — FrameGen Native Prep — Test 1

Incremental update over `Wudroid-0.1.1-FrameGen-Config-Test1`.

## Fixed
- Frame Generation dialog is vertically scrollable, so the bottom settings no longer disappear on smaller/tall-density screens.
- `Target frame rate` and `Frame multiplier` no longer fight each other. A fixed target disables manual multiplier editing, matching Eden's behavior.
- The dialog reports the real backend state instead of implying generated frames are already active.

## Native preparation added
- JNI bridge compiled into `CemuAndroid`.
- Real `lsfg-vk-android` framegen static library is pulled into the Android build from the public MIT `release` branch.
- AHardwareBuffer GPU support probe is exposed to the UI.
- Existing `Lossless.dll` import remains user-supplied only.

## Important
This build **does not yet claim end-to-end generated frames**. The LSFG engine can be linked into the APK, but Cemu still needs the renderer/present hook that passes two rendered frames into the LSFG chain and presents the generated images. That is the target for Wudroid 0.1.2.

## Files to add/replace
- `wudroid-overlay/WudroidFrameGeneration.kt`
- `wudroid-overlay/WudroidFrameGenerationUi.kt`
- `wudroid-overlay/WudroidFrameGenerationNative.kt`
- `wudroid-overlay/WudroidFrameGenerationNative.cpp`
- `wudroid-overlay/apply-v011b-framegen-native.py`
- `.github/workflows/build-wudroid.yml`
