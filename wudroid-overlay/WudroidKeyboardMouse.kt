package info.cemu.cemu.emulation

import android.content.Context
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import android.view.InputDevice
import android.view.KeyEvent
import android.view.MotionEvent
import info.cemu.cemu.emulation.input.InputHandler
import kotlin.math.abs

/**
 * Wudroid keyboard + mouse bridge.
 *
 * Keyboard buttons are NOT hard-coded here anymore. They are mapped through
 * Cemu's real controller mapping screen (A/B/X/Y, d-pad, left stick, etc.).
 * This bridge only converts relative mouse movement into the emulated right
 * analog stick while keeping everything inside EmulationActivity.
 */
object WudroidKeyboardMouse {
    private const val PREFS_NAME = "wudroid_keyboard_mouse"
    private const val KEY_ENABLED = "enabled"
    private const val KEY_MOUSE_RIGHT_STICK = "mouse_right_stick"
    private const val KEY_SENSITIVITY = "mouse_sensitivity"
    private const val KEY_INVERT_X = "invert_x"
    private const val KEY_INVERT_Y = "invert_y"
    private const val KEY_CAPTURE_POINTER = "capture_pointer"

    private const val DEFAULT_SENSITIVITY = 0.035f
    private const val MOUSE_RELEASE_MS = 22L

    private val mainHandler = Handler(Looper.getMainLooper())

    private var appContext: Context? = null
    private var rightX = 0f
    private var rightY = 0f
    private var lastPointerX: Float? = null
    private var lastPointerY: Float? = null
    private var lastDeviceId = 0

    private val releaseMouseStick = Runnable {
        rightX = 0f
        rightY = 0f
        emitVirtualRightStick(lastDeviceId)
    }

    fun init(context: Context) {
        appContext = context.applicationContext
    }

    fun reset() {
        rightX = 0f
        rightY = 0f
        lastPointerX = null
        lastPointerY = null
        mainHandler.removeCallbacks(releaseMouseStick)
        emitVirtualRightStick(lastDeviceId)
    }

    /**
     * Keyboard events deliberately fall through to Cemu's InputHandler.
     * The player maps them from Controls -> Player -> each individual input.
     */
    fun onKeyEvent(event: KeyEvent): Boolean {
        return false
    }

    fun shouldCapturePointer(): Boolean {
        val prefs = prefs() ?: return true
        return prefs.getBoolean(KEY_ENABLED, true) &&
            prefs.getBoolean(KEY_MOUSE_RIGHT_STICK, true) &&
            prefs.getBoolean(KEY_CAPTURE_POINTER, true)
    }

    fun onMouseMotion(event: MotionEvent): Boolean {
        if (!isMouse(event)) return false

        val prefs = prefs()
        if (prefs != null) {
            if (!prefs.getBoolean(KEY_ENABLED, true)) return false
            if (!prefs.getBoolean(KEY_MOUSE_RIGHT_STICK, true)) return false
        }

        if (event.actionMasked != MotionEvent.ACTION_MOVE &&
            event.actionMasked != MotionEvent.ACTION_HOVER_MOVE
        ) return false

        lastDeviceId = event.deviceId

        var dx = event.getAxisValue(MotionEvent.AXIS_RELATIVE_X)
        var dy = event.getAxisValue(MotionEvent.AXIS_RELATIVE_Y)

        // Android only exposes true relative axes on some devices after pointer
        // capture. Fall back to pointer delta when RELATIVE_X/Y are zero.
        if (abs(dx) < 0.0001f && abs(dy) < 0.0001f) {
            val oldX = lastPointerX
            val oldY = lastPointerY
            if (oldX != null && oldY != null) {
                dx = event.x - oldX
                dy = event.y - oldY
            }
            lastPointerX = event.x
            lastPointerY = event.y
        }

        if (abs(dx) < 0.0001f && abs(dy) < 0.0001f) return true

        val sensitivity = prefs?.getFloat(KEY_SENSITIVITY, DEFAULT_SENSITIVITY)
            ?: DEFAULT_SENSITIVITY
        val invertX = prefs?.getBoolean(KEY_INVERT_X, false) ?: false
        val invertY = prefs?.getBoolean(KEY_INVERT_Y, false) ?: false

        if (invertX) dx = -dx
        if (invertY) dy = -dy

        rightX = (dx * sensitivity).coerceIn(-1f, 1f)
        rightY = (dy * sensitivity).coerceIn(-1f, 1f)
        emitVirtualRightStick(event.deviceId)

        mainHandler.removeCallbacks(releaseMouseStick)
        mainHandler.postDelayed(releaseMouseStick, MOUSE_RELEASE_MS)
        return true
    }

    private fun emitVirtualRightStick(deviceId: Int) {
        val now = SystemClock.uptimeMillis()
        val pointerProperties = arrayOf(
            MotionEvent.PointerProperties().apply {
                id = 0
                toolType = MotionEvent.TOOL_TYPE_UNKNOWN
            }
        )
        val pointerCoords = arrayOf(
            MotionEvent.PointerCoords().apply {
                x = 0f
                y = 0f
                pressure = 1f
                size = 1f
                setAxisValue(MotionEvent.AXIS_X, 0f)
                setAxisValue(MotionEvent.AXIS_Y, 0f)
                // Android gamepads expose the right stick on Z/RZ.
                setAxisValue(MotionEvent.AXIS_Z, rightX)
                setAxisValue(MotionEvent.AXIS_RZ, rightY)
            }
        )

        val synthetic = MotionEvent.obtain(
            now,
            now,
            MotionEvent.ACTION_MOVE,
            1,
            pointerProperties,
            pointerCoords,
            0,
            0,
            1f,
            1f,
            deviceId,
            0,
            InputDevice.SOURCE_JOYSTICK or InputDevice.SOURCE_GAMEPAD,
            0,
        )
        try {
            InputHandler.onMotionEvent(synthetic)
        } finally {
            synthetic.recycle()
        }
    }

    private fun prefs() = appContext?.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    private fun isMouse(event: MotionEvent): Boolean =
        (event.source and InputDevice.SOURCE_MOUSE) == InputDevice.SOURCE_MOUSE ||
            (event.source and InputDevice.SOURCE_MOUSE_RELATIVE) == InputDevice.SOURCE_MOUSE_RELATIVE
}
