package info.cemu.cemu

/**
 * Thin JNI bridge compiled into CemuAndroid.
 *
 * Test 2 keeps this tiny Cemu-side capability probe. The real LSFG engine is
 * provided by the embedded LSFG-Android library module and runs through the
 * Android capture/overlay path.
 */
object WudroidFrameGenerationNative {
    @JvmStatic
    external fun isBridgeCompiled(): Boolean

    @JvmStatic
    external fun hasAhardwareBufferSupport(): Boolean

    @JvmStatic
    external fun lsfgEngineVersion(): String
}
