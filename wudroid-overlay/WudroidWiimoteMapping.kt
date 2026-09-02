package info.cemu.cemu

/**
 * Canonical mapping IDs from Cemu WiimoteController::ButtonId.
 * Power is intentionally absent: Cemu does not expose it as an emulated game button.
 */
object WudroidWiimoteMapping {
    const val A = 1
    const val B = 2
    const val ONE = 3
    const val TWO = 4
    const val NUNCHUK_Z = 5
    const val NUNCHUK_C = 6
    const val PLUS = 7
    const val MINUS = 8
    const val UP = 9
    const val DOWN = 10
    const val LEFT = 11
    const val RIGHT = 12
    const val NUNCHUK_UP = 13
    const val NUNCHUK_DOWN = 14
    const val NUNCHUK_LEFT = 15
    const val NUNCHUK_RIGHT = 16
    const val HOME = 17
}
