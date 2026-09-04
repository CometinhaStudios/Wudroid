package info.cemu.cemu

import info.cemu.cemu.nativeinterface.NativeInput

/**
 * Wudroid aliases the Wiimote IDs exported by the Cemu Android bridge itself.
 * This avoids drifting from NativeInput.WiimoteButton.
 */
object WudroidWiimoteMapping {
    const val A = NativeInput.WiimoteButton.A
    const val B = NativeInput.WiimoteButton.B
    const val ONE = NativeInput.WiimoteButton.ONE
    const val TWO = NativeInput.WiimoteButton.TWO
    const val NUNCHUK_Z = NativeInput.WiimoteButton.NUNCHUCK_Z
    const val NUNCHUK_C = NativeInput.WiimoteButton.NUNCHUCK_C
    const val PLUS = NativeInput.WiimoteButton.PLUS
    const val MINUS = NativeInput.WiimoteButton.MINUS
    const val UP = NativeInput.WiimoteButton.UP
    const val DOWN = NativeInput.WiimoteButton.DOWN
    const val LEFT = NativeInput.WiimoteButton.LEFT
    const val RIGHT = NativeInput.WiimoteButton.RIGHT
    const val NUNCHUK_UP = NativeInput.WiimoteButton.NUNCHUCK_UP
    const val NUNCHUK_DOWN = NativeInput.WiimoteButton.NUNCHUCK_DOWN
    const val NUNCHUK_LEFT = NativeInput.WiimoteButton.NUNCHUCK_LEFT
    const val NUNCHUK_RIGHT = NativeInput.WiimoteButton.NUNCHUCK_RIGHT
    const val HOME = NativeInput.WiimoteButton.HOME
}
