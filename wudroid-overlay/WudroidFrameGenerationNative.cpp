#include <jni.h>
#include <android/hardware_buffer.h>

namespace {

jstring MakeString(JNIEnv* env, const char* value) {
    return env->NewStringUTF(value);
}

} // namespace

extern "C" JNIEXPORT jboolean JNICALL
Java_info_cemu_cemu_WudroidFrameGenerationNative_isBridgeCompiled(
    JNIEnv*, jclass) {
    return JNI_TRUE;
}

extern "C" JNIEXPORT jboolean JNICALL
Java_info_cemu_cemu_WudroidFrameGenerationNative_hasAhardwareBufferSupport(
    JNIEnv*, jclass) {
    AHardwareBuffer_Desc desc{};
    desc.width = 64;
    desc.height = 64;
    desc.layers = 1;
    desc.format = AHARDWAREBUFFER_FORMAT_R8G8B8A8_UNORM;
    desc.usage = AHARDWAREBUFFER_USAGE_GPU_SAMPLED_IMAGE |
                 AHARDWAREBUFFER_USAGE_GPU_COLOR_OUTPUT;
    return AHardwareBuffer_isSupported(&desc) ? JNI_TRUE : JNI_FALSE;
}

extern "C" JNIEXPORT jstring JNICALL
Java_info_cemu_cemu_WudroidFrameGenerationNative_lsfgEngineVersion(
    JNIEnv* env, jclass) {
#ifdef WUDROID_LSFG_LINKED
    return MakeString(env, "lsfg-vk-android 1.x • framegen linked");
#else
    return MakeString(env, "Wudroid JNI bridge • LSFG não linkado");
#endif
}
