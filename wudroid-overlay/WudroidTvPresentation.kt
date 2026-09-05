package info.cemu.cemu.emulation

import android.app.Presentation
import android.content.Context
import android.os.Bundle
import android.view.Display
import android.view.SurfaceHolder
import android.view.SurfaceView
import android.view.WindowManager

/**
 * WUDROID_TV_MODE_TEST1_RUNTIMEFIX1
 * Dedicated external-display surface.
 *
 * RuntimeFix1 intentionally does NOT reuse EmulationViewModel.mainHolderCallback:
 * that callback guards against a second main surface and can ignore the TV surface
 * if the phone SurfaceView has not finished destroying yet. The TV mode waits for
 * the phone surface to be released and then binds this surface explicitly.
 */
class WudroidTvPresentation(
    context: Context,
    display: Display,
    private val onSurfaceReady: (SurfaceHolder, Int, Int) -> Unit,
    private val onSurfaceLost: () -> Unit = {},
) : Presentation(context, display) {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window?.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)

        val surfaceView = SurfaceView(context).apply {
            setBackgroundColor(android.graphics.Color.BLACK)
            holder.addCallback(object : SurfaceHolder.Callback {
                override fun surfaceCreated(holder: SurfaceHolder) = Unit

                override fun surfaceChanged(
                    holder: SurfaceHolder,
                    format: Int,
                    width: Int,
                    height: Int,
                ) {
                    if (width > 0 && height > 0 && holder.surface.isValid) {
                        onSurfaceReady(holder, width, height)
                    }
                }

                override fun surfaceDestroyed(holder: SurfaceHolder) {
                    onSurfaceLost()
                }
            })
        }
        setContentView(surfaceView)
    }
}
