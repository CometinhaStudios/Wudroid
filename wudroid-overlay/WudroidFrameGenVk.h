#pragma once

#if BOOST_PLAT_ANDROID

#include <atomic>
#include <chrono>
#include <cstdlib>
#include <cstring>
#include <mutex>
#include <string>
#include <vector>
#include <vulkan/vulkan.h>

#include "Cafe/HW/Latte/Renderer/Vulkan/VulkanAPI.h"
#include "Cafe/HW/Latte/Renderer/Vulkan/WudroidFrameGenShaderSpv.h"

// Wudroid Native Frame Generation Test 1
// Runs inside Cemu's Vulkan renderer. It never captures the Android screen.

struct WudroidFrameGenPresent
{
    bool generated = false;
    uint32_t imageIndex = 0;
    VkSemaphore acquireSemaphore = VK_NULL_HANDLE;
    VkSemaphore presentSemaphore = VK_NULL_HANDLE;
};

namespace WudroidFrameGenInternal
{
struct ImageResource
{
    VkImage image = VK_NULL_HANDLE;
    VkDeviceMemory memory = VK_NULL_HANDLE;
    VkImageView view = VK_NULL_HANDLE;
    bool initialized = false;
};

struct PushConstants
{
    int32_t width;
    int32_t height;
    int32_t radius;
    float strength;
};

inline std::atomic<int> g_status{0}; // 0 off, 1 warming, 2 active, 3 unsupported, 4 error
inline std::atomic<int> g_realFps{0};
inline std::atomic<int> g_generatedFps{0};
inline std::atomic<int> g_outputFps{0};
inline std::atomic<bool> g_nvOpticalFlowAdvertised{false};
inline std::atomic<bool> g_modeChanged{false};
inline std::atomic<bool> g_lastEnabled{false};
inline std::string g_error;
inline std::mutex g_errorMutex;

inline bool envBool(const char* name, bool fallback = false)
{
    const char* v = std::getenv(name);
    if (!v) return fallback;
    return std::strcmp(v, "1") == 0 || std::strcmp(v, "true") == 0 || std::strcmp(v, "on") == 0;
}

inline int envInt(const char* name, int fallback)
{
    const char* v = std::getenv(name);
    if (!v) return fallback;
    char* end = nullptr;
    long out = std::strtol(v, &end, 10);
    if (end == v) return fallback;
    return static_cast<int>(out);
}

inline float envFloat(const char* name, float fallback)
{
    const char* v = std::getenv(name);
    if (!v) return fallback;
    char* end = nullptr;
    float out = std::strtof(v, &end);
    if (end == v) return fallback;
    return out;
}

inline bool enabled()
{
    bool now = envBool("WUDROID_FRAMEGEN_ENABLED", false);
    bool old = g_lastEnabled.exchange(now);
    if (now != old)
        g_modeChanged.store(true);
    return now;
}

inline void setError(const char* msg)
{
    {
        std::lock_guard<std::mutex> lock(g_errorMutex);
        g_error = msg ? msg : "unknown";
    }
    g_status.store(4);
}

class Engine
{
public:
    bool record(
        VkPhysicalDevice physicalDevice,
        VkDevice device,
        VkCommandBuffer cmd,
        VkSwapchainKHR swapchain,
        const std::vector<VkImage>& swapImages,
        const std::vector<VkSemaphore>& presentSemaphores,
        uint32_t realIndex,
        VkExtent2D extent,
        VkFormat swapFormat,
        WudroidFrameGenPresent& out)
    {
        tickReal();
        if (!enabled())
        {
            g_status.store(0);
            m_historyValid = false;
            return false;
        }

        if (!envBool("WUDROID_FRAMEGEN_SWAPCHAIN_TRANSFER_SRC", false))
        {
            g_status.store(3);
            return false;
        }

        if (!ensureResources(physicalDevice, device, extent, swapFormat))
        {
            g_status.store(4);
            return false;
        }

        const int next = m_historyValid ? (1 - m_currentHistory) : 0;
        recordCapture(cmd, swapImages[realIndex], m_history[next], extent);

        if (!m_historyValid)
        {
            m_historyValid = true;
            m_currentHistory = next;
            g_status.store(1);
            return false;
        }

        uint32_t synthIndex = 0;
        VkResult acquire = vkAcquireNextImageKHR(
            device, swapchain, 1'000'000'000ULL, m_synthAcquireSemaphore,
            VK_NULL_HANDLE, &synthIndex);
        if (acquire != VK_SUCCESS && acquire != VK_SUBOPTIMAL_KHR)
        {
            if (acquire != VK_ERROR_OUT_OF_DATE_KHR)
                setError("second swapchain image acquisition failed");
            return false;
        }
        if (synthIndex == realIndex || synthIndex >= swapImages.size())
        {
            setError("driver returned invalid second swapchain image");
            return false;
        }

        const int prev = m_currentHistory;
        const int curr = next;
        recordInterpolation(cmd, prev, curr, extent);
        recordOutputToSwapchain(cmd, swapImages[synthIndex], extent);

        m_currentHistory = curr;
        out.generated = true;
        out.imageIndex = synthIndex;
        out.acquireSemaphore = m_synthAcquireSemaphore;
        out.presentSemaphore = presentSemaphores[synthIndex];
        g_status.store(2);
        tickGenerated();
        return true;
    }

