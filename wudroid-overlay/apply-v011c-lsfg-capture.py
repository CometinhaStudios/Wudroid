#!/usr/bin/env python3
from pathlib import Path
import re

cemu = Path("cemu-engine")
android_root = cemu / "src/android"
app = android_root / "app"
java = app / "src/main/java/info/cemu/cemu"
lsfg_root = Path("lsfg-android")
lsfg_app = lsfg_root / "LSFG-Android-Application/app"

if not lsfg_app.exists():
    raise SystemExit("LSFG-Android checkout missing: lsfg-android/LSFG-Android-Application/app")

# ---------------------------------------------------------------------------
# 1. Convert upstream LSFG Android app into an Android library module.
#    We keep its full Kotlin/native capture pipeline but remove its own app id,
#    launcher and signing/splits. It is then packaged inside Wudroid.
# ---------------------------------------------------------------------------
module_gradle = lsfg_app / "build.gradle.kts"
module_gradle.write_text(r'''plugins {
    alias(libs.plugins.android.library)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
}

android {
    namespace = "com.lsfg.android"
    compileSdk = 35
    ndkVersion = "27.0.12077973"

    defaultConfig {
        minSdk = 29
        externalNativeBuild {
            cmake {
                cppFlags += listOf(
                    "-std=c++20",
                    "-DNDEBUG",
                    "-fvisibility=hidden",
                    "-fvisibility-inlines-hidden",
                    "-ffunction-sections",
                    "-fdata-sections"
                )
                arguments += listOf(
                    "-DANDROID_STL=c++_shared",
                    "-DANDROID_PLATFORM=android-29",
                    "-DCMAKE_SHARED_LINKER_FLAGS=-Wl,--gc-sections,--icf=safe"
                )
                abiFilters("arm64-v8a")
            }
        }
    }

    externalNativeBuild {
        cmake {
            path = file("src/main/cpp/CMakeLists.txt")
            version = "3.22.1"
        }
    }

    buildFeatures {
        compose = true
        aidl = true
        buildConfig = true
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
        debug {
            isMinifyEnabled = false
        }
    }

    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
        jniLibs {
            useLegacyPackaging = true
        }
    }
}

dependencies {
    val composeBom = platform("androidx.compose:compose-bom:2024.09.03")
    implementation(composeBom)
    implementation("androidx.activity:activity-compose:1.9.2")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material:material-icons-extended")
    implementation("androidx.navigation:navigation-compose:2.8.1")
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.6")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.6")
    implementation("androidx.documentfile:documentfile:1.0.1")
    implementation("dev.rikka.shizuku:api:13.1.5")
    implementation("dev.rikka.shizuku:provider:13.1.5")
    implementation("com.github.topjohnwu.libsu:core:5.3.0")
    implementation("com.github.topjohnwu.libsu:service:5.3.0")
}
''')

