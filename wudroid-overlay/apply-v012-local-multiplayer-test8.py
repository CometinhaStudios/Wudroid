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

marker = "WUDROID_012_LOCAL_MULTIPLAYER_TEST8_BUILDFIX1"

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
            "Test8 BuildFix1 EmulationSurface touch anchor missing"
        )

    screen = screen.replace(
        touch_anchor,
        touch_new,
        1,
    )

    # Do not rewrite Cemu's existing callback. Several older Wudroid
    # patches may legitimately change its body. Add an independent
    # SurfaceHolder.Callback used only by LAN video.
    callback_anchor = '''                holder.addCallback(holderCallback)
'''

    callback_new = '''                holder.addCallback(holderCallback)

                holder.addCallback(object : SurfaceHolder.Callback {
                    override fun surfaceChanged(
                        holder: SurfaceHolder,
                        format: Int,
                        width: Int,
                        height: Int
                    ) {
                        if (isTV && width > 1 && height > 1) {
                            info.cemu.cemu.WudroidLanVideoHost.attachSurfaceView(
                                wudroidVideoSurface
                            )
                        }
                    }

                    override fun surfaceCreated(holder: SurfaceHolder) {
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
                })
'''

    surface_pos = screen.find("val wudroidVideoSurface = this")
    callback_pos = screen.find(callback_anchor, surface_pos)

    if callback_pos < 0:
        raise SystemExit(
            "Test8 BuildFix1 holder callback anchor missing"
        )

    screen = (
        screen[:callback_pos]
        + screen[callback_pos:].replace(
            callback_anchor,
            callback_new,
            1,
        )
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
    "val wudroidVideoSurface = this",
    "WudroidLanVideoHost.attachSurfaceView",
    "WudroidLanVideoHost.detachSurfaceView",
    marker,
):
    if required not in screen:
        raise SystemExit(
            "Test8 BuildFix1 verification failed: " + required
        )

print("Wudroid 0.1.2 Local Multiplayer Test8 BuildFix1 applied")
print("- independent SurfaceHolder callback for LAN video")
print("- original Cemu Surface callback preserved")
print("- no MediaProjection")
