#pragma once

#include "Cafe/HW/Latte/Renderer/Vulkan/VulkanAPI.h"
#include "Cafe/HW/Latte/Renderer/Vulkan/WudroidFrameGenBlendSpv.h"

#include <algorithm>
#include <atomic>
#include <cstdint>
#include <cstring>
#include <mutex>
#include <vector>

namespace WudroidFrameGenVk {

struct Config {
    std::atomic<int> enabled{0};
    std::atomic<int> multiplier{2};
    std::atomic<float> flowScale{0.50f};
    std::atomic<int> preset{2};
    std::atomic<int> presentHookActive{0};
    std::atomic<int> opticalFlowAdvertised{0};
    std::atomic<uint64_t> generatedFrames{0};
    std::atomic<int> status{0}; // 0 idle, 1 ready, 2 failed
};

static Config g_cfg;

static inline void BarrierImage(
    VkCommandBuffer cmd,
    VkImage image,
    VkImageLayout oldLayout,
    VkImageLayout newLayout,
    VkAccessFlags srcAccess,
    VkAccessFlags dstAccess,
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
    b.subresourceRange.baseMipLevel = 0;
    b.subresourceRange.levelCount = 1;
    b.subresourceRange.baseArrayLayer = 0;
    b.subresourceRange.layerCount = 1;
    vkCmdPipelineBarrier(cmd, srcStage, dstStage, 0, 0, nullptr, 0, nullptr, 1, &b);
}

class Engine {
public:
    bool BeginRealFrame(
        VkPhysicalDevice physical,
        VkDevice device,
        VkQueue graphicsQueue,
        uint32_t graphicsFamily,
        VkFormat swapFormat,
        VkExtent2D extent,
        VkImage swapImage,
        VkSemaphore renderDone)
    {
        std::lock_guard<std::mutex> lk(m_lock);
        g_cfg.presentHookActive.store(1);
        if (!Ensure(physical, device, graphicsQueue, graphicsFamily, extent))
            return false;

        return Submit([&](VkCommandBuffer cmd) {
            BarrierImage(cmd, swapImage, VK_IMAGE_LAYOUT_PRESENT_SRC_KHR,
                         VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                         VK_ACCESS_MEMORY_READ_BIT, VK_ACCESS_TRANSFER_READ_BIT);
            TransitionInternal(cmd, m_curr, m_currLayout,
                               VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                               VK_ACCESS_TRANSFER_WRITE_BIT);
            Blit(cmd, swapImage, swapFormat, m_curr.image, kInternalFormat, extent);
            BarrierImage(cmd, m_curr.image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                         VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
                         VK_ACCESS_TRANSFER_WRITE_BIT, VK_ACCESS_SHADER_READ_BIT,
                         VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT);
            m_currLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL;
            BarrierImage(cmd, swapImage, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                         VK_IMAGE_LAYOUT_PRESENT_SRC_KHR,
                         VK_ACCESS_TRANSFER_READ_BIT, VK_ACCESS_MEMORY_READ_BIT);
        }, renderDone);
    }

    bool HasPrevious() const { return m_havePrev; }

