#!/usr/bin/env python3
from pathlib import Path
import re

screen_path = Path('cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationScreen.kt')
native_kt_path = Path('cemu-engine/src/android/app/src/main/java/info/cemu/cemu/nativeinterface/NativeEmulation.kt')
native_cpp_path = Path('cemu-engine/src/android/app/src/main/cpp/NativeEmulation.cpp')

for p in (screen_path, native_kt_path, native_cpp_path):
    if not p.exists():
        raise SystemExit(f'Required source not found: {p}')

screen = screen_path.read_text()
native_kt = native_kt_path.read_text()
native_cpp = native_cpp_path.read_text()
marker = 'WUDROID_QUICKSTATE_ENGINE_TEST10'
if marker in screen:
    print('Wudroid Quick State Engine Test10 already applied')
    raise SystemExit(0)

if 'WUDROID_EDITOR_POLISH_PTBR_TEST9_BUILDFIX1' not in screen:
    raise SystemExit('Test9 BuildFix1 must be applied before Quick State Test10')

# ---------------------------------------------------------------------------
# 1) NativeEmulation.kt: expose a minimal native quick-state bridge.
# ---------------------------------------------------------------------------
kt_anchor = '''    @JvmStatic
    external fun supportsLoadingCustomDriver(): Boolean
'''
if kt_anchor not in native_kt:
    raise SystemExit('NativeEmulation Kotlin anchor missing')
kt_insert = '''    // WUDROID_QUICKSTATE_ENGINE_TEST10
    // Experimental same-session state snapshot. The first engine revision
    // stores/restores committed writable Wii U guest RAM. Full CPU/GPU
    // component serialization is added incrementally in later revisions.
    @JvmStatic
    external fun saveQuickState(path: String): Int

    @JvmStatic
    external fun loadQuickState(path: String): Int

'''
native_kt = native_kt.replace(kt_anchor, kt_insert + kt_anchor, 1)
native_kt_path.write_text(native_kt)

# ---------------------------------------------------------------------------
# 2) NativeEmulation.cpp: NetherSX2/PCSX2-inspired state container model.
#    This code is original Wudroid code; it does NOT copy PS2 emulator code.
#
#    Test10 is intentionally a SAME-SESSION snapshot engine:
#    - validates PID + Cemu guest base before loading
#    - records only actually committed read/write mappings inside Wii U RAM
#    - records zero chunks without storing their bytes
#    - leaves emulation paused; the existing Wudroid menu flow resumes it
#
#    It is a real guest-RAM rewind foundation, not yet a complete persistent
#    Cemu savestate (CPU/GPU/audio serializers come in later engine stages).
# ---------------------------------------------------------------------------
cpp_includes = '''
// WUDROID_QUICKSTATE_ENGINE_TEST10
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <filesystem>
#include <limits>
#include <string>
#include <vector>
#include <unistd.h>

namespace fs = std::filesystem;

// Cemu exposes the base of the 4 GiB guest address reservation.
extern "C" void* memory_getBase();
'''
if 'WUDROID_QUICKSTATE_ENGINE_TEST10' not in native_cpp:
    # Put the standard-library additions after the existing include block's first line.
    first_nl = native_cpp.find('\n')
    if first_nl < 0:
        raise SystemExit('NativeEmulation.cpp malformed')
    native_cpp = native_cpp[:first_nl+1] + cpp_includes + native_cpp[first_nl+1:]

namespace_anchor = '} // namespace NativeEmulation'
if namespace_anchor not in native_cpp:
    raise SystemExit('NativeEmulation namespace closing anchor missing')

