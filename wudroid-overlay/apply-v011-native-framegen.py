#!/usr/bin/env python3
from pathlib import Path
import re, shutil

root = Path("cemu-engine")
vulkan = root / "src/Cafe/HW/Latte/Renderer/Vulkan"
android_app = root / "src/android/app"
java = android_app / "src/main/java/info/cemu/cemu"
overlay = Path("wudroid-overlay")

required = [
    overlay / "WudroidFrameGenVk.h",
    overlay / "WudroidFrameGenShaderSpv.h",
    overlay / "WudroidFrameGenNative.cpp",
    overlay / "WudroidNativeFrameGen.kt",
    overlay / "WudroidFrameGenOverlay.kt",
]
for f in required:
    if not f.exists():
        raise SystemExit(f"Missing generated/input file: {f}")

# Native shader/backend header lives next to VulkanRenderer so it can use Cemu's
# existing Vulkan proc table without adding an external library or capture layer.
shutil.copy2(overlay / "WudroidFrameGenVk.h", vulkan / "WudroidFrameGenVk.h")
shutil.copy2(overlay / "WudroidFrameGenShaderSpv.h", vulkan / "WudroidFrameGenShaderSpv.h")

# Android runtime UI + JNI bridge.
fg_java = java / "framegen"
fg_java.mkdir(parents=True, exist_ok=True)
shutil.copy2(overlay / "WudroidNativeFrameGen.kt", fg_java / "WudroidNativeFrameGen.kt")
shutil.copy2(overlay / "WudroidFrameGenOverlay.kt", fg_java / "WudroidFrameGenOverlay.kt")
shutil.copy2(overlay / "WudroidFrameGenNative.cpp", android_app / "src/main/cpp/WudroidFrameGenNative.cpp")

# 1) Vulkan proc table: native compute pipeline functions.
api = vulkan / "VulkanAPI.h"
s = api.read_text()
if "VKFUNC_DEVICE(vkCreateComputePipelines);" not in s:
    anchor = "VKFUNC_DEVICE(vkCreateGraphicsPipelines);"
    if anchor not in s: raise SystemExit("VulkanAPI graphics pipeline anchor missing")
    s = s.replace(anchor, anchor + "\nVKFUNC_DEVICE(vkCreateComputePipelines);", 1)
if "VKFUNC_DEVICE(vkCmdDispatch);" not in s:
    anchor = "VKFUNC_DEVICE(vkCmdDraw);"
    if anchor not in s: raise SystemExit("VulkanAPI draw anchor missing")
    s = s.replace(anchor, anchor + "\nVKFUNC_DEVICE(vkCmdDispatch);", 1)
api.write_text(s)

# 2) Swapchain must be readable by the in-process FrameGen. This is NOT Android
# screen capture. Only request TRANSFER_SRC when the surface advertises it.
swap = vulkan / "SwapchainInfoVk.cpp"
s = swap.read_text()
if "WUDROID_FRAMEGEN_SWAPCHAIN_TRANSFER_SRC" not in s:
    if "#include <cstdlib>" not in s:
        s = s.replace('#include "Cafe/HW/Latte/Renderer/Vulkan/VulkanRenderer.h"',
                      '#include "Cafe/HW/Latte/Renderer/Vulkan/VulkanRenderer.h"\n#include <cstdlib>', 1)
    old = "create_info.imageUsage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT;"
    new = r'''create_info.imageUsage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT;
	const bool wudroidTransferSrc = (details.capabilities.supportedUsageFlags & VK_IMAGE_USAGE_TRANSFER_SRC_BIT) != 0;
	if (wudroidTransferSrc)
		create_info.imageUsage |= VK_IMAGE_USAGE_TRANSFER_SRC_BIT;
#if BOOST_PLAT_ANDROID
	setenv("WUDROID_FRAMEGEN_SWAPCHAIN_TRANSFER_SRC", wudroidTransferSrc ? "1" : "0", 1);
#endif'''
    if old not in s: raise SystemExit("Swapchain imageUsage anchor missing")
    s = s.replace(old, new, 1)

    # When FG is already enabled at launch or after a mode-change recreation,
    # FIFO preserves synth -> real ordering. No fake 60-FPS patch is used.
    anchor = "VkPresentModeKHR SwapchainInfoVk::ChoosePresentMode(const std::vector<VkPresentModeKHR>& modes)\n{\n\tm_maxQueued = 0;"
    if anchor in s:
        s = s.replace(anchor, anchor + r'''
#if BOOST_PLAT_ANDROID
	const char* wfg = std::getenv("WUDROID_FRAMEGEN_ENABLED");
	if (wfg && std::strcmp(wfg, "1") == 0)
		return VK_PRESENT_MODE_FIFO_KHR;
#endif''', 1)
        if "#include <cstring>" not in s:
            s = s.replace("#include <cstdlib>", "#include <cstdlib>\n#include <cstring>", 1)
