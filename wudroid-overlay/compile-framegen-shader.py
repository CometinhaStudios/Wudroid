#!/usr/bin/env python3
from pathlib import Path
import os, shutil, struct, subprocess, sys

root = Path(__file__).resolve().parent
src = root / "wudroid_framegen.comp"
spv = root / "wudroid_framegen.comp.spv"
header = root / "WudroidFrameGenShaderSpv.h"

candidates = []
for env in ("ANDROID_NDK_HOME", "ANDROID_NDK_ROOT", "NDK_HOME"):
    value = os.environ.get(env)
    if value:
        candidates += [
            Path(value) / "shader-tools/linux-x86_64/glslc",
            Path(value) / "shader-tools/darwin-x86_64/glslc",
            Path(value) / "shader-tools/windows-x86_64/glslc.exe",
        ]

sdk = os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME")
if sdk:
    ndk_root = Path(sdk) / "ndk"
    if ndk_root.exists():
        for ndk in sorted(ndk_root.iterdir(), reverse=True):
            candidates += [
                ndk / "shader-tools/linux-x86_64/glslc",
                ndk / "shader-tools/darwin-x86_64/glslc",
                ndk / "shader-tools/windows-x86_64/glslc.exe",
            ]

for name in ("glslc", "glslangValidator"):
    p = shutil.which(name)
    if p:
        candidates.append(Path(p))

tool = next((p for p in candidates if p.exists()), None)
if tool is None:
    raise SystemExit(
        "No GLSL -> SPIR-V compiler found. Install Android NDK shader-tools, glslc, or glslangValidator."
    )

if "glslangValidator" in tool.name:
    cmd = [str(tool), "-V", "-S", "comp", "-o", str(spv), str(src)]
else:
    cmd = [str(tool), "-fshader-stage=compute", "--target-env=vulkan1.1", "-O", "-o", str(spv), str(src)]

print("Wudroid FrameGen shader compiler:", tool)
subprocess.run(cmd, check=True)
data = spv.read_bytes()
if len(data) < 20 or data[:4] != b"\x03\x02\x23\x07":
    raise SystemExit("Generated file is not a valid SPIR-V module")
if len(data) % 4:
    raise SystemExit("SPIR-V size is not 32-bit aligned")
words = struct.unpack("<%dI" % (len(data) // 4), data)
lines = []
for i in range(0, len(words), 8):
    lines.append("    " + ", ".join(f"0x{w:08x}u" for w in words[i:i+8]) + ",")
header.write_text(
    "#pragma once\n#include <cstddef>\n#include <cstdint>\n\n"
    "static const uint32_t kWudroidFrameGenCompSpv[] = {\n"
    + "\n".join(lines)
    + "\n};\n"
    + f"static constexpr size_t kWudroidFrameGenCompSpvBytes = {len(data)}u;\n"
)
print(f"Generated {header.name}: {len(data)} bytes SPIR-V")