state_impl = r'''

namespace WudroidQuickState
{
constexpr uint32_t kFormatVersion = 1;
constexpr uint32_t kChunkSize = 64 * 1024;
constexpr uint64_t kGuestSpaceSize = 0x100000000ULL;
constexpr uint64_t kMaxStoredBytes = 1536ULL * 1024ULL * 1024ULL;
constexpr uint32_t kChunkFlagZero = 1u;

struct StateHeader
{
    char magic[8];
    uint32_t version;
    uint32_t pid;
    uint64_t guestBase;
    uint32_t chunkSize;
    uint32_t chunkCount;
    uint64_t storedBytes;
};

struct ChunkHeader
{
    uint64_t guestOffset;
    uint32_t size;
    uint32_t flags;
};

struct HostRange
{
    uintptr_t begin;
    uintptr_t end;
};

struct GuestWindow
{
    uint64_t begin;
    uint64_t end;
};

// Physical/virtual RAM windows relevant to Cafe applications. MMIO-only holes
// are intentionally omitted. The actual /proc/self/maps permissions are still
// checked before any byte is read or restored.
constexpr std::array<GuestWindow, 4> kGuestRamWindows{{
    {0x00000000ULL, 0x02000000ULL}, // MEM1 (32 MiB)
    {0x10000000ULL, 0x28000000ULL}, // MEM2 system/PPC + RAM disk
    {0x28000000ULL, 0x90000000ULL}, // MEM2-B / Cafe application memory
    {0xFFC00000ULL, 0x100000000ULL}, // Cafe codegen/kernel mirror area
}};

static std::vector<HostRange> CollectWritableMappings()
{
    std::vector<HostRange> ranges;
    std::ifstream maps("/proc/self/maps");
    std::string line;
    while (std::getline(maps, line))
    {
        unsigned long long begin = 0;
        unsigned long long end = 0;
        char perms[5]{};
        if (std::sscanf(line.c_str(), "%llx-%llx %4s", &begin, &end, perms) != 3)
            continue;
        if (perms[0] != 'r' || perms[1] != 'w')
            continue;
        if (begin >= end)
            continue;
        ranges.push_back({static_cast<uintptr_t>(begin), static_cast<uintptr_t>(end)});
    }
    return ranges;
}

static bool IsWritableRange(const std::vector<HostRange>& maps, uintptr_t begin, uintptr_t end)
{
    for (const auto& map : maps)
    {
        if (begin >= map.begin && end <= map.end)
            return true;
    }
    return false;
}

static std::vector<HostRange> CollectGuestRamRanges(uintptr_t guestBase)
{
    const auto maps = CollectWritableMappings();
    std::vector<HostRange> out;
    const uintptr_t guestEnd = guestBase + static_cast<uintptr_t>(kGuestSpaceSize);

    for (const auto& map : maps)
    {
        const uintptr_t mapBegin = std::max(map.begin, guestBase);
        const uintptr_t mapEnd = std::min(map.end, guestEnd);
        if (mapBegin >= mapEnd)
            continue;

        for (const auto& window : kGuestRamWindows)
        {
            const uintptr_t windowBegin = guestBase + static_cast<uintptr_t>(window.begin);
            const uintptr_t windowEnd = guestBase + static_cast<uintptr_t>(window.end);
            const uintptr_t begin = std::max(mapBegin, windowBegin);
            const uintptr_t end = std::min(mapEnd, windowEnd);
            if (begin < end)
                out.push_back({begin, end});
        }
    }

    std::sort(out.begin(), out.end(), [](const HostRange& a, const HostRange& b) {
        return a.begin < b.begin;
    });

    std::vector<HostRange> merged;
    for (const auto& range : out)
    {
        if (!merged.empty() && range.begin <= merged.back().end)
            merged.back().end = std::max(merged.back().end, range.end);
        else
            merged.push_back(range);
    }
    return merged;
}

static bool IsAllZero(const uint8_t* data, size_t size)
{
    size_t i = 0;
    for (; i + sizeof(uint64_t) <= size; i += sizeof(uint64_t))
    {
        uint64_t value = 0;
        std::memcpy(&value, data + i, sizeof(value));
        if (value != 0)
            return false;
    }
    for (; i < size; ++i)
    {
        if (data[i] != 0)
            return false;
    }
    return true;
}

// Result codes shared with the Kotlin UI:
// 0 success, 1 invalid path, 2 guest memory unavailable, 3 no writable RAM,
// 4 file I/O failure, 5 different process/session, 6 corrupt/unsupported,
// 7 guest mapping changed, 8 snapshot exceeded safety cap.
static int Save(const fs::path& path)
{
    if (path.empty())
        return 1;

    auto* guest = static_cast<uint8_t*>(memory_getBase());
    if (!guest)
        return 2;

    const uintptr_t guestBase = reinterpret_cast<uintptr_t>(guest);
    const auto ranges = CollectGuestRamRanges(guestBase);
    if (ranges.empty())
        return 3;

    std::error_code ec;
    if (!path.parent_path().empty())
        fs::create_directories(path.parent_path(), ec);

    std::ofstream file(path, std::ios::binary | std::ios::trunc);
    if (!file.is_open())
        return 4;

    StateHeader header{};
    std::memcpy(header.magic, "WQSTATE", 7);
    header.version = kFormatVersion;
    header.pid = static_cast<uint32_t>(getpid());
    header.guestBase = static_cast<uint64_t>(guestBase);
    header.chunkSize = kChunkSize;
    file.write(reinterpret_cast<const char*>(&header), sizeof(header));
    if (!file.good())
        return 4;

    uint64_t storedBytes = 0;
    uint32_t chunkCount = 0;

    for (const auto& range : ranges)
    {
        uintptr_t cursor = range.begin;
        while (cursor < range.end)
        {
            const size_t size = static_cast<size_t>(std::min<uintptr_t>(
                static_cast<uintptr_t>(kChunkSize), range.end - cursor));
            const auto* data = reinterpret_cast<const uint8_t*>(cursor);
            const bool zero = IsAllZero(data, size);

            ChunkHeader chunk{};
            chunk.guestOffset = static_cast<uint64_t>(cursor - guestBase);
            chunk.size = static_cast<uint32_t>(size);
            chunk.flags = zero ? kChunkFlagZero : 0u;
            file.write(reinterpret_cast<const char*>(&chunk), sizeof(chunk));
            if (!file.good())
                return 4;

            if (!zero)
            {
                storedBytes += size;
                if (storedBytes > kMaxStoredBytes)
                {
                    file.close();
                    fs::remove(path, ec);
                    return 8;
                }
                file.write(reinterpret_cast<const char*>(data), static_cast<std::streamsize>(size));
                if (!file.good())
                    return 4;
            }

            ++chunkCount;
            cursor += size;
        }
    }

    header.chunkCount = chunkCount;
    header.storedBytes = storedBytes;
    file.seekp(0, std::ios::beg);
    file.write(reinterpret_cast<const char*>(&header), sizeof(header));
    file.flush();
    return file.good() ? 0 : 4;
}

static int Load(const fs::path& path)
{
    if (path.empty())
        return 1;

    auto* guest = static_cast<uint8_t*>(memory_getBase());
    if (!guest)
        return 2;
    const uintptr_t guestBase = reinterpret_cast<uintptr_t>(guest);

    std::ifstream file(path, std::ios::binary);
    if (!file.is_open())
        return 4;

    StateHeader header{};
    file.read(reinterpret_cast<char*>(&header), sizeof(header));
    if (!file.good() || std::memcmp(header.magic, "WQSTATE", 7) != 0 ||
        header.version != kFormatVersion || header.chunkSize != kChunkSize)
        return 6;

    // Test10 deliberately refuses cross-process loads. Host-side Cemu CPU/GPU
    // objects are not serialized yet, so restoring RAM in another session
    // would be unsafe and misleading.
    if (header.pid != static_cast<uint32_t>(getpid()) ||
        header.guestBase != static_cast<uint64_t>(guestBase))
        return 5;

    const auto maps = CollectWritableMappings();
    std::vector<uint8_t> buffer(kChunkSize);

    // Pass 1 validates the complete file and all target mappings BEFORE
    // touching emulated memory, preventing half-applied corrupt states.
    for (uint32_t i = 0; i < header.chunkCount; ++i)
    {
        ChunkHeader chunk{};
        file.read(reinterpret_cast<char*>(&chunk), sizeof(chunk));
        if (!file.good() || chunk.size == 0 || chunk.size > kChunkSize ||
            chunk.guestOffset >= kGuestSpaceSize ||
            chunk.guestOffset + chunk.size > kGuestSpaceSize)
            return 6;

        const uintptr_t begin = guestBase + static_cast<uintptr_t>(chunk.guestOffset);
        const uintptr_t end = begin + static_cast<uintptr_t>(chunk.size);
        if (!IsWritableRange(maps, begin, end))
            return 7;

        if ((chunk.flags & kChunkFlagZero) == 0)
        {
            file.seekg(static_cast<std::streamoff>(chunk.size), std::ios::cur);
            if (!file.good())
                return 6;
        }
    }

    // No unexpected trailing truncation/errors.
    if (!file.good() && !file.eof())
        return 6;

    file.clear();
    file.seekg(sizeof(StateHeader), std::ios::beg);

    // Pass 2 restores the guest RAM snapshot.
    for (uint32_t i = 0; i < header.chunkCount; ++i)
    {
        ChunkHeader chunk{};
        file.read(reinterpret_cast<char*>(&chunk), sizeof(chunk));
        if (!file.good())
            return 6;

        auto* target = reinterpret_cast<uint8_t*>(guestBase + static_cast<uintptr_t>(chunk.guestOffset));
        if ((chunk.flags & kChunkFlagZero) != 0)
        {
            std::memset(target, 0, chunk.size);
        }
        else
        {
            file.read(reinterpret_cast<char*>(buffer.data()), chunk.size);
            if (!file.good())
                return 6;
            std::memcpy(target, buffer.data(), chunk.size);
        }
    }

    return 0;
}
} // namespace WudroidQuickState
'''

