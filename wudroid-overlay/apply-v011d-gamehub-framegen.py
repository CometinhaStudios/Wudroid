#!/usr/bin/env python3
from pathlib import Path

vulkan_dir = Path("cemu-engine/src/Cafe/HW/Latte/Renderer/Vulkan")
renderer = vulkan_dir / "VulkanRenderer.cpp"
swapchain = vulkan_dir / "SwapchainInfoVk.cpp"

s = renderer.read_text()
include_anchor = '#include "Cafe/HW/Latte/Renderer/Vulkan/VulkanAPI.h"\n'
include_line = '#include "Cafe/HW/Latte/Renderer/Vulkan/WudroidFrameGenVk.h"\n'
if include_line not in s:
    if include_anchor not in s:
        raise SystemExit("VulkanRenderer.cpp include anchor not found")
    s = s.replace(include_anchor, include_anchor + include_line, 1)

# Record whether the Android Vulkan driver advertises VK_NV_optical_flow.
detect_anchor = 'CheckDeviceExtensionSupport(m_physicalDevice, m_featureControl); // todo - merge this with GetDeviceFeatures and separate from IsDeviceSuitable?\n'
if 'WudroidFrameGen_DetectOpticalFlow(m_physicalDevice);' not in s:
    if detect_anchor not in s:
        raise SystemExit("Vulkan physical-device detection anchor not found")
    s = s.replace(
        detect_anchor,
        detect_anchor + '#if BOOST_PLAT_ANDROID\n\tWudroidFrameGen_DetectOpticalFlow(m_physicalDevice);\n#endif\n',
        1,
    )

# Insert a direct swapchain path before the stock present path.  It consumes the
# render-done semaphore by copying the real frame into Wudroid-owned history,
# presents one or more synthetic frames, then restores/presents the real frame.
branch_anchor = '\tchainInfo.WaitAvailableFence();\n\n\tVkPresentIdKHR presentId = {};\n'
if 'WUDROID_FRAMEGEN_VULKAN_TEST9' not in s:
    if branch_anchor not in s:
        raise SystemExit("SwapBuffer present anchor not found")
    branch = r'''	chainInfo.WaitAvailableFence();

#if BOOST_PLAT_ANDROID
	// WUDROID_FRAMEGEN_VULKAN_TEST9
	if (mainWindow && WudroidFrameGen_IsEnabledForPresent())
	{
		auto extent = chainInfo.getExtent();
		const VkFormat surfaceFormat = chainInfo.m_surfaceFormat.format;
		const uint32_t firstIndex = chainInfo.swapchainImageIndex;
		VkImage firstImage = chainInfo.m_swapchainImages[firstIndex];

		if (WudroidFrameGenVk::g_engine.BeginRealFrame(
			m_physicalDevice,
			m_logicalDevice,
			m_graphicsQueue,
			(uint32_t)m_indices.graphicsFamily,
			surfaceFormat,
			extent,
			firstImage,
			presentSemaphore))
		{
			auto presentNoWait = [&](uint32_t imageIndex) -> VkResult
			{
				VkPresentInfoKHR fgPresent{};
				fgPresent.sType = VK_STRUCTURE_TYPE_PRESENT_INFO_KHR;
				fgPresent.swapchainCount = 1;
				fgPresent.pSwapchains = &chainInfo.m_swapchain;
				fgPresent.pImageIndices = &imageIndex;
				fgPresent.waitSemaphoreCount = 0;
				fgPresent.pWaitSemaphores = nullptr;
				return vkQueuePresentKHR(m_presentQueue, &fgPresent);
			};

			VkResult fgResult = VK_SUCCESS;
			uint32_t presentedCount = 0;

			if (!WudroidFrameGenVk::g_engine.HasPrevious())
			{
				// First real frame only seeds history. No synthetic frame yet.
				fgResult = presentNoWait(firstIndex);
				presentedCount = (fgResult >= 0) ? 1u : 0u;
				WudroidFrameGenVk::g_engine.CommitRealAsPrevious();
			}
			else
			{
				const int multiplier = WudroidFrameGen_GetMultiplier();
				uint32_t targetIndex = firstIndex;
				VkSemaphore targetAcquireSemaphore = VK_NULL_HANDLE;

				for (int generated = 1; generated < multiplier && fgResult >= 0; ++generated)
				{
					const float t = (float)generated / (float)multiplier;
					VkImage targetImage = chainInfo.m_swapchainImages[targetIndex];
					if (!WudroidFrameGenVk::g_engine.WriteGenerated(
						targetImage,
						surfaceFormat,
						extent,
						t,
						targetAcquireSemaphore))
					{
						fgResult = VK_ERROR_INITIALIZATION_FAILED;
						break;
					}

					fgResult = presentNoWait(targetIndex);
					if (fgResult < 0)
						break;
					presentedCount++;

					// Reserve a fresh swapchain image through Cemu's own SwapchainInfo
					// so its acquire fences/semaphores remain coherent.
					chainInfo.hasDefinedSwapchainImage = false;
					chainInfo.swapchainImageIndex = -1;
					if (!chainInfo.AcquireImage())
					{
						fgResult = VK_ERROR_OUT_OF_DATE_KHR;
						break;
					}
					chainInfo.WaitAvailableFence();
					targetIndex = chainInfo.swapchainImageIndex;
					targetAcquireSemaphore = chainInfo.ConsumeAcquireSemaphore();
				}

				if (fgResult >= 0)
				{
					VkImage targetImage = chainInfo.m_swapchainImages[targetIndex];
					if (!WudroidFrameGenVk::g_engine.WriteReal(
						targetImage,
						surfaceFormat,
						extent,
						targetAcquireSemaphore))
					{
						fgResult = VK_ERROR_INITIALIZATION_FAILED;
					}
					else
					{
						fgResult = presentNoWait(targetIndex);
						if (fgResult >= 0)
							presentedCount++;
					}
				}

				WudroidFrameGenVk::g_engine.CommitRealAsPrevious();
			}

			// present_wait/present_id markers are intentionally bypassed while
			// Wudroid owns the extra presents. FIFO remains the pacing mechanism.
			chainInfo.m_queueDepth = 0;
			chainInfo.m_presentId += presentedCount;

			if (fgResult < 0 && fgResult != VK_ERROR_OUT_OF_DATE_KHR &&
				fgResult != VK_ERROR_SURFACE_LOST_KHR)
			{
				throw std::runtime_error(fmt::format("Wudroid FrameGen present failed: {}", fgResult));
			}
			if (fgResult == VK_ERROR_OUT_OF_DATE_KHR)
				chainInfo.m_shouldRecreate = true;
			if (fgResult == VK_ERROR_SURFACE_LOST_KHR)
				chainInfo.surfaceWasLost = true;

			chainInfo.hasDefinedSwapchainImage = false;
			chainInfo.swapchainImageIndex = -1;
			return;
		}
		// If the framegen pipeline could not initialize, fall through to Cemu's
		// stock present path. BeginRealFrame fails before consuming the semaphore
		// for unsupported-format/setup errors.
	}
#endif

	VkPresentIdKHR presentId = {};
'''
    s = s.replace(branch_anchor, branch, 1)

renderer.write_text(s)

ss = swapchain.read_text()
old_usage = 'VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT'
new_usage = 'VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT'
if new_usage not in ss:
    if old_usage not in ss:
        raise SystemExit("Swapchain imageUsage anchor not found")
    ss = ss.replace(old_usage, new_usage, 1)
swapchain.write_text(ss)

print("Wudroid 0.1.1 direct Vulkan FrameGen Test9 renderer hook applied")
