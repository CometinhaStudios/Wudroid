from pathlib import Path

renderer = Path("cemu-engine/src/Cafe/HW/Latte/Renderer/Vulkan/VulkanRenderer.cpp")
s = renderer.read_text()

if '#include <cstdlib>' not in s:
    s = '#include <cstdlib>\n#include <cstring>\n' + s

helper = r'''
#if BOOST_PLAT_ANDROID
static bool WudroidVulkanXEnabled()
{
    const char* value = std::getenv("WUDROID_VULKAN_X");
    return value != nullptr && std::strcmp(value, "1") == 0;
}
#else
static bool WudroidVulkanXEnabled()
{
    return false;
}
#endif
'''.strip()

anchor = 'extern std::atomic_int g_compiling_pipelines;'
if 'static bool WudroidVulkanXEnabled()' not in s:
    if anchor not in s:
        raise SystemExit('Vulkan X helper anchor not found')
    s = s.replace(anchor, helper + '\n\n' + anchor, 1)

ctor_anchor = 'cemuLog_log(LogType::Force, "------- Init Vulkan graphics backend -------");'
ctor_patch = ctor_anchor + r'''
	if (WudroidVulkanXEnabled())
		cemuLog_log(LogType::Force, "[Wudroid Vulkan X] v0.1 experimental path active");'''
if '[Wudroid Vulkan X] v0.1 experimental path active' not in s:
    if ctor_anchor not in s:
        raise SystemExit('Vulkan X constructor anchor not found')
    s = s.replace(ctor_anchor, ctor_patch, 1)

device_anchor = 'vkGetPhysicalDeviceProperties2(m_physicalDevice, &properties);'
device_patch = device_anchor + r'''
	if (WudroidVulkanXEnabled())
	{
		cemuLog_log(LogType::Force,
			"[Wudroid Vulkan X] GPU: {} vendor={} device={} driver={}",
			properties.properties.deviceName,
			properties.properties.vendorID,
			properties.properties.deviceID,
			properties.properties.driverVersion);

		// Test 1 policy: keep pipeline compilation conservative on mobile.
		// This intentionally trades shader warm-up speed for less concurrent
		// pressure on Android Vulkan drivers while Vulkan X is experimental.
		m_featureControl.disableMultithreadedCompilation = true;
		cemuLog_log(LogType::Force,
			"[Wudroid Vulkan X] Pipeline Safe Scheduler v0.1 enabled");
	}'''
if 'Pipeline Safe Scheduler v0.1 enabled' not in s:
    if device_anchor not in s:
        raise SystemExit('Vulkan X device anchor not found')
    s = s.replace(device_anchor, device_patch, 1)

renderer.write_text(s)

check = renderer.read_text()
if '[Wudroid Vulkan X] v0.1 experimental path active' not in check:
    raise SystemExit('Vulkan X native constructor patch failed')
if 'Pipeline Safe Scheduler v0.1 enabled' not in check:
    raise SystemExit('Vulkan X scheduler patch failed')

print('Wudroid Vulkan X v0.1 native patch applied')