native_cpp = native_cpp.replace(namespace_anchor, state_impl + '\n' + namespace_anchor, 1)

jni_append = r'''

extern "C" [[maybe_unused]] JNIEXPORT jint JNICALL
Java_info_cemu_cemu_nativeinterface_NativeEmulation_saveQuickState(
    JNIEnv* env, [[maybe_unused]] jclass clazz, jstring state_path)
{
    CafeSystem::PauseTitle();
    const fs::path path = JNIUtils::toString(env, state_path);
    return WudroidQuickState::Save(path);
}

extern "C" [[maybe_unused]] JNIEXPORT jint JNICALL
Java_info_cemu_cemu_nativeinterface_NativeEmulation_loadQuickState(
    JNIEnv* env, [[maybe_unused]] jclass clazz, jstring state_path)
{
    CafeSystem::PauseTitle();
    const fs::path path = JNIUtils::toString(env, state_path);
    return WudroidQuickState::Load(path);
}
'''

if 'Java_info_cemu_cemu_nativeinterface_NativeEmulation_saveQuickState' not in native_cpp:
    native_cpp = native_cpp.rstrip() + jni_append + '\n'

native_cpp_path.write_text(native_cpp)

# ---------------------------------------------------------------------------
# 3) EmulationScreen.kt: quick save/load actions in the REAL left in-game menu.
# ---------------------------------------------------------------------------
for imp in [
    'import kotlinx.coroutines.Dispatchers',
    'import kotlinx.coroutines.withContext',
]:
    if imp not in screen:
        screen = screen.replace('import kotlinx.coroutines.launch\n', 'import kotlinx.coroutines.launch\n' + imp + '\n', 1)

