#!/usr/bin/env python3
from pathlib import Path
import re

root = Path("cemu-engine/src/Cafe/HW/Latte/Renderer/Vulkan")
hdr = root / "VulkanAPI.h"
cpp = root / "VulkanAPI.cpp"
if not hdr.exists() or not cpp.exists():
    raise SystemExit("Cemu VulkanAPI.h/.cpp not found")

h = hdr.read_text()

def ensure_decl(text: str, fn: str, anchors):
    decl = f"VKFUNC_DEVICE({fn});"
    if decl in text:
        return text
    for anchor in anchors:
        anchor_decl = f"VKFUNC_DEVICE({anchor});"
        if anchor_decl in text:
            return text.replace(anchor_decl, anchor_decl + "\\n" + decl, 1)
    raise SystemExit(f"Cannot patch VulkanAPI.h: no anchor found for {fn}")

h = ensure_decl(h, "vkCreateComputePipelines", ["vkCreateGraphicsPipelines"])
h = ensure_decl(h, "vkCmdDispatch", ["vkCmdDraw", "vkCmdDrawIndexed", "vkCmdBindPipeline"])
hdr.write_text(h)

s = cpp.read_text()

def has_loader_line(text: str, wanted: str) -> bool:
    for line in text.splitlines():
        if wanted in line and ("load" in line.lower() or "vkGetDeviceProcAddr" in line or "=" in line or "VKFUNC" in line):
            return True
    return False

def duplicate_loader_line(text: str, existing: str, wanted: str) -> str:
    if has_loader_line(text, wanted):
        return text
    candidates = []
    for m in re.finditer(rf"(?m)^.*\\b{re.escape(existing)}\\b.*$", text):
        line = m.group(0)
        low = line.lower()
        score = (4 if "load" in low else 0) + (4 if "vkgetdeviceprocaddr" in low else 0) + (2 if "=" in line else 0) + (1 if "vkfunc" in low else 0)
        candidates.append((score,m,line))
    if not candidates:
        raise SystemExit(f"Cannot patch VulkanAPI.cpp: no line containing {existing}")
    candidates.sort(key=lambda x:x[0], reverse=True)
    _,m,line = candidates[0]
    new_line = line.replace(existing, wanted)
    if new_line == line:
        raise SystemExit(f"Cannot derive loader line for {wanted}")
    return text[:m.end()] + "\\n" + new_line + text[m.end():]

s = duplicate_loader_line(s, "vkCreateGraphicsPipelines", "vkCreateComputePipelines")
for anchor in ["vkCmdDraw", "vkCmdDrawIndexed", "vkCmdBindPipeline"]:
    try:
        s = duplicate_loader_line(s, anchor, "vkCmdDispatch")
        break
    except SystemExit:
        continue
else:
    raise SystemExit("Cannot patch VulkanAPI.cpp: no command loader anchor for vkCmdDispatch")
cpp.write_text(s)

for p, needles in [
    (hdr,["VKFUNC_DEVICE(vkCreateComputePipelines);","VKFUNC_DEVICE(vkCmdDispatch);"]),
    (cpp,["vkCreateComputePipelines","vkCmdDispatch"]),
]:
    t=p.read_text()
    for needle in needles:
        if needle not in t:
            raise SystemExit(f"Vulkan loader patch verification failed: {needle} missing from {p}")
print("Wudroid 0.1.1 Test9: Cemu Vulkan compute dispatch functions enabled")