    bool WriteGenerated(
        VkImage target,
        VkFormat targetFormat,
        VkExtent2D extent,
        float t,
        VkSemaphore acquireSemaphore)
    {
        std::lock_guard<std::mutex> lk(m_lock);
        if (!m_ready || !m_havePrev)
            return false;

        t = std::clamp(t, 0.0f, 1.0f);
        bool ok = Submit([&](VkCommandBuffer cmd) {
            TransitionInternal(cmd, m_generated, m_generatedLayout,
                               VK_IMAGE_LAYOUT_GENERAL,
                               VK_ACCESS_SHADER_WRITE_BIT);

            vkCmdBindPipeline(cmd, VK_PIPELINE_BIND_POINT_COMPUTE, m_pipeline);
            vkCmdBindDescriptorSets(cmd, VK_PIPELINE_BIND_POINT_COMPUTE,
                                    m_pipelineLayout, 0, 1, &m_descriptorSet,
                                    0, nullptr);
            vkCmdPushConstants(cmd, m_pipelineLayout, VK_SHADER_STAGE_COMPUTE_BIT,
                               0, sizeof(float), &t);
            vkCmdDispatch(cmd, (extent.width + 7) / 8, (extent.height + 7) / 8, 1);

            BarrierImage(cmd, m_generated.image, VK_IMAGE_LAYOUT_GENERAL,
                         VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                         VK_ACCESS_SHADER_WRITE_BIT, VK_ACCESS_TRANSFER_READ_BIT,
                         VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT);
            m_generatedLayout = VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL;

            BarrierImage(cmd, target, VK_IMAGE_LAYOUT_PRESENT_SRC_KHR,
                         VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                         VK_ACCESS_MEMORY_READ_BIT, VK_ACCESS_TRANSFER_WRITE_BIT);
            Blit(cmd, m_generated.image, kInternalFormat, target, targetFormat, extent);
            BarrierImage(cmd, target, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                         VK_IMAGE_LAYOUT_PRESENT_SRC_KHR,
                         VK_ACCESS_TRANSFER_WRITE_BIT, VK_ACCESS_MEMORY_READ_BIT);

            BarrierImage(cmd, m_generated.image, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                         VK_IMAGE_LAYOUT_GENERAL,
                         VK_ACCESS_TRANSFER_READ_BIT, VK_ACCESS_SHADER_WRITE_BIT,
                         VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT);
            m_generatedLayout = VK_IMAGE_LAYOUT_GENERAL;
        }, acquireSemaphore);

        if (ok)
            g_cfg.generatedFrames.fetch_add(1);
        return ok;
    }

    bool WriteReal(
        VkImage target,
        VkFormat targetFormat,
        VkExtent2D extent,
        VkSemaphore acquireSemaphore)
    {
        std::lock_guard<std::mutex> lk(m_lock);
        if (!m_ready)
            return false;
        return Submit([&](VkCommandBuffer cmd) {
            BarrierImage(cmd, m_curr.image, m_currLayout,
                         VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                         VK_ACCESS_SHADER_READ_BIT, VK_ACCESS_TRANSFER_READ_BIT,
                         VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT);
            m_currLayout = VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL;
            BarrierImage(cmd, target, VK_IMAGE_LAYOUT_PRESENT_SRC_KHR,
                         VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                         VK_ACCESS_MEMORY_READ_BIT, VK_ACCESS_TRANSFER_WRITE_BIT);
            Blit(cmd, m_curr.image, kInternalFormat, target, targetFormat, extent);
            BarrierImage(cmd, target, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                         VK_IMAGE_LAYOUT_PRESENT_SRC_KHR,
                         VK_ACCESS_TRANSFER_WRITE_BIT, VK_ACCESS_MEMORY_READ_BIT);
            BarrierImage(cmd, m_curr.image, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                         VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
                         VK_ACCESS_TRANSFER_READ_BIT, VK_ACCESS_SHADER_READ_BIT,
                         VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT);
            m_currLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL;
        }, acquireSemaphore);
    }

    bool CommitRealAsPrevious()
    {
        std::lock_guard<std::mutex> lk(m_lock);
        if (!m_ready)
            return false;
        bool ok = Submit([&](VkCommandBuffer cmd) {
            BarrierImage(cmd, m_curr.image, m_currLayout,
                         VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                         VK_ACCESS_SHADER_READ_BIT, VK_ACCESS_TRANSFER_READ_BIT,
                         VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT);
            m_currLayout = VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL;
            TransitionInternal(cmd, m_prev, m_prevLayout,
                               VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                               VK_ACCESS_TRANSFER_WRITE_BIT);
            Copy(cmd, m_curr.image, m_prev.image, m_extent);
            BarrierImage(cmd, m_prev.image, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                         VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
                         VK_ACCESS_TRANSFER_WRITE_BIT, VK_ACCESS_SHADER_READ_BIT,
                         VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT);
            m_prevLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL;
            BarrierImage(cmd, m_curr.image, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                         VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL,
                         VK_ACCESS_TRANSFER_READ_BIT, VK_ACCESS_SHADER_READ_BIT,
                         VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_COMPUTE_SHADER_BIT);
            m_currLayout = VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL;
        }, VK_NULL_HANDLE);
        if (ok)
            m_havePrev = true;
        return ok;
    }

private:
    static constexpr VkFormat kInternalFormat = VK_FORMAT_R8G8B8A8_UNORM;

