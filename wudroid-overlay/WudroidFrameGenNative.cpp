#include <jni.h>

extern "C" int WudroidFrameGen_GetStatusCode();
extern "C" int WudroidFrameGen_GetRealFps();
extern "C" int WudroidFrameGen_GetGeneratedFps();
extern "C" int WudroidFrameGen_GetOutputFps();
extern "C" bool WudroidFrameGen_HasNvOpticalFlow();
extern "C" const char* WudroidFrameGen_GetLastError();

extern "C" JNIEXPORT jint JNICALL
Java_info_cemu_cemu_framegen_WudroidNativeFrameGenBridge_nativeStatusCode(JNIEnv*, jobject)
{
    return WudroidFrameGen_GetStatusCode();
}

extern "C" JNIEXPORT jintArray JNICALL
Java_info_cemu_cemu_framegen_WudroidNativeFrameGenBridge_nativeFps(JNIEnv* env, jobject)
{
    jint values[3] = {
        WudroidFrameGen_GetRealFps(),
        WudroidFrameGen_GetGeneratedFps(),
        WudroidFrameGen_GetOutputFps(),
    };
    jintArray out = env->NewIntArray(3);
    if (out) env->SetIntArrayRegion(out, 0, 3, values);
    return out;
}

extern "C" JNIEXPORT jboolean JNICALL
Java_info_cemu_cemu_framegen_WudroidNativeFrameGenBridge_nativeHasNvOpticalFlow(JNIEnv*, jobject)
{
    return WudroidFrameGen_HasNvOpticalFlow() ? JNI_TRUE : JNI_FALSE;
}

extern "C" JNIEXPORT jstring JNICALL
Java_info_cemu_cemu_framegen_WudroidNativeFrameGenBridge_nativeLastError(JNIEnv* env, jobject)
{
    const char* text = WudroidFrameGen_GetLastError();
    return env->NewStringUTF(text ? text : "");
}