scope_anchor = '    val scope = rememberCoroutineScope()\n'
if scope_anchor not in screen:
    raise SystemExit('rememberCoroutineScope anchor missing')
if 'val wudroidQuickStateContext = LocalContext.current' not in screen:
    screen = screen.replace(
        scope_anchor,
        scope_anchor + '    val wudroidQuickStateContext = LocalContext.current // WUDROID_QUICKSTATE_ENGINE_TEST10\n',
        1,
    )

quick_cb_anchor = '''                        onQuickSettings = {
                            openQuickDrawer()
                        },
'''
if quick_cb_anchor not in screen:
    raise SystemExit('Quick Settings callback anchor missing')

quick_callbacks = r'''                        onQuickSettings = {
                            openQuickDrawer()
                        },
                        onQuickSave = {
                            scope.launch {
                                val statePath = wudroidQuickStateContext.cacheDir
                                    .resolve("wudroid_states/quick.wstate")
                                    .absolutePath
                                val result = withContext(Dispatchers.IO) {
                                    NativeEmulation.saveQuickState(statePath)
                                }
                                snackbarHostState.showSnackbar(
                                    when (result) {
                                        0 -> "Estado rápido salvo"
                                        2 -> "Memória do Wii U ainda não está disponível"
                                        3 -> "Nenhuma região de RAM do jogo foi encontrada"
                                        4 -> "Falha ao gravar o estado rápido"
                                        8 -> "Estado grande demais para o limite de segurança"
                                        else -> "Falha ao salvar estado (código $result)"
                                    }
                                )
                                if (result == 0) closeDrawer()
                            }
                        },
                        onQuickLoad = {
                            scope.launch {
                                val statePath = wudroidQuickStateContext.cacheDir
                                    .resolve("wudroid_states/quick.wstate")
                                    .absolutePath
                                val result = withContext(Dispatchers.IO) {
                                    NativeEmulation.loadQuickState(statePath)
                                }
                                snackbarHostState.showSnackbar(
                                    when (result) {
                                        0 -> "Estado rápido restaurado"
                                        4 -> "Nenhum estado rápido encontrado"
                                        5 -> "Este estado pertence a outra sessão do Wudroid"
                                        6 -> "Estado rápido inválido ou incompleto"
                                        7 -> "O mapa de memória mudou; carregamento cancelado"
                                        else -> "Falha ao carregar estado (código $result)"
                                    }
                                )
                                if (result == 0) closeDrawer()
                            }
                        },
'''
screen = screen.replace(quick_cb_anchor, quick_callbacks, 1)

