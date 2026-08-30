package info.cemu.cemu.emulation

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
 * - W/A/S/D are translated to the emulated left analog stick.
 * - Mouse relative movement is translated to the emulated right analog stick.
 * - All other keyboard keys are intentionally NOT consumed here, so Cemu's
 *   normal InputHandler can map them to gamepad buttons in the input profile.
 *
 * This class does not use Accessibility, overlays from other apps, or root.
 * Input stays inside EmulationActivity.
 */
object WudroidKeyboardMouse {
    private const val MOUSE_SENSITIVITY = 0.035f
    private const val MOUSE_RELEASE_MS = 22L

    private val mainHandler = Handler(Looper.getMainLooper())
    private val heldMovementKeys = mutableSetOf<Int>()

    private var leftX = 0f
    private var leftY = 0f
    private var rightX = 0f
    private var rightY = 0f
    private var lastPointerX: Float? = null
    private var lastPointerY: Float? = null
    private var lastDeviceId = 0

    private val releaseMouseStick = Runnable {
        rightX = 0f
        rightY = 0f
        emitVirtualPad(lastDeviceId)
    }

    fun reset() {
        heldMovementKeys.clear()
        leftX = 0f
        leftY = 0f
        rightX = 0f
        rightY = 0f
        lastPointerX = null
        lastPointerY = null
        mainHandler.removeCallbacks(releaseMouseStick)
        emitVirtualPad(lastDeviceId)
    }

    fun onKeyEvent(event: KeyEvent): Boolean {
        if (!isKeyboard(event)) return false

        val movementKey = when (event.keyCode) {
            KeyEvent.KEYCODE_W,
            KeyEvent.KEYCODE_A,
            KeyEvent.KEYCODE_S,
            KeyEvent.KEYCODE_D -> true
            else -> false
        }
        if (!movementKey) return false

        lastDeviceId = event.deviceId
        when (event.action) {
            KeyEvent.ACTION_DOWN -> heldMovementKeys.add(event.keyCode)
            KeyEvent.ACTION_UP -> heldMovementKeys.remove(event.keyCode)
            else -> return true
        }

        updateLeftStick()
        emitVirtualPad(event.deviceId)
        return true
    }

    fun onMouseMotion(event: MotionEvent): Boolean {
        if (!isMouse(event)) return false
        if (event.actionMasked != MotionEvent.ACTION_MOVE &&
            event.actionMasked != MotionEvent.ACTION_HOVER_MOVE
        ) return false

        lastDeviceId = event.deviceId

        var dx = event.getAxisValue(MotionEvent.AXIS_RELATIVE_X)
        var dy = event.getAxisValue(MotionEvent.AXIS_RELATIVE_Y)

        // Some Android mouse drivers don't expose RELATIVE_X/Y until pointer
        // capture is active. Use pointer deltas as a safe fallback.
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

        rightX = (dx * MOUSE_SENSITIVITY).coerceIn(-1f, 1f)
        rightY = (dy * MOUSE_SENSITIVITY).coerceIn(-1f, 1f)
        emitVirtualPad(event.deviceId)

        mainHandler.removeCallbacks(releaseMouseStick)
        mainHandler.postDelayed(releaseMouseStick, MOUSE_RELEASE_MS)
        return true
    }

    private fun updateLeftStick() {
        val x = (if (KeyEvent.KEYCODE_D in heldMovementKeys) 1 else 0) -
            (if (KeyEvent.KEYCODE_A in heldMovementKeys) 1 else 0)
        val y = (if (KeyEvent.KEYCODE_S in heldMovementKeys) 1 else 0) -
            (if (KeyEvent.KEYCODE_W in heldMovementKeys) 1 else 0)

        // Normalize diagonals so W+D isn't faster than W alone.
        if (x != 0 && y != 0) {
            leftX = x * 0.70710677f
            leftY = y * 0.70710677f
        } else {
            leftX = x.toFloat()
            leftY = y.toFloat()
        }
    }

    private fun emitVirtualPad(deviceId: Int) {
        val now = SystemClock.uptimeMillis()
        val pointerProperties = arrayOf(
            MotionEvent.PointerProperties().apply {
                id = 0
                toolType = MotionEvent.TOOL_TYPE_UNKNOWN
            }
        )
        val pointerCoords = arrayOf(
            MotionEvent.PointerCoords().apply {
                x = leftX
                y = leftY
                pressure = 1f
                size = 1f
                setAxisValue(MotionEvent.AXIS_X, leftX)
                setAxisValue(MotionEvent.AXIS_Y, leftY)
                // Android gamepads normally expose the right stick as Z/RZ.
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

    private fun isKeyboard(event: KeyEvent): Boolean =
        event.device?.keyboardType == InputDevice.KEYBOARD_TYPE_ALPHABETIC ||
            (event.source and InputDevice.SOURCE_KEYBOARD) == InputDevice.SOURCE_KEYBOARD

    private fun isMouse(event: MotionEvent): Boolean =
        (event.source and InputDevice.SOURCE_MOUSE) == InputDevice.SOURCE_MOUSE ||
            (event.source and InputDevice.SOURCE_MOUSE_RELATIVE) == InputDevice.SOURCE_MOUSE_RELATIVE
}
