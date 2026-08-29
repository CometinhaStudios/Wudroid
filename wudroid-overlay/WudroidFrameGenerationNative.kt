package info.cemu.cemu

/**
 * Thin JNI bridge compiled into CemuAndroid.
 *
 * Test 1b does not claim that the renderer is already presenting generated
 * frames. This bridge exists so the UI can report the real native state and
 * so the next renderer patch can call the linked LSFG engine without adding
 * another Java/Kotlin API layer.
 */
object WudroidFrameGenerationNative {
    @JvmStatic
    external fun isBridgeCompiled(): Boolean

    @JvmStatic
    external fun hasAhardwareBufferSupport(): Boolean

    @JvmStatic
    external fun lsfgEngineVersion(): String
}