    void resetHistory() { m_historyValid = false; }

    void shutdown()
    {
        if (m_device == VK_NULL_HANDLE) return;
        vkDeviceWaitIdle(m_device);
        destroyResources();
        if (m_synthAcquireSemaphore)
            vkDestroySemaphore(m_device, m_synthAcquireSemaphore, nullptr);
        m_synthAcquireSemaphore = VK_NULL_HANDLE;
        m_device = VK_NULL_HANDLE;
        m_physicalDevice = VK_NULL_HANDLE;
    }

private:
    VkPhysicalDevice m_physicalDevice = VK_NULL_HANDLE;
    VkDevice m_device = VK_NULL_HANDLE;
    VkExtent2D m_extent{};
    VkFormat m_swapFormat = VK_FORMAT_UNDEFINED;
    ImageResource m_history[2];
    ImageResource m_output;
    VkDescriptorSetLayout m_descriptorSetLayout = VK_NULL_HANDLE;
    VkDescriptorPool m_descriptorPool = VK_NULL_HANDLE;
    VkDescriptorSet m_descriptorSets[2]{};
    VkPipelineLayout m_pipelineLayout = VK_NULL_HANDLE;
    VkPipeline m_pipeline = VK_NULL_HANDLE;
    VkSemaphore m_synthAcquireSemaphore = VK_NULL_HANDLE;
    bool m_historyValid = false;
    int m_currentHistory = 0;

    std::chrono::steady_clock::time_point m_fpsWindow = std::chrono::steady_clock::now();
    int m_realCounter = 0;
    int m_generatedCounter = 0;

    void tickReal()
    {
        ++m_realCounter;
        auto now = std::chrono::steady_clock::now();
        auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(now - m_fpsWindow).count();
        if (ms >= 1000)
        {
            int real = static_cast<int>(m_realCounter * 1000LL / ms);
            int gen = static_cast<int>(m_generatedCounter * 1000LL / ms);
            g_realFps.store(real);
            g_generatedFps.store(gen);
            g_outputFps.store(real + gen);
            m_realCounter = 0;
            m_generatedCounter = 0;
            m_fpsWindow = now;
        }
    }

    void tickGenerated() { ++m_generatedCounter; }

    uint32_t findMemoryType(uint32_t bits, VkMemoryPropertyFlags flags)
    {
        VkPhysicalDeviceMemoryProperties mem{};
        vkGetPhysicalDeviceMemoryProperties(m_physicalDevice, &mem);
        for (uint32_t i = 0; i < mem.memoryTypeCount; ++i)
            if ((bits & (1u << i)) && (mem.memoryTypes[i].propertyFlags & flags) == flags)
                return i;
        return UINT32_MAX;
    }

