#!/usr/bin/env python3
from pathlib import Path
import re

root = Path("cemu-engine")
shader = root / "src/Cafe/HW/Latte/Core/LatteShaderCache.cpp"
if not shader.exists():
    raise SystemExit("LatteShaderCache.cpp not found")
s = shader.read_text()

if "#include <cstdlib>" not in s:
    m = re.search(r'(?m)^#include .+$', s)
    if m:
        s = s[:m.end()] + "\n#include <cstdlib>" + s[m.end():]

if "WudroidShaderPreload_IsEnabled" not in s:
    insert_at = s.find("void LatteShaderCache_Load()")
    if insert_at < 0:
        raise SystemExit("LatteShaderCache_Load anchor missing")
    helper = '''#if BOOST_PLAT_ANDROID
static bool WudroidShaderPreload_IsEnabled()
{
    const char* value = std::getenv("WUDROID_SHADER_PRELOAD");
    return value == nullptr || value[0] != '0';
}
#endif

'''
    s = s[:insert_at] + helper + s[insert_at:]

start = "void LatteShaderCache_Load()\n{"
if "[Wudroid ShaderPreload] begin" not in s:
    if start not in s:
        raise SystemExit("LatteShaderCache_Load start anchor missing")
    s = s.replace(start, start + '''
#if BOOST_PLAT_ANDROID
    if (WudroidShaderPreload_IsEnabled())
        cemuLog_log(LogType::Force, "[Wudroid ShaderPreload] begin: compiling cached shaders and pipelines before gameplay");
#endif''', 1)

queue_anchor = "LatteShaderCache_updateCompileQueue(0);"
if "[Wudroid ShaderPreload] cached shaders ready" not in s:
    if queue_anchor not in s:
        raise SystemExit("shader compile queue drain anchor missing")
    s = s.replace(queue_anchor, queue_anchor + '''
#if BOOST_PLAT_ANDROID
    if (WudroidShaderPreload_IsEnabled())
        cemuLog_log(LogType::Force, "[Wudroid ShaderPreload] cached shaders ready");
#endif''', 1)

pipe_anchor = "LatteShaderCache_LoadPipelineCache(cacheTitleId);"
if "[Wudroid ShaderPreload] cached pipelines ready" not in s:
    if pipe_anchor not in s:
        raise SystemExit("pipeline cache load anchor missing")
    s = s.replace(pipe_anchor, pipe_anchor + '''
#if BOOST_PLAT_ANDROID
        if (WudroidShaderPreload_IsEnabled())
            cemuLog_log(LogType::Force, "[Wudroid ShaderPreload] cached pipelines ready; releasing gameplay");
#endif''', 1)

s = s.replace('text = "Loading cached pipelines...";', 'text = "Wudroid: pre-loading cached pipelines...";')
s = s.replace('text = "Compiling cached shaders...";', 'text = "Wudroid: compiling cached shaders...";')
s = s.replace('text = "Loading cached shaders...";', 'text = "Wudroid: pre-loading cached shaders...";')
shader.write_text(s)

final = shader.read_text()
for needle in [
    "LatteShaderCache_updateCompileQueue(0);",
    "LatteShaderCache_LoadPipelineCache(cacheTitleId);",
    "[Wudroid ShaderPreload] cached pipelines ready",
]:
    if needle not in final:
        raise SystemExit(f"Shader preload verification failed: {needle}")

print("Wudroid 0.1.1 Shader Preload Test1 applied")
print("cached shaders -> compile queue drain -> Vulkan pipelines -> gameplay")