swap.write_text(s)

# 3) VulkanRenderer: add backend and allow one command submission to signal both
# the generated-frame present semaphore and the real-frame present semaphore.
h = vulkan / "VulkanRenderer.h"
hs = h.read_text()
old_decl = "void SubmitCommandBuffer(VkSemaphore signalSemaphore = VK_NULL_HANDLE, VkSemaphore waitSemaphore = VK_NULL_HANDLE);"
new_decl = "void SubmitCommandBuffer(VkSemaphore signalSemaphore = VK_NULL_HANDLE, VkSemaphore waitSemaphore = VK_NULL_HANDLE, VkSemaphore secondSignalSemaphore = VK_NULL_HANDLE);"
if old_decl in hs:
    hs = hs.replace(old_decl, new_decl, 1)
elif new_decl not in hs:
    raise SystemExit("SubmitCommandBuffer declaration anchor missing")
h.write_text(hs)

renderer = vulkan / "VulkanRenderer.cpp"
rs = renderer.read_text()
include = '#include "Cafe/HW/Latte/Renderer/Vulkan/WudroidFrameGenVk.h"'
if include not in rs:
    # Put after the renderer's own include if possible, otherwise at top.
    m = re.search(r'(#include "Cafe/HW/Latte/Renderer/Vulkan/VulkanRenderer\.h"\s*)', rs)
    if m:
        rs = rs[:m.end()] + "\n" + include + rs[m.end():]
    else:
        rs = include + "\n" + rs

old_sig = "void VulkanRenderer::SubmitCommandBuffer(VkSemaphore signalSemaphore, VkSemaphore waitSemaphore)"
new_sig = "void VulkanRenderer::SubmitCommandBuffer(VkSemaphore signalSemaphore, VkSemaphore waitSemaphore, VkSemaphore secondSignalSemaphore)"
if old_sig in rs:
    rs = rs.replace(old_sig, new_sig, 1)
elif new_sig not in rs:
    raise SystemExit("SubmitCommandBuffer definition anchor missing")

# Replace the original 2-semaphore signal block.
pattern = re.compile(r'''\t// signal current command buffer semaphore\n\tVkSemaphore signalSemArray\[2\];\n\tif \(signalSemaphore != VK_NULL_HANDLE\)\n\t\{.*?\n\t\}\n\telse\n\t\{.*?\n\t\}\n''', re.S)
if "VkSemaphore signalSemArray[3];" not in rs:
    replacement = '''\t// signal current command buffer semaphore + up to two Wudroid/present semaphores\n\tVkSemaphore signalSemArray[3];\n\tuint32_t signalCount = 0;\n\tsignalSemArray[signalCount++] = m_commandBufferSemaphores[m_commandBufferIndex];\n\tif (signalSemaphore != VK_NULL_HANDLE)\n\t\tsignalSemArray[signalCount++] = signalSemaphore;\n\tif (secondSignalSemaphore != VK_NULL_HANDLE)\n\t\tsignalSemArray[signalCount++] = secondSignalSemaphore;\n\tsubmitInfo.signalSemaphoreCount = signalCount;\n\tsubmitInfo.pSignalSemaphores = signalSemArray;\n'''
    rs, n = pattern.subn(replacement, rs, count=1)
    if n != 1: raise SystemExit("SubmitCommandBuffer signal block patch failed")

