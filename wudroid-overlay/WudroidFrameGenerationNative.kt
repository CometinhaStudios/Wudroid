package info.cemu.cemu

/** Direct JNI bridge into Cemu's Vulkan present path. */
object WudroidFrameGenerationNative {
    @JvmStatic external fun isBridgeCompiled(): Boolean
    @JvmStatic external fun setConfig(enabled: Boolean, multiplier: Int, flowScale: Float, preset: Int)
    @JvmStatic external fun isPresentHookActive(): Boolean
    @JvmStatic external fun isOpticalFlowAdvertised(): Boolean
    @JvmStatic external fun generatedFrameCount(): Long
    @JvmStatic external fun engineStatus(): String
}
