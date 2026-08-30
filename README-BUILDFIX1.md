# Wudroid 0.1.1 - LibraryFix + KeyboardMouse BuildFix1

Fixes the GitHub Actions failure:
`EmulationActivity onGenericMotionEvent anchor missing`

Cause: build-wudroid.yml copies wudroid-overlay/EmulationActivity.kt over the
fresh Cemu activity before apply-v011f-library-input.py runs. The previous
package did not ship a matching activity, so the regex was patching an older
repo overlay.

BuildFix1 ships a complete EmulationActivity based on the current android-port
layout, already containing:
- W/A/S/D -> left stick bridge
- mouse -> right stick bridge
- Android pointer capture and ESC release
- other keys forwarded to Cemu InputHandler
- Wudroid graceful NativeEmulation.stopEmulation() quit

The patcher remains as a verification/fallback layer and no longer depends on
the failed old anchor when the activity is already patched.