# Recreate swapchain when live FG on/off changes, so present mode can switch FIFO.
update_anchor = "bool stateChanged = chainInfo.m_shouldRecreate;"
if "WudroidFrameGen_ConsumeModeChange()" not in rs:
    if update_anchor not in rs: raise SystemExit("UpdateSwapchainProperties anchor missing")
    rs = rs.replace(update_anchor, update_anchor + r'''
#if BOOST_PLAT_ANDROID
	if (mainWindow && WudroidFrameGen_ConsumeModeChange())
	{
		stateChanged = true;
		WudroidFrameGen_ResetHistory();
	}
#endif''', 1)

# Record native interpolation before command submission.
submit_anchor = "VkSemaphore presentSemaphore = chainInfo.m_presentSemaphores[chainInfo.swapchainImageIndex];\n\tSubmitCommandBuffer(presentSemaphore); // submit all command and signal semaphore"
if "WudroidFrameGenPresent wudroidFgPresent" not in rs:
    if submit_anchor not in rs: raise SystemExit("SwapBuffer submit anchor missing")
    replacement = r'''VkSemaphore presentSemaphore = chainInfo.m_presentSemaphores[chainInfo.swapchainImageIndex];
#if BOOST_PLAT_ANDROID
	WudroidFrameGenPresent wudroidFgPresent{};
	if (mainWindow && WudroidFrameGen_IsEnabled())
	{
		draw_endRenderPass();
		wudroidFgPresent = WudroidFrameGen_Record(
			m_physicalDevice,
			m_logicalDevice,
			m_state.currentCommandBuffer,
			chainInfo.m_swapchain,
			chainInfo.m_swapchainImages,
			chainInfo.m_presentSemaphores,
			static_cast<uint32_t>(chainInfo.swapchainImageIndex),
			chainInfo.getExtent(),
			chainInfo.m_surfaceFormat.format);
	}
	if (wudroidFgPresent.generated)
		SubmitCommandBuffer(presentSemaphore, wudroidFgPresent.acquireSemaphore, wudroidFgPresent.presentSemaphore);
	else
		SubmitCommandBuffer(presentSemaphore);
#else
	SubmitCommandBuffer(presentSemaphore);
#endif // submit all command and signal semaphore'''
    rs = rs.replace(submit_anchor, replacement, 1)

# Present generated frame first, then the real frame on the same present queue.
present_anchor = "VkResult result = vkQueuePresentKHR(m_presentQueue, &presentInfo);"
if "wudroidSynthInfo" not in rs:
    if present_anchor not in rs: raise SystemExit("vkQueuePresentKHR anchor missing")
    replacement = r'''#if BOOST_PLAT_ANDROID
	if (wudroidFgPresent.generated)
	{
		VkPresentInfoKHR wudroidSynthInfo{};
		wudroidSynthInfo.sType = VK_STRUCTURE_TYPE_PRESENT_INFO_KHR;
		wudroidSynthInfo.swapchainCount = 1;
		wudroidSynthInfo.pSwapchains = &chainInfo.m_swapchain;
		wudroidSynthInfo.pImageIndices = &wudroidFgPresent.imageIndex;
		wudroidSynthInfo.waitSemaphoreCount = 1;
		wudroidSynthInfo.pWaitSemaphores = &wudroidFgPresent.presentSemaphore;
		VkResult synthResult = vkQueuePresentKHR(m_presentQueue, &wudroidSynthInfo);
		if (synthResult == VK_ERROR_OUT_OF_DATE_KHR || synthResult == VK_SUBOPTIMAL_KHR)
			chainInfo.m_shouldRecreate = true;
		else if (synthResult < 0 && synthResult != VK_ERROR_SURFACE_LOST_KHR)
			cemuLog_log(LogType::Force, "[Wudroid FrameGen] synthetic present failed: {}", synthResult);
	}
#endif
	VkResult result = vkQueuePresentKHR(m_presentQueue, &presentInfo);'''
    rs = rs.replace(present_anchor, replacement, 1)
renderer.write_text(rs)

