#!/usr/bin/env python3
from pathlib import Path

screen_path = Path(
    "cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationScreen.kt"
)
main_path = Path(
    "cemu-engine/src/android/app/src/main/java/info/cemu/cemu/MainActivity.kt"
)

if not screen_path.exists():
    raise SystemExit("EmulationScreen.kt missing")
if not main_path.exists():
    raise SystemExit("MainActivity.kt missing")

screen = screen_path.read_text()
main = main_path.read_text()

marker = "WUDROID_012_LOCAL_MULTIPLAYER_TEST8"

if marker not in screen:
    touch_anchor = '''                setOnTouchListener(CanvasOnTouchListener(isTV))

                holder.addCallback(holderCallback)
'''
    touch_new = '''                setOnTouchListener(CanvasOnTouchListener(isTV))

                val wudroidVideoSurface = this

                holder.addCallback(holderCallback)
'''

    if touch_anchor not in screen:
        raise SystemExit(
            "Test8 EmulationSurface touch anchor missing"
        )

    screen = screen.replace(
        touch_anchor,
        touch_new,
        1,
    )

    callback_anchor = '''                    override fun surfaceCreated(holder: SurfaceHolder) {}
                    override fun surfaceDestroyed(holder: SurfaceHolder) {}
'''

    callback_new = '''                    override fun surfaceCreated(holder: SurfaceHolder) {
                        if (isTV) {
                            info.cemu.cemu.WudroidLanVideoHost.attachSurfaceView(
                                wudroidVideoSurface
                            )
                        }
                    }

                    override fun surfaceDestroyed(holder: SurfaceHolder) {
                        if (isTV) {
                            info.cemu.cemu.WudroidLanVideoHost.detachSurfaceView(
                                wudroidVideoSurface
                            )
                        }
                    }
'''

    if callback_anchor not in screen:
        raise SystemExit(
            "Test8 EmulationSurface callback anchor missing"
        )

    screen = screen.replace(
        callback_anchor,
        callback_new,
        1,
    )

    screen += "\n// " + marker + "\n"

main = main.replace(
    "Wudroid 0.1.2 • multiplayer local Test7",
    "Wudroid 0.1.2 • multiplayer local Test8",
)
main = main.replace(
    "multiplayer local Test7",
    "multiplayer local Test8",
)

screen_path.write_text(screen)
main_path.write_text(main)

for required in (
    "WudroidLanVideoHost.attachSurfaceView",
    "WudroidLanVideoHost.detachSurfaceView",
    marker,
):
    if required not in screen:
        raise SystemExit(
            "Test8 verification failed: " + required
        )

print("Wudroid 0.1.2 Local Multiplayer Test8 applied")
print("- TV SurfaceView -> experimental LAN video")
print("- no MediaProjection")
