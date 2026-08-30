#include <jni.h>
#include <cstdint>

extern "C" {
void WudroidFrameGen_SetConfig(int enabled, int multiplier, float flowScale, int preset);
int WudroidFrameGen_IsPresentHookActive();
int WudroidFrameGen_IsOpticalFlowAdvertised();
uint64_t WudroidFrameGen_GetGeneratedFrameCount();
const char* WudroidFrameGen_GetStatus();
}

extern "C" JNIEXPORT jboolean JNICALL
Java_info_cemu_cemu_WudroidFrameGenerationNative_isBridgeCompiled(JNIEnv*, jclass) {
    return JNI_TRUE;
}

extern "C" JNIEXPORT void JNICALL
Java_info_cemu_cemu_WudroidFrameGenerationNative_setConfig(
    JNIEnv*, jclass, jboolean enabled, jint multiplier, jfloat flowScale, jint preset) {
    WudroidFrameGen_SetConfig(enabled ? 1 : 0, (int)multiplier, (float)flowScale, (int)preset);
}

extern "C" JNIEXPORT jboolean JNICALL
Java_info_cemu_cemu_WudroidFrameGenerationNative_isPresentHookActive(JNIEnv*, jclass) {
    return WudroidFrameGen_IsPresentHookActive() ? JNI_TRUE : JNI_FALSE;
}

extern "C" JNIEXPORT jboolean JNICALL
Java_info_cemu_cemu_WudroidFrameGenerationNative_isOpticalFlowAdvertised(JNIEnv*, jclass) {
    return WudroidFrameGen_IsOpticalFlowAdvertised() ? JNI_TRUE : JNI_FALSE;
}

extern "C" JNIEXPORT jlong JNICALL
Java_info_cemu_cemu_WudroidFrameGenerationNative_generatedFrameCount(JNIEnv*, jclass) {
    return (jlong)WudroidFrameGen_GetGeneratedFrameCount();
}

extern "C" JNIEXPORT jstring JNICALL
Java_info_cemu_cemu_WudroidFrameGenerationNative_engineStatus(JNIEnv* env, jclass) {
    const char* s = WudroidFrameGen_GetStatus();
    return env->NewStringUTF(s ? s : "Wudroid FrameGen Vulkan");
}