# Library manifest: keep permissions/components required by the real capture
# backend, but never replace CemuApplication and never add a second launcher.
manifest = lsfg_app / "src/main/AndroidManifest.xml"
manifest.write_text(r'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:tools="http://schemas.android.com/tools">
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_MEDIA_PROJECTION" />
    <uses-permission android:name="android.permission.FOREGROUND_SERVICE_SPECIAL_USE" />
    <uses-permission android:name="android.permission.SYSTEM_ALERT_WINDOW" />
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
    <uses-permission android:name="moe.shizuku.manager.permission.API_V23" />
    <uses-feature
        android:name="android.hardware.vulkan.version"
        android:required="true"
        android:version="0x401000" />

    <queries>
        <intent>
            <action android:name="android.intent.action.MAIN" />
            <category android:name="android.intent.category.LAUNCHER" />
        </intent>
    </queries>

    <application tools:targetApi="35">
        <provider
            android:name="androidx.core.content.FileProvider"
            android:authorities="${applicationId}.lsfg.fileprovider"
            android:exported="false"
            android:grantUriPermissions="true">
            <meta-data
                android:name="android.support.FILE_PROVIDER_PATHS"
                android:resource="@xml/file_provider_paths" />
        </provider>
        <provider
            android:name="rikka.shizuku.ShizukuProvider"
            android:authorities="${applicationId}.lsfg.shizuku"
            android:enabled="true"
            android:exported="true"
            android:multiprocess="false"
            android:permission="android.permission.INTERACT_ACROSS_USERS_FULL" />
        <activity
            android:name="com.lsfg.android.ui.ProjectionRequestActivity"
            android:exported="false"
            android:excludeFromRecents="true"
            android:taskAffinity=""
            android:launchMode="singleInstance"
            android:theme="@android:style/Theme.Translucent.NoTitleBar" />
        <service
            android:name="com.lsfg.android.session.LsfgForegroundService"
            android:exported="false"
            android:foregroundServiceType="mediaProjection|specialUse">
            <property
                android:name="android.app.PROPERTY_SPECIAL_USE_FGS_SUBTYPE"
                android:value="wudroid_lsfg_capture_pacing" />
        </service>
        <service
            android:name="com.lsfg.android.session.RootCaptureService"
            android:exported="false"
            tools:ignore="Instantiatable" />
        <service
            android:name="com.lsfg.android.session.LsfgAccessibilityService"
            android:exported="true"
            android:label="@string/accessibility_service_label"
            android:permission="android.permission.BIND_ACCESSIBILITY_SERVICE">
            <intent-filter>
                <action android:name="android.accessibilityservice.AccessibilityService" />
            </intent-filter>
            <meta-data
                android:name="android.accessibilityservice"
                android:resource="@xml/accessibility_service_config" />
        </service>
    </application>
</manifest>
''')

# ---------------------------------------------------------------------------
# 2. Because the target app IS Wudroid itself, don't relaunch Wudroid's
#    launcher after MediaProjection starts. Keep the current EmulationActivity.
# ---------------------------------------------------------------------------
service = lsfg_app / "src/main/java/com/lsfg/android/session/LsfgForegroundService.kt"
s = service.read_text()
needle = "launchTarget(pkg)"
replacement = '''if (pkg != packageName) {
                        launchTarget(pkg)
                    } else {
                        LsfgLog.i(TAG, "Wudroid host target detected — keeping current EmulationActivity")
                    }'''
if replacement not in s:
    if needle not in s:
        raise SystemExit("Could not find LSFG launchTarget(pkg) call")
    s = s.replace(needle, replacement, 1)
service.write_text(s)

# ---------------------------------------------------------------------------
# 3. Register the external lsfgembed module in Cemu's Gradle build.
# ---------------------------------------------------------------------------
settings = android_root / "settings.gradle.kts"
if not settings.exists():
    raise SystemExit("Cemu settings.gradle.kts not found")
s = settings.read_text()
block = '''\ninclude(":lsfgembed")\nproject(":lsfgembed").projectDir = file("../../../lsfg-android/LSFG-Android-Application/app")\n'''
if 'include(":lsfgembed")' not in s:
    s += block
settings.write_text(s)

app_gradle = app / "build.gradle.kts"
s = app_gradle.read_text()
if 'implementation(project(":lsfgembed"))' not in s:
    s = s.replace("dependencies {", 'dependencies {\n    implementation(project(":lsfgembed"))', 1)
app_gradle.write_text(s)

# ---------------------------------------------------------------------------
# 4. Start the projection flow from the game activity, not from the launcher.
#    prepareBeforeLaunch() arms the request; onResume() handles overlay settings
#    first and then the MediaProjection consent prompt.
# ---------------------------------------------------------------------------
emu = java / "emulation/EmulationActivity.kt"
s = emu.read_text()
if "import info.cemu.cemu.WudroidLsfgCaptureController" not in s:
    package_end = s.find("\n", s.find("package "))
    s = s[:package_end+1] + "import info.cemu.cemu.WudroidLsfgCaptureController\n" + s[package_end+1:]

if "WudroidLsfgCaptureController.maybeStartForEmulation(this)" not in s:
    m = re.search(r"override\s+fun\s+onResume\s*\(\s*\)\s*\{", s)
    if not m:
        raise SystemExit("Could not locate EmulationActivity.onResume")
    pos = m.end()
    s = s[:pos] + "\n        WudroidLsfgCaptureController.maybeStartForEmulation(this)" + s[pos:]
emu.write_text(s)

# ---------------------------------------------------------------------------
# 5. Preserve upstream license in the produced APK/repository build assets.
# ---------------------------------------------------------------------------
license_src = lsfg_root / "LSFG-Android-Application/LICENSE"
license_dst = app / "src/main/assets/licenses/LSFG-Android-Application-LICENSE.txt"
license_dst.parent.mkdir(parents=True, exist_ok=True)
if license_src.exists():
    license_dst.write_text(license_src.read_text())

# Wudroid UI display version stays 0.1.1.
main = java / "MainActivity.kt"
if main.exists():
    x = main.read_text()
    x = x.replace("Wudroid 0.1.1b • frontend independente", "Wudroid 0.1.1 • frontend independente")
    x = x.replace('InfoRow("Wudroid", "0.1.1b")', 'InfoRow("Wudroid", "0.1.1")')
    x = x.replace('Text("0.1.1b", color = WBlue', 'Text("0.1.1", color = WBlue')
    main.write_text(x)

print("Wudroid 0.1.1 LSFG Android capture backend embedded")