# 4) JNI bridge in CemuAndroid.
cmake = android_app / "src/main/cpp/CMakeLists.txt"
cs = cmake.read_text()
if "WudroidFrameGenNative.cpp" not in cs:
    anchor = "NativeSettings.cpp"
    if anchor not in cs: raise SystemExit("Android CMake NativeSettings.cpp anchor missing")
    cs = cs.replace(anchor, anchor + "\n        WudroidFrameGenNative.cpp", 1)
cmake.write_text(cs)

# 5) EmulationActivity: apply saved values before native emulation starts, then
# attach a right-edge in-game panel during onResume. This does not use Android's
# SYSTEM_ALERT_WINDOW permission; it is a child view of the emulator Activity.
activity = java / "emulation/EmulationActivity.kt"
asrc = activity.read_text()
if "info.cemu.cemu.framegen.WudroidNativeFrameGen" not in asrc:
    pkg_end = asrc.find("\n", asrc.find("package "))
    imports = "\nimport info.cemu.cemu.framegen.WudroidNativeFrameGen\nimport info.cemu.cemu.framegen.WudroidFrameGenOverlay"
    # Add with the other imports, right after BuildConfig if available.
    anchor = "import info.cemu.cemu.BuildConfig"
    if anchor in asrc:
        asrc = asrc.replace(anchor, anchor + imports, 1)
    else:
        asrc = asrc[:pkg_end+1] + imports + "\n" + asrc[pkg_end+1:]

if "private var wudroidFrameGenOverlayAttached" not in asrc:
    anchor = "private var processInputEvents = true"
    if anchor not in asrc: raise SystemExit("EmulationActivity processInputEvents anchor missing")
    asrc = asrc.replace(anchor, anchor + "\n    private var wudroidFrameGenOverlayAttached = false", 1)

if "WudroidNativeFrameGen.applySaved(this)" not in asrc:
    anchor = "super.onCreate(savedInstanceState)"
    if anchor not in asrc: raise SystemExit("EmulationActivity onCreate anchor missing")
    asrc = asrc.replace(anchor, anchor + "\n\n        WudroidNativeFrameGen.applySaved(this)", 1)

if "WudroidFrameGenOverlay.attach(this)" not in asrc:
    # onResume happens after setContent and is robust across old/new Wudroid UI variants.
    anchor = "override fun onResume() {\n        super.onResume()"
    if anchor not in asrc:
        # tolerate CR/extra spaces via regex
        m = re.search(r'override fun onResume\(\)\s*\{\s*super\.onResume\(\)', asrc)
        if not m: raise SystemExit("EmulationActivity onResume anchor missing")
        inject_at = m.end()
        inject = '''\n        if (!wudroidFrameGenOverlayAttached) {\n            wudroidFrameGenOverlayAttached = true\n            window.decorView.post {\n                WudroidFrameGenOverlay.attach(this) { open -> processInputEvents = !open }\n            }\n        }'''
        asrc = asrc[:inject_at] + inject + asrc[inject_at:]
    else:
        asrc = asrc.replace(anchor, anchor + '''\n        if (!wudroidFrameGenOverlayAttached) {\n            wudroidFrameGenOverlayAttached = true\n            window.decorView.post {\n                WudroidFrameGenOverlay.attach(this) { open -> processInputEvents = !open }\n            }\n        }''', 1)
activity.write_text(asrc)

# Sanity checks.
checks = {
    api: ["vkCreateComputePipelines", "vkCmdDispatch"],
    swap: ["WUDROID_FRAMEGEN_SWAPCHAIN_TRANSFER_SRC", "VK_IMAGE_USAGE_TRANSFER_SRC_BIT"],
    renderer: ["WudroidFrameGen_Record", "wudroidSynthInfo", "signalSemArray[3]"],
    activity: ["WudroidFrameGenOverlay.attach", "WudroidNativeFrameGen.applySaved"],
    cmake: ["WudroidFrameGenNative.cpp"],
}
for path, needles in checks.items():
    text = path.read_text()
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"Patch verification failed: {needle} missing from {path}")

print("Wudroid 0.1.1 Native FrameGen Test1 applied")
print("Backend: in-renderer Wudroid Motion Compute v0.1; no LSFG/MediaProjection")
