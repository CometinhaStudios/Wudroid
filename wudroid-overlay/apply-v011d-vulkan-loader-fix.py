#!/usr/bin/env python3
from pathlib import Path
import re

root = Path("cemu-engine/src/Cafe/HW/Latte/Renderer/Vulkan")
hdr = root / "VulkanAPI.h"
cpp = root / "VulkanAPI.cpp"
if not hdr.exists() or not cpp.exists():
    raise SystemExit("Cemu VulkanAPI.h/.cpp not found")

# Cemu's Android branch can expose the Vulkan device-function table primarily
# from VulkanAPI.h.  Older Wudroid tests assumed VulkanAPI.cpp contained a
# literal vkCreateGraphicsPipelines loader line, which is not true for every
# branch/revision.  Patch the header first, then patch .cpp only when its loader
# layout is explicit and can be detected safely.

h = hdr.read_text()

def ensure_decl(text: str, fn: str, anchors):
    decl = f"VKFUNC_DEVICE({fn});"
    if decl in text:
        return text, False

    for anchor in anchors:
        anchor_decl = f"VKFUNC_DEVICE({anchor});"
        if anchor_decl in text:
            return text.replace(anchor_decl, anchor_decl + "\n" + decl, 1), True

    # Fallback: insert beside any device function declaration.  This keeps the
    # patch compatible with branches that don't list the exact graphics/draw
    # anchors used by desktop Cemu.
    matches = list(re.finditer(r"(?m)^\s*VKFUNC_DEVICE\([^\n]+\);\s*$", text))
    if matches:
        m = matches[-1]
        return text[:m.end()] + "\n" + decl + text[m.end():], True

    raise SystemExit(f"Cannot patch VulkanAPI.h: no VKFUNC_DEVICE declaration block found for {fn}")

h, added_compute = ensure_decl(
    h,
    "vkCreateComputePipelines",
    ["vkCreateGraphicsPipelines", "vkCreatePipelineLayout", "vkCreateShaderModule", "vkCreatePipelineCache"],
)
h, added_dispatch = ensure_decl(
    h,
    "vkCmdDispatch",
    ["vkCmdDraw", "vkCmdDrawIndexed", "vkCmdBindPipeline", "vkCmdPipelineBarrier"],
)
hdr.write_text(h)

s = cpp.read_text()

# Only duplicate an explicit loader line when the current VulkanAPI.cpp
# actually contains one.  Some Cemu revisions drive the device function list
# from VulkanAPI.h, so absence of an explicit line in .cpp is not an error.
def has_loader_line(text: str, fn: str) -> bool:
    for line in text.splitlines():
        if fn not in line:
            continue
        low = line.lower()
        if (
            "vkgetdeviceprocaddr" in low
            or "load" in low
            or "proc" in low
            or "vkfunc" in low
            or "=" in line
        ):
            return True
    return False


def duplicate_explicit_loader(text: str, wanted: str, anchors) -> tuple[str, bool]:
    if wanted in text and has_loader_line(text, wanted):
        return text, False

    candidates = []
    for existing in anchors:
        for m in re.finditer(rf"(?m)^.*\b{re.escape(existing)}\b.*$", text):
            line = m.group(0)
            low = line.lower()
            if not (
                "vkgetdeviceprocaddr" in low
                or "load" in low
                or "proc" in low
                or "vkfunc" in low
                or "=" in line
            ):
                continue
            score = (
                (8 if "vkgetdeviceprocaddr" in low else 0)
                + (5 if "load" in low else 0)
                + (3 if "proc" in low else 0)
                + (2 if "vkfunc" in low else 0)
                + (1 if "=" in line else 0)
            )
            candidates.append((score, m, line, existing))

    if not candidates:
        return text, False

    candidates.sort(key=lambda x: x[0], reverse=True)
    _, m, line, existing = candidates[0]
    new_line = line.replace(existing, wanted)
    if new_line == line:
        return text, False
    return text[:m.end()] + "\n" + new_line + text[m.end():], True

s, cpp_compute = duplicate_explicit_loader(
    s,
    "vkCreateComputePipelines",
    [
        "vkCreateGraphicsPipelines",
        "vkCreatePipelineLayout",
        "vkCreateShaderModule",
        "vkCreatePipelineCache",
        "vkCreateDescriptorSetLayout",
    ],
)
s, cpp_dispatch = duplicate_explicit_loader(
    s,
    "vkCmdDispatch",
    [
        "vkCmdDraw",
        "vkCmdDrawIndexed",
        "vkCmdBindPipeline",
        "vkCmdPipelineBarrier",
        "vkCmdCopyBuffer",
    ],
)
cpp.write_text(s)

# Header declarations are mandatory; .cpp loader additions are conditional.
# If this branch uses a header-driven/generated dispatch table, the header is
# the source of truth and the compilation step will verify it naturally.
final_h = hdr.read_text()
for needle in [
    "VKFUNC_DEVICE(vkCreateComputePipelines);",
    "VKFUNC_DEVICE(vkCmdDispatch);",
]:
    if needle not in final_h:
        raise SystemExit(f"Vulkan loader patch verification failed: {needle} missing from {hdr}")

print(
    "Wudroid 0.1.1 Test10: Vulkan compute API declarations enabled; "
    f"header_added_compute={added_compute}, header_added_dispatch={added_dispatch}, "
    f"cpp_loader_compute={cpp_compute}, cpp_loader_dispatch={cpp_dispatch}"
)
if not cpp_compute and not cpp_dispatch:
    print(
        "Wudroid Test10: VulkanAPI.cpp has no compatible explicit loader lines; "
        "continuing with Cemu's header-driven/generated loader layout"
    )