    struct ImageRes {
        VkImage image{VK_NULL_HANDLE};
        VkDeviceMemory memory{VK_NULL_HANDLE};
        VkImageView view{VK_NULL_HANDLE};
    };

    std::mutex m_lock;
    VkPhysicalDevice m_physical{VK_NULL_HANDLE};
    VkDevice m_device{VK_NULL_HANDLE};
    VkQueue m_queue{VK_NULL_HANDLE};
    uint32_t m_family{0};
    VkExtent2D m_extent{};
    VkCommandPool m_commandPool{VK_NULL_HANDLE};
    VkCommandBuffer m_commandBuffer{VK_NULL_HANDLE};
    VkFence m_fence{VK_NULL_HANDLE};
    VkSampler m_sampler{VK_NULL_HANDLE};
    VkDescriptorSetLayout m_descriptorLayout{VK_NULL_HANDLE};
    VkDescriptorPool m_descriptorPool{VK_NULL_HANDLE};
    VkDescriptorSet m_descriptorSet{VK_NULL_HANDLE};
    VkPipelineLayout m_pipelineLayout{VK_NULL_HANDLE};
    VkPipeline m_pipeline{VK_NULL_HANDLE};
    ImageRes m_prev{}, m_curr{}, m_generated{};
    VkImageLayout m_prevLayout{VK_IMAGE_LAYOUT_UNDEFINED};
    VkImageLayout m_currLayout{VK_IMAGE_LAYOUT_UNDEFINED};
    VkImageLayout m_generatedLayout{VK_IMAGE_LAYOUT_UNDEFINED};
    bool m_havePrev{false};
    bool m_ready{false};

    uint32_t MemoryType(uint32_t bits, VkMemoryPropertyFlags wanted)
    {
        VkPhysicalDeviceMemoryProperties props{};
        vkGetPhysicalDeviceMemoryProperties(m_physical, &props);
        for (uint32_t i = 0; i < props.memoryTypeCount; ++i) {
            if ((bits & (1u << i)) &&
                (props.memoryTypes[i].propertyFlags & wanted) == wanted)
                return i;
        }
        return UINT32_MAX;
    }

