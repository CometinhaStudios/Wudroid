# Wudroid 0.1.1 — FrameGen Vulkan Test9

Test build that replaces the previous Lossless.dll / MediaProjection capture path with an in-renderer Vulkan path.

## What changed

- Removes the LSFG-Android Gradle module from the Wudroid build workflow.
- No Lossless.dll import is required.
- No MediaProjection / overlay capture service is used.
- Hooks Cemu's Android Vulkan `SwapBuffer` / swapchain present path.
- Adds `VK_IMAGE_USAGE_TRANSFER_SRC_BIT` to the swapchain so rendered frames can be copied into Wudroid history textures.
- Detects whether the Vulkan driver advertises `VK_NV_optical_flow` and exposes that status to the Android UI.
- Generates synthetic frames in Test9 with a Wudroid-owned Vulkan compute shader that temporally interpolates previous/current real frames.
- Supports 2x / 3x / 4x presentation experiments and counts synthetic presents.
- Keeps the public Wudroid version at **0.1.1**.

## Important scope of Test9

The architecture is inspired by the direct-Vulkan approach used by GameHub/GameScopeVK, but no GameHub proprietary binary or code is bundled or copied.

Test9 is intentionally a first direct-renderer implementation: `VK_NV_optical_flow` detection is wired in, while the actual interpolation kernel is temporal blending. Motion-vector/optical-flow warping is the next renderer refinement after this path is proven to build, boot, and present synthetic frames correctly.

## Expected validation

1. GitHub Actions must pass Kotlin/Java and native release compilation.
2. A Vulkan game must boot with Frame Generation disabled exactly as before.
3. With Frame Generation enabled, the status should change to `Present Vulkan` active.
4. `Quadros sintéticos apresentados` should increase while a game is running.
5. 2x is the primary first test. 3x/4x are experimental.

