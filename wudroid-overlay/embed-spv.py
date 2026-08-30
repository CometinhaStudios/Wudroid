#!/usr/bin/env python3
from pathlib import Path
import struct, sys

if len(sys.argv) != 3:
    raise SystemExit("usage: embed-spv.py input.spv output.h")
raw = Path(sys.argv[1]).read_bytes()
if len(raw) % 4:
    raise SystemExit("SPIR-V length is not a multiple of 4")
words = struct.unpack("<%dI" % (len(raw)//4), raw)
lines = ["#pragma once", "#include <cstddef>", "#include <cstdint>", "",
         "static const uint32_t kWudroidFrameGenBlendSpv[] = {"]
for i in range(0, len(words), 8):
    lines.append("    " + ", ".join(f"0x{w:08x}u" for w in words[i:i+8]) + ",")
lines += ["};", f"static const size_t kWudroidFrameGenBlendSpvSize = {len(raw)}u;", ""]
Path(sys.argv[2]).write_text("\n".join(lines))