param_anchor = '''    onPauseToggle: () -> Unit,
    onQuickSettings: () -> Unit,
    onQuit: () -> Unit,
) {
'''
if param_anchor not in screen:
    raise SystemExit('EmulationSideMenuContent parameter anchor missing')
screen = screen.replace(
    param_anchor,
    '''    onPauseToggle: () -> Unit,
    onQuickSettings: () -> Unit,
    onQuickSave: () -> Unit,
    onQuickLoad: () -> Unit,
    onQuit: () -> Unit,
) {
''',
    1,
)

# q patch translated Quick Settings -> Configurações rápidas. Insert the save
# section immediately after that button so it stays high in the main menu.
menu_anchor = '''    TextButtonItem(
        label = "Configurações rápidas",
        onClick = onQuickSettings,
    )
'''
if menu_anchor not in screen:
    # fallback for a source where translation occurs after this patch
    menu_anchor = '''    TextButtonItem(
        label = "Quick Settings",
        onClick = onQuickSettings,
    )
'''
if menu_anchor not in screen:
    raise SystemExit('Quick Settings menu item anchor missing')

save_menu = menu_anchor + r'''
    Text(
        text = "Save State",
        color = WudroidCyan,
        fontWeight = FontWeight.Bold,
        fontSize = 12.sp,
        modifier = Modifier.padding(start = 12.dp, top = 10.dp, bottom = 4.dp),
    )
    TextButtonItem(
        label = "Salvar rápido",
        onClick = onQuickSave,
    )
    TextButtonItem(
        label = "Carregar rápido",
        onClick = onQuickLoad,
    )
'''
screen = screen.replace(menu_anchor, save_menu, 1)

screen_path.write_text(screen)

# ---------------------------------------------------------------------------
# Verification: fail during Apply step instead of letting Gradle fail later.
# ---------------------------------------------------------------------------
checks = {
    screen_path: [
        marker,
        'label = "Salvar rápido"',
        'label = "Carregar rápido"',
        'NativeEmulation.saveQuickState(statePath)',
        'NativeEmulation.loadQuickState(statePath)',
        'withContext(Dispatchers.IO)',
    ],
    native_kt_path: [
        'external fun saveQuickState(path: String): Int',
        'external fun loadQuickState(path: String): Int',
    ],
    native_cpp_path: [
        'WudroidQuickState::Save(path)',
        'WudroidQuickState::Load(path)',
        'Java_info_cemu_cemu_nativeinterface_NativeEmulation_saveQuickState',
        'Java_info_cemu_cemu_nativeinterface_NativeEmulation_loadQuickState',
        'extern "C" void* memory_getBase();',
        '#include <filesystem>',
        'namespace fs = std::filesystem;',
    ],
}
for p, needles in checks.items():
    text = p.read_text()
    missing = [n for n in needles if n not in text]
    if missing:
        raise SystemExit(f'Verification failed for {p}: {missing}')

print('Wudroid Quick State Engine Test10 applied')
print('- real JNI save/load bridge added to NativeEmulation')
print('- same-session guest RAM snapshot container added')
print('- zero chunks encoded without storing payload bytes')
print('- PID + guest-base compatibility guard added')
print('- Save rápido / Carregar rápido added to real in-game menu')
print('- full CPU/GPU/audio serialization intentionally remains for later stages')