    bool createImage(ImageResource& out, VkFormat format, VkImageUsageFlags usage)
    {
        VkImageCreateInfo ci{};
        ci.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
        ci.imageType = VK_IMAGE_TYPE_2D;
        ci.format = format;
        ci.extent = { m_extent.width, m_extent.height, 1 };
        ci.mipLevels = 1;
        ci.arrayLayers = 1;
        ci.samples = VK_SAMPLE_COUNT_1_BIT;
        ci.tiling = VK_IMAGE_TILING_OPTIMAL;
        ci.usage = usage;
        ci.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
        ci.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
        if (vkCreateImage(m_device, &ci, nullptr, &out.image) != VK_SUCCESS)
            return false;

        VkMemoryRequirements req{};
        vkGetImageMemoryRequirements(m_device, out.image, &req);
        uint32_t mt = findMemoryType(req.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
        if (mt == UINT32_MAX) return false;

        VkMemoryAllocateInfo ai{};
        ai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        ai.allocationSize = req.size;
        ai.memoryTypeIndex = mt;
        if (vkAllocateMemory(m_device, &ai, nullptr, &out.memory) != VK_SUCCESS)
            return false;
        if (vkBindImageMemory(m_device, out.image, out.memory, 0) != VK_SUCCESS)
            return false;

        VkImageViewCreateInfo vi{};
        vi.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
        vi.image = out.image;
        vi.viewType = VK_IMAGE_VIEW_TYPE_2D;
        vi.format = format;
        vi.subresourceRange.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
        vi.subresourceRange.levelCount = 1;
        vi.subresourceRange.layerCount = 1;
        if (vkCreateImageView(m_device, &vi, nullptr, &out.view) != VK_SUCCESS)
            return false;
        return true;
    }

    void destroyImage(ImageResource& img)
    {
        if (img.view) vkDestroyImageView(m_device, img.view, nullptr);
        if (img.image) vkDestroyImage(m_device, img.image, nullptr);
        if (img.memory) vkFreeMemory(m_device, img.memory, nullptr);
        img = {};
    }

    void destroyResources()
    {
        if (m_pipeline) vkDestroyPipeline(m_device, m_pipeline, nullptr);
        if (m_pipelineLayout) vkDestroyPipelineLayout(m_device, m_pipelineLayout, nullptr);
        if (m_descriptorPool) vkDestroyDescriptorPool(m_device, m_descriptorPool, nullptr);
        if (m_descriptorSetLayout) vkDestroyDescriptorSetLayout(m_device, m_descriptorSetLayout, nullptr);
        m_pipeline = VK_NULL_HANDLE;
        m_pipelineLayout = VK_NULL_HANDLE;
        m_descriptorPool = VK_NULL_HANDLE;
        m_descriptorSetLayout = VK_NULL_HANDLE;
        destroyImage(m_history[0]);
        destroyImage(m_history[1]);
        destroyImage(m_output);
        m_historyValid = false;
    }

    bool ensureResources(VkPhysicalDevice physical, VkDevice device, VkExtent2D extent, VkFormat swapFormat)
    {
        if (m_device == device && m_extent.width == extent.width && m_extent.height == extent.height &&
            m_pipeline != VK_NULL_HANDLE)
            return true;

        if (m_device != VK_NULL_HANDLE)
        {
            vkDeviceWaitIdle(m_device);
            destroyResources();
            if (m_synthAcquireSemaphore)
                vkDestroySemaphore(m_device, m_synthAcquireSemaphore, nullptr);
            m_synthAcquireSemaphore = VK_NULL_HANDLE;
        }

        m_physicalDevice = physical;
        m_device = device;
        m_extent = extent;
        m_swapFormat = swapFormat;

        VkFormatProperties swapFmt{};
        vkGetPhysicalDeviceFormatProperties(physical, swapFormat, &swapFmt);
        const VkFormatFeatureFlags swapRequired = VK_FORMAT_FEATURE_BLIT_SRC_BIT | VK_FORMAT_FEATURE_BLIT_DST_BIT;
        if ((swapFmt.optimalTilingFeatures & swapRequired) != swapRequired)
        {
            setError("swapchain format cannot blit to/from FrameGen images");
            return false;
        }

        VkFormatProperties fmt{};
        vkGetPhysicalDeviceFormatProperties(physical, VK_FORMAT_R8G8B8A8_UNORM, &fmt);
        const VkFormatFeatureFlags required = VK_FORMAT_FEATURE_STORAGE_IMAGE_BIT |
            VK_FORMAT_FEATURE_TRANSFER_SRC_BIT | VK_FORMAT_FEATURE_TRANSFER_DST_BIT;
        if ((fmt.optimalTilingFeatures & required) != required)
        {
            setError("RGBA8 storage/transfer image unsupported");
            return false;
        }

        VkImageUsageFlags historyUsage = VK_IMAGE_USAGE_STORAGE_BIT |
            VK_IMAGE_USAGE_TRANSFER_DST_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT;
        if (!createImage(m_history[0], VK_FORMAT_R8G8B8A8_UNORM, historyUsage) ||
            !createImage(m_history[1], VK_FORMAT_R8G8B8A8_UNORM, historyUsage) ||
            !createImage(m_output, VK_FORMAT_R8G8B8A8_UNORM, historyUsage))
        {
            setError("failed to allocate FrameGen images");
            return false;
        }

        VkDescriptorSetLayoutBinding bindings[3]{};
        for (uint32_t i = 0; i < 3; ++i)
        {
            bindings[i].binding = i;
            bindings[i].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_IMAGE;
            bindings[i].descriptorCount = 1;
            bindings[i].stageFlags = VK_SHADER_STAGE_COMPUTE_BIT;
        }
        VkDescriptorSetLayoutCreateInfo dl{};
        dl.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO;
        dl.bindingCount = 3;
        dl.pBindings = bindings;
        if (vkCreateDescriptorSetLayout(m_device, &dl, nullptr, &m_descriptorSetLayout) != VK_SUCCESS)
        {
            setError("failed to create FrameGen descriptor layout");
            return false;
        }

        VkPushConstantRange push{};
        push.stageFlags = VK_SHADER_STAGE_COMPUTE_BIT;
        push.offset = 0;
        push.size = sizeof(PushConstants);
        VkPipelineLayoutCreateInfo pl{};
        pl.sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
        pl.setLayoutCount = 1;
        pl.pSetLayouts = &m_descriptorSetLayout;
        pl.pushConstantRangeCount = 1;
        pl.pPushConstantRanges = &push;
        if (vkCreatePipelineLayout(m_device, &pl, nullptr, &m_pipelineLayout) != VK_SUCCESS)
        {
            setError("failed to create FrameGen pipeline layout");
            return false;
        }

        VkShaderModuleCreateInfo sm{};
        sm.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
        sm.codeSize = kWudroidFrameGenCompSpvBytes;
        sm.pCode = kWudroidFrameGenCompSpv;
        VkShaderModule module = VK_NULL_HANDLE;
        if (vkCreateShaderModule(m_device, &sm, nullptr, &module) != VK_SUCCESS)
        {
            setError("failed to create FrameGen compute shader");
            return false;
        }
        VkComputePipelineCreateInfo cp{};
        cp.sType = VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO;
        cp.stage.sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
        cp.stage.stage = VK_SHADER_STAGE_COMPUTE_BIT;
        cp.stage.module = module;
        cp.stage.pName = "main";
        cp.layout = m_pipelineLayout;
        VkResult pipeResult = vkCreateComputePipelines(m_device, VK_NULL_HANDLE, 1, &cp, nullptr, &m_pipeline);
        vkDestroyShaderModule(m_device, module, nullptr);
        if (pipeResult != VK_SUCCESS)
        {
            setError("failed to create FrameGen compute pipeline");
            return false;
        }

        VkDescriptorPoolSize ps{};
        ps.type = VK_DESCRIPTOR_TYPE_STORAGE_IMAGE;
        ps.descriptorCount = 6;
        VkDescriptorPoolCreateInfo dp{};
        dp.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
        dp.maxSets = 2;
        dp.poolSizeCount = 1;
        dp.pPoolSizes = &ps;
        if (vkCreateDescriptorPool(m_device, &dp, nullptr, &m_descriptorPool) != VK_SUCCESS)
        {
            setError("failed to create FrameGen descriptor pool");
            return false;
        }

        VkDescriptorSetLayout layouts[2] = { m_descriptorSetLayout, m_descriptorSetLayout };
        VkDescriptorSetAllocateInfo da{};
        da.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
        da.descriptorPool = m_descriptorPool;
        da.descriptorSetCount = 2;
        da.pSetLayouts = layouts;
        if (vkAllocateDescriptorSets(m_device, &da, m_descriptorSets) != VK_SUCCESS)
        {
            setError("failed to allocate FrameGen descriptor sets");
            return false;
        }

        for (int set = 0; set < 2; ++set)
        {
            const int prev = set == 0 ? 0 : 1;
            const int curr = set == 0 ? 1 : 0;
            VkDescriptorImageInfo ii[3]{};
            ii[0].imageView = m_history[prev].view; ii[0].imageLayout = VK_IMAGE_LAYOUT_GENERAL;
            ii[1].imageView = m_history[curr].view; ii[1].imageLayout = VK_IMAGE_LAYOUT_GENERAL;
            ii[2].imageView = m_output.view; ii[2].imageLayout = VK_IMAGE_LAYOUT_GENERAL;
            VkWriteDescriptorSet writes[3]{};
            for (uint32_t i = 0; i < 3; ++i)
            {
                writes[i].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
                writes[i].dstSet = m_descriptorSets[set];
                writes[i].dstBinding = i;
                writes[i].descriptorCount = 1;
                writes[i].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_IMAGE;
                writes[i].pImageInfo = &ii[i];
            }
            vkUpdateDescriptorSets(m_device, 3, writes, 0, nullptr);
        }

        VkSemaphoreCreateInfo sci{};
        sci.sType = VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO;
        if (vkCreateSemaphore(m_device, &sci, nullptr, &m_synthAcquireSemaphore) != VK_SUCCESS)
        {
            setError("failed to create FrameGen acquire semaphore");
            return false;
        }

        detectNvOpticalFlow(physical);
        m_historyValid = false;
        return true;
    }

    void detectNvOpticalFlow(VkPhysicalDevice physical)
    {
        uint32_t count = 0;
        if (vkEnumerateDeviceExtensionProperties(physical, nullptr, &count, nullptr) != VK_SUCCESS)
            return;
        std::vector<VkExtensionProperties> exts(count);
        if (vkEnumerateDeviceExtensionProperties(physical, nullptr, &count, exts.data()) != VK_SUCCESS)
            return;
        for (const auto& e : exts)
            if (std::strcmp(e.extensionName, "VK_NV_optical_flow") == 0)
                g_nvOpticalFlowAdvertised.store(true);
    }

    void barrier(VkCommandBuffer cmd, VkImage image, VkImageLayout oldLayout, VkImageLayout newLayout,
                 VkAccessFlags srcAccess, VkAccessFlags dstAccess,
                 VkPipelineStageFlags srcStage = VK_PIPELINE_STAGE_ALL_COMMANDS_BIT,
                 VkPipelineStageFlags dstStage = VK_PIPELINE_STAGE_ALL_COMMANDS_BIT)
    {
        VkImageMemoryBarrier b{};
        b.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER;
        b.srcAccessMask = srcAccess;
        b.dstAccessMask = dstAccess;
        b.oldLayout = oldLayout;
        b.newLayout = newLayout;
        b.srcQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
        b.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED;
        b.image = image;
        b.subresourceRange.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
        b.subresourceRange.levelCount = 1;
        b.subresourceRange.layerCount = 1;
        vkCmdPipelineBarrier(cmd, srcStage, dstStage, 0, 0, nullptr, 0, nullptr, 1, &b);
    }

    void blit(VkCommandBuffer cmd, VkImage src, VkImageLayout srcLayout,
              VkImage dst, VkImageLayout dstLayout, VkExtent2D extent)
    {
        VkImageBlit region{};
        region.srcSubresource.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
        region.srcSubresource.layerCount = 1;
        region.srcOffsets[1] = { static_cast<int32_t>(extent.width), static_cast<int32_t>(extent.height), 1 };
        region.dstSubresource.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
        region.dstSubresource.layerCount = 1;
        region.dstOffsets[1] = { static_cast<int32_t>(extent.width), static_cast<int32_t>(extent.height), 1 };
        vkCmdBlitImage(cmd, src, srcLayout, dst, dstLayout, 1, &region, VK_FILTER_NEAREST);
    }

    void recordCapture(VkCommandBuffer cmd, VkImage realImage, ImageResource& dst, VkExtent2D extent)
    {
        barrier(cmd, realImage, VK_IMAGE_LAYOUT_PRESENT_SRC_KHR, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                VK_ACCESS_MEMORY_READ_BIT, VK_ACCESS_TRANSFER_READ_BIT);
        barrier(cmd, dst.image, dst.initialized ? VK_IMAGE_LAYOUT_GENERAL : VK_IMAGE_LAYOUT_UNDEFINED,
                VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                dst.initialized ? VK_ACCESS_SHADER_READ_BIT : 0, VK_ACCESS_TRANSFER_WRITE_BIT);
        blit(cmd, realImage, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
             dst.image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, extent);
        barrier(cmd, dst.image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, VK_IMAGE_LAYOUT_GENERAL,
                VK_ACCESS_TRANSFER_WRITE_BIT, VK_ACCESS_SHADER_READ_BIT);
        barrier(cmd, realImage, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, VK_IMAGE_LAYOUT_PRESENT_SRC_KHR,
                VK_ACCESS_TRANSFER_READ_BIT, VK_ACCESS_MEMORY_READ_BIT);
        dst.initialized = true;
    }

    void recordInterpolation(VkCommandBuffer cmd, int prev, int curr, VkExtent2D extent)
    {
        barrier(cmd, m_output.image,
                m_output.initialized ? VK_IMAGE_LAYOUT_GENERAL : VK_IMAGE_LAYOUT_UNDEFINED,
                VK_IMAGE_LAYOUT_GENERAL,
                m_output.initialized ? VK_ACCESS_TRANSFER_READ_BIT : 0,
                VK_ACCESS_SHADER_WRITE_BIT,
                VK_PIPELINE_STAGE_ALL_COMMANDS_BIT, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT);

        vkCmdBindPipeline(cmd, VK_PIPELINE_BIND_POINT_COMPUTE, m_pipeline);
        // set0 = history0 -> history1, set1 = history1 -> history0
        const int setIndex = (prev == 0 && curr == 1) ? 0 : 1;
        vkCmdBindDescriptorSets(cmd, VK_PIPELINE_BIND_POINT_COMPUTE, m_pipelineLayout,
                                0, 1, &m_descriptorSets[setIndex], 0, nullptr);
        int quality = envInt("WUDROID_FRAMEGEN_QUALITY", 1);
        int radius = quality <= 0 ? 1 : (quality == 1 ? 2 : 4);
        PushConstants pc{
            static_cast<int32_t>(extent.width),
            static_cast<int32_t>(extent.height),
            radius,
            envFloat("WUDROID_FRAMEGEN_STRENGTH", 0.92f)
        };
        vkCmdPushConstants(cmd, m_pipelineLayout, VK_SHADER_STAGE_COMPUTE_BIT, 0, sizeof(pc), &pc);
        vkCmdDispatch(cmd, (extent.width + 31) / 32, (extent.height + 31) / 32, 1);
        barrier(cmd, m_output.image, VK_IMAGE_LAYOUT_GENERAL, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                VK_ACCESS_SHADER_WRITE_BIT, VK_ACCESS_TRANSFER_READ_BIT,
                VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT);
        m_output.initialized = true;
    }

    void recordOutputToSwapchain(VkCommandBuffer cmd, VkImage synthSwap, VkExtent2D extent)
    {
        barrier(cmd, synthSwap, VK_IMAGE_LAYOUT_UNDEFINED, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                0, VK_ACCESS_TRANSFER_WRITE_BIT);
        blit(cmd, m_output.image, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
             synthSwap, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, extent);
        barrier(cmd, synthSwap, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, VK_IMAGE_LAYOUT_PRESENT_SRC_KHR,
                VK_ACCESS_TRANSFER_WRITE_BIT, VK_ACCESS_MEMORY_READ_BIT);
        barrier(cmd, m_output.image, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, VK_IMAGE_LAYOUT_GENERAL,
                VK_ACCESS_TRANSFER_READ_BIT, VK_ACCESS_SHADER_WRITE_BIT);
    }
};

inline Engine g_engine;
} // namespace WudroidFrameGenInternal

inline bool WudroidFrameGen_IsEnabled()
{
    return WudroidFrameGenInternal::enabled();
}

inline bool WudroidFrameGen_ConsumeModeChange()
{
    WudroidFrameGenInternal::enabled();
    return WudroidFrameGenInternal::g_modeChanged.exchange(false);
}

inline void WudroidFrameGen_ResetHistory()
{
    WudroidFrameGenInternal::g_engine.resetHistory();
}

inline WudroidFrameGenPresent WudroidFrameGen_Record(
    VkPhysicalDevice physicalDevice,
    VkDevice device,
    VkCommandBuffer cmd,
    VkSwapchainKHR swapchain,
    const std::vector<VkImage>& swapImages,
    const std::vector<VkSemaphore>& presentSemaphores,
    uint32_t realIndex,
    VkExtent2D extent,
    VkFormat swapFormat)
{
    WudroidFrameGenPresent out{};
    WudroidFrameGenInternal::g_engine.record(
        physicalDevice, device, cmd, swapchain, swapImages, presentSemaphores,
        realIndex, extent, swapFormat, out);
    return out;
}

extern "C" int WudroidFrameGen_GetStatusCode()
{
    return WudroidFrameGenInternal::g_status.load();
}
extern "C" int WudroidFrameGen_GetRealFps()
{
    return WudroidFrameGenInternal::g_realFps.load();
}
extern "C" int WudroidFrameGen_GetGeneratedFps()
{
    return WudroidFrameGenInternal::g_generatedFps.load();
}
extern "C" int WudroidFrameGen_GetOutputFps()
{
    return WudroidFrameGenInternal::g_outputFps.load();
}
extern "C" bool WudroidFrameGen_HasNvOpticalFlow()
{
    return WudroidFrameGenInternal::g_nvOpticalFlowAdvertised.load();
}
extern "C" const char* WudroidFrameGen_GetLastError()
{
    std::lock_guard<std::mutex> lock(WudroidFrameGenInternal::g_errorMutex);
    return WudroidFrameGenInternal::g_error.c_str();
}

#else
struct WudroidFrameGenPresent { bool generated = false; };
inline bool WudroidFrameGen_IsEnabled() { return false; }
inline bool WudroidFrameGen_ConsumeModeChange() { return false; }
inline void WudroidFrameGen_ResetHistory() {}
#endif