    bool MakeImage(ImageRes& r, VkImageUsageFlags usage)
    {
        VkImageCreateInfo ci{};
        ci.sType = VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO;
        ci.imageType = VK_IMAGE_TYPE_2D;
        ci.format = kInternalFormat;
        ci.extent = {m_extent.width, m_extent.height, 1};
        ci.mipLevels = 1;
        ci.arrayLayers = 1;
        ci.samples = VK_SAMPLE_COUNT_1_BIT;
        ci.tiling = VK_IMAGE_TILING_OPTIMAL;
        ci.usage = usage;
        ci.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
        ci.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
        if (vkCreateImage(m_device, &ci, nullptr, &r.image) != VK_SUCCESS)
            return false;

        VkMemoryRequirements req{};
        vkGetImageMemoryRequirements(m_device, r.image, &req);
        uint32_t type = MemoryType(req.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
        if (type == UINT32_MAX)
            return false;
        VkMemoryAllocateInfo ai{};
        ai.sType = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO;
        ai.allocationSize = req.size;
        ai.memoryTypeIndex = type;
        if (vkAllocateMemory(m_device, &ai, nullptr, &r.memory) != VK_SUCCESS)
            return false;
        if (vkBindImageMemory(m_device, r.image, r.memory, 0) != VK_SUCCESS)
            return false;

        VkImageViewCreateInfo vi{};
        vi.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
        vi.image = r.image;
        vi.viewType = VK_IMAGE_VIEW_TYPE_2D;
        vi.format = kInternalFormat;
        vi.subresourceRange.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
        vi.subresourceRange.levelCount = 1;
        vi.subresourceRange.layerCount = 1;
        return vkCreateImageView(m_device, &vi, nullptr, &r.view) == VK_SUCCESS;
    }

    void DestroyImage(ImageRes& r)
    {
        if (!m_device) return;
        if (r.view) vkDestroyImageView(m_device, r.view, nullptr);
        if (r.image) vkDestroyImage(m_device, r.image, nullptr);
        if (r.memory) vkFreeMemory(m_device, r.memory, nullptr);
        r = {};
    }

    void Cleanup()
    {
        if (!m_device) return;
        vkDeviceWaitIdle(m_device);
        if (m_pipeline) vkDestroyPipeline(m_device, m_pipeline, nullptr);
        if (m_pipelineLayout) vkDestroyPipelineLayout(m_device, m_pipelineLayout, nullptr);
        if (m_descriptorPool) vkDestroyDescriptorPool(m_device, m_descriptorPool, nullptr);
        if (m_descriptorLayout) vkDestroyDescriptorSetLayout(m_device, m_descriptorLayout, nullptr);
        if (m_sampler) vkDestroySampler(m_device, m_sampler, nullptr);
        if (m_fence) vkDestroyFence(m_device, m_fence, nullptr);
        if (m_commandPool) vkDestroyCommandPool(m_device, m_commandPool, nullptr);
        DestroyImage(m_prev);
        DestroyImage(m_curr);
        DestroyImage(m_generated);
        m_pipeline = VK_NULL_HANDLE;
        m_pipelineLayout = VK_NULL_HANDLE;
        m_descriptorPool = VK_NULL_HANDLE;
        m_descriptorLayout = VK_NULL_HANDLE;
        m_sampler = VK_NULL_HANDLE;
        m_fence = VK_NULL_HANDLE;
        m_commandPool = VK_NULL_HANDLE;
        m_commandBuffer = VK_NULL_HANDLE;
        m_prevLayout = m_currLayout = m_generatedLayout = VK_IMAGE_LAYOUT_UNDEFINED;
        m_havePrev = false;
        m_ready = false;
    }

    bool Ensure(VkPhysicalDevice physical, VkDevice device, VkQueue queue,
                uint32_t family, VkExtent2D extent)
    {
        if (m_ready && m_device == device && m_extent.width == extent.width &&
            m_extent.height == extent.height)
            return true;

        Cleanup();
        m_physical = physical;
        m_device = device;
        m_queue = queue;
        m_family = family;
        m_extent = extent;

        VkFormatProperties fp{};
        vkGetPhysicalDeviceFormatProperties(m_physical, kInternalFormat, &fp);
        const VkFormatFeatureFlags needed = VK_FORMAT_FEATURE_SAMPLED_IMAGE_BIT |
                                            VK_FORMAT_FEATURE_STORAGE_IMAGE_BIT |
                                            VK_FORMAT_FEATURE_BLIT_SRC_BIT |
                                            VK_FORMAT_FEATURE_BLIT_DST_BIT;
        if ((fp.optimalTilingFeatures & needed) != needed) {
            g_cfg.status.store(2);
            return false;
        }

        if (!MakeImage(m_prev, VK_IMAGE_USAGE_TRANSFER_SRC_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT | VK_IMAGE_USAGE_SAMPLED_BIT) ||
            !MakeImage(m_curr, VK_IMAGE_USAGE_TRANSFER_SRC_BIT | VK_IMAGE_USAGE_TRANSFER_DST_BIT | VK_IMAGE_USAGE_SAMPLED_BIT) ||
            !MakeImage(m_generated, VK_IMAGE_USAGE_TRANSFER_SRC_BIT | VK_IMAGE_USAGE_STORAGE_BIT)) {
            g_cfg.status.store(2);
            return false;
        }

        VkCommandPoolCreateInfo pci{};
        pci.sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO;
        pci.flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT;
        pci.queueFamilyIndex = m_family;
        if (vkCreateCommandPool(m_device, &pci, nullptr, &m_commandPool) != VK_SUCCESS)
            return Fail();
        VkCommandBufferAllocateInfo cai{};
        cai.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO;
        cai.commandPool = m_commandPool;
        cai.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY;
        cai.commandBufferCount = 1;
        if (vkAllocateCommandBuffers(m_device, &cai, &m_commandBuffer) != VK_SUCCESS)
            return Fail();
        VkFenceCreateInfo fci{};
        fci.sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO;
        if (vkCreateFence(m_device, &fci, nullptr, &m_fence) != VK_SUCCESS)
            return Fail();

        VkSamplerCreateInfo sci{};
        sci.sType = VK_STRUCTURE_TYPE_SAMPLER_CREATE_INFO;
        sci.magFilter = VK_FILTER_LINEAR;
        sci.minFilter = VK_FILTER_LINEAR;
        sci.mipmapMode = VK_SAMPLER_MIPMAP_MODE_NEAREST;
        sci.addressModeU = sci.addressModeV = sci.addressModeW = VK_SAMPLER_ADDRESS_MODE_CLAMP_TO_EDGE;
        sci.maxLod = 1.0f;
        if (vkCreateSampler(m_device, &sci, nullptr, &m_sampler) != VK_SUCCESS)
            return Fail();

        VkDescriptorSetLayoutBinding bindings[3]{};
        for (uint32_t i = 0; i < 2; ++i) {
            bindings[i].binding = i;
            bindings[i].descriptorType = VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;
            bindings[i].descriptorCount = 1;
            bindings[i].stageFlags = VK_SHADER_STAGE_COMPUTE_BIT;
        }
        bindings[2].binding = 2;
        bindings[2].descriptorType = VK_DESCRIPTOR_TYPE_STORAGE_IMAGE;
        bindings[2].descriptorCount = 1;
        bindings[2].stageFlags = VK_SHADER_STAGE_COMPUTE_BIT;
        VkDescriptorSetLayoutCreateInfo dl{};
        dl.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO;
        dl.bindingCount = 3;
        dl.pBindings = bindings;
        if (vkCreateDescriptorSetLayout(m_device, &dl, nullptr, &m_descriptorLayout) != VK_SUCCESS)
            return Fail();

        VkDescriptorPoolSize ps[2]{};
        ps[0] = {VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER, 2};
        ps[1] = {VK_DESCRIPTOR_TYPE_STORAGE_IMAGE, 1};
        VkDescriptorPoolCreateInfo dp{};
        dp.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO;
        dp.maxSets = 1;
        dp.poolSizeCount = 2;
        dp.pPoolSizes = ps;
        if (vkCreateDescriptorPool(m_device, &dp, nullptr, &m_descriptorPool) != VK_SUCCESS)
            return Fail();
        VkDescriptorSetAllocateInfo da{};
        da.sType = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO;
        da.descriptorPool = m_descriptorPool;
        da.descriptorSetCount = 1;
        da.pSetLayouts = &m_descriptorLayout;
        if (vkAllocateDescriptorSets(m_device, &da, &m_descriptorSet) != VK_SUCCESS)
            return Fail();

        VkDescriptorImageInfo imgs[3]{};
        imgs[0] = {m_sampler, m_prev.view, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL};
        imgs[1] = {m_sampler, m_curr.view, VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL};
        imgs[2] = {VK_NULL_HANDLE, m_generated.view, VK_IMAGE_LAYOUT_GENERAL};
        VkWriteDescriptorSet writes[3]{};
        for (uint32_t i = 0; i < 3; ++i) {
            writes[i].sType = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET;
            writes[i].dstSet = m_descriptorSet;
            writes[i].dstBinding = i;
            writes[i].descriptorCount = 1;
            writes[i].descriptorType = (i == 2) ? VK_DESCRIPTOR_TYPE_STORAGE_IMAGE : VK_DESCRIPTOR_TYPE_COMBINED_IMAGE_SAMPLER;
            writes[i].pImageInfo = &imgs[i];
        }
        vkUpdateDescriptorSets(m_device, 3, writes, 0, nullptr);

        VkPushConstantRange pc{};
        pc.stageFlags = VK_SHADER_STAGE_COMPUTE_BIT;
        pc.offset = 0;
        pc.size = sizeof(float);
        VkPipelineLayoutCreateInfo pl{};
        pl.sType = VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO;
        pl.setLayoutCount = 1;
        pl.pSetLayouts = &m_descriptorLayout;
        pl.pushConstantRangeCount = 1;
        pl.pPushConstantRanges = &pc;
        if (vkCreatePipelineLayout(m_device, &pl, nullptr, &m_pipelineLayout) != VK_SUCCESS)
            return Fail();

        VkShaderModuleCreateInfo sm{};
        sm.sType = VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO;
        sm.codeSize = kWudroidFrameGenBlendSpvSize;
        sm.pCode = kWudroidFrameGenBlendSpv;
        VkShaderModule shader{VK_NULL_HANDLE};
        if (vkCreateShaderModule(m_device, &sm, nullptr, &shader) != VK_SUCCESS)
            return Fail();
        VkPipelineShaderStageCreateInfo stage{};
        stage.sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
        stage.stage = VK_SHADER_STAGE_COMPUTE_BIT;
        stage.module = shader;
        stage.pName = "main";
        VkComputePipelineCreateInfo cp{};
        cp.sType = VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO;
        cp.stage = stage;
        cp.layout = m_pipelineLayout;
        VkResult pr = vkCreateComputePipelines(m_device, VK_NULL_HANDLE, 1, &cp, nullptr, &m_pipeline);
        vkDestroyShaderModule(m_device, shader, nullptr);
        if (pr != VK_SUCCESS)
            return Fail();

        m_ready = true;
        g_cfg.status.store(1);
        return true;
    }

    bool Fail() {
        g_cfg.status.store(2);
        return false;
    }

    template<typename Fn>
    bool Submit(Fn&& record, VkSemaphore waitSemaphore)
    {
        vkResetFences(m_device, 1, &m_fence);
        vkResetCommandBuffer(m_commandBuffer, 0);
        VkCommandBufferBeginInfo bi{};
        bi.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
        bi.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
        if (vkBeginCommandBuffer(m_commandBuffer, &bi) != VK_SUCCESS)
            return false;
        record(m_commandBuffer);
        if (vkEndCommandBuffer(m_commandBuffer) != VK_SUCCESS)
            return false;

        VkPipelineStageFlags waitStage = VK_PIPELINE_STAGE_ALL_COMMANDS_BIT;
        VkSubmitInfo si{};
        si.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO;
        if (waitSemaphore != VK_NULL_HANDLE) {
            si.waitSemaphoreCount = 1;
            si.pWaitSemaphores = &waitSemaphore;
            si.pWaitDstStageMask = &waitStage;
        }
        si.commandBufferCount = 1;
        si.pCommandBuffers = &m_commandBuffer;
        if (vkQueueSubmit(m_queue, 1, &si, m_fence) != VK_SUCCESS)
            return false;
        return vkWaitForFences(m_device, 1, &m_fence, VK_TRUE, UINT64_MAX) == VK_SUCCESS;
    }

    void TransitionInternal(VkCommandBuffer cmd, ImageRes& r, VkImageLayout& layout,
                            VkImageLayout next, VkAccessFlags dst)
    {
        VkAccessFlags src = 0;
        if (layout == VK_IMAGE_LAYOUT_SHADER_READ_ONLY_OPTIMAL) src = VK_ACCESS_SHADER_READ_BIT;
        else if (layout == VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL) src = VK_ACCESS_TRANSFER_READ_BIT;
        else if (layout == VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL) src = VK_ACCESS_TRANSFER_WRITE_BIT;
        else if (layout == VK_IMAGE_LAYOUT_GENERAL) src = VK_ACCESS_SHADER_WRITE_BIT;
        BarrierImage(cmd, r.image, layout, next, src, dst);
        layout = next;
    }

    static void Copy(VkCommandBuffer cmd, VkImage src, VkImage dst, VkExtent2D extent)
    {
        VkImageCopy c{};
        c.srcSubresource.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
        c.srcSubresource.layerCount = 1;
        c.dstSubresource.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
        c.dstSubresource.layerCount = 1;
        c.extent = {extent.width, extent.height, 1};
        vkCmdCopyImage(cmd, src, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                       dst, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &c);
    }

    static void Blit(VkCommandBuffer cmd, VkImage src, VkFormat, VkImage dst, VkFormat,
                     VkExtent2D extent)
    {
        VkImageBlit b{};
        b.srcSubresource.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
        b.srcSubresource.layerCount = 1;
        b.srcOffsets[1] = {(int32_t)extent.width, (int32_t)extent.height, 1};
        b.dstSubresource.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
        b.dstSubresource.layerCount = 1;
        b.dstOffsets[1] = {(int32_t)extent.width, (int32_t)extent.height, 1};
        vkCmdBlitImage(cmd, src, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL,
                       dst, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL,
                       1, &b, VK_FILTER_LINEAR);
    }
};

static Engine g_engine;

} // namespace WudroidFrameGenVk

extern "C" void WudroidFrameGen_SetConfig(int enabled, int multiplier, float flowScale, int preset)
{
    WudroidFrameGenVk::g_cfg.enabled.store(enabled ? 1 : 0);
    WudroidFrameGenVk::g_cfg.multiplier.store(std::clamp(multiplier, 2, 4));
    WudroidFrameGenVk::g_cfg.flowScale.store(std::clamp(flowScale, 0.20f, 1.00f));
    WudroidFrameGenVk::g_cfg.preset.store(std::clamp(preset, 0, 5));
}

extern "C" int WudroidFrameGen_IsPresentHookActive()
{
    return WudroidFrameGenVk::g_cfg.presentHookActive.load();
}

extern "C" int WudroidFrameGen_IsOpticalFlowAdvertised()
{
    return WudroidFrameGenVk::g_cfg.opticalFlowAdvertised.load();
}

extern "C" uint64_t WudroidFrameGen_GetGeneratedFrameCount()
{
    return WudroidFrameGenVk::g_cfg.generatedFrames.load();
}

extern "C" const char* WudroidFrameGen_GetStatus()
{
    if (!WudroidFrameGenVk::g_cfg.enabled.load()) return "Wudroid FrameGen Vulkan • desativado";
    if (!WudroidFrameGenVk::g_cfg.presentHookActive.load()) return "Wudroid FrameGen Vulkan • aguardando renderer";
    if (WudroidFrameGenVk::g_cfg.status.load() == 2) return "Wudroid FrameGen Vulkan • falha ao criar pipeline";
    if (WudroidFrameGenVk::g_cfg.opticalFlowAdvertised.load()) return "Wudroid FrameGen Vulkan • temporal • Optical Flow disponível";
    return "Wudroid FrameGen Vulkan • temporal compute";
}

extern "C" int WudroidFrameGen_IsEnabledForPresent()
{
    return WudroidFrameGenVk::g_cfg.enabled.load();
}

extern "C" int WudroidFrameGen_GetMultiplier()
{
    return std::clamp(WudroidFrameGenVk::g_cfg.multiplier.load(), 2, 4);
}

extern "C" void WudroidFrameGen_DetectOpticalFlow(VkPhysicalDevice physical)
{
    uint32_t count = 0;
    bool found = false;
    if (vkEnumerateDeviceExtensionProperties(physical, nullptr, &count, nullptr) == VK_SUCCESS && count) {
        std::vector<VkExtensionProperties> props(count);
        if (vkEnumerateDeviceExtensionProperties(physical, nullptr, &count, props.data()) == VK_SUCCESS) {
            for (const auto& p : props) {
                if (std::strcmp(p.extensionName, "VK_NV_optical_flow") == 0) {
                    found = true;
                    break;
                }
            }
        }
    }
    WudroidFrameGenVk::g_cfg.opticalFlowAdvertised.store(found ? 1 : 0);
}
