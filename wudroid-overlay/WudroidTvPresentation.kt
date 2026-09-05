package info.cemu.cemu.emulation

import android.app.Presentation
import android.content.Context
import android.os.Bundle
import android.view.Display
import android.view.SurfaceHolder
import android.view.SurfaceView
import android.view.WindowManager

/**
 * WUDROID_TV_MODE_TEST1
 * Dedicated external-display surface. Cemu's TV framebuffer is attached here,
 * while the phone can keep only the touch controller / Wii U GamePad surface.
 */
class WudroidTvPresentation(
    context: Context,
    display: Display,
    private val mainHolderCallback: SurfaceHolder.Callback,
) : Presentation(context, display) {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window?.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        val surface = SurfaceView(context).apply {
            holder.addCallback(mainHolderCallback)
            setBackgroundColor(android.graphics.Color.BLACK)
        }
        setContentView(surface)
    }
}
