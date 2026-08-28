#!/usr/bin/env python3
from pathlib import Path
import re

path = Path("cemu-engine/src/android/app/src/main/java/info/cemu/cemu/MainActivity.kt")
s = path.read_text()

needle = "        WindowCompat.setDecorFitsSystemWindows(window, false)\n"
insert = needle + "        try { applyWudroidTouchLayoutV1(this) } catch (_: Throwable) {}\n"
if "applyWudroidTouchLayoutV1(this)" not in s:
    if needle not in s:
        raise SystemExit("Could not find MainActivity startup insertion point")
    s = s.replace(needle, insert, 1)

s = s.replace("overlay.alpha < 150", "overlay.alpha < 96")
s = s.replace("maxOf(it.alpha, 150)", "maxOf(it.alpha, 96)")
s = s.replace("maxOf(current.alpha, 150)", "maxOf(current.alpha, 96)")

advanced_marker = '    ScreenScaffold("Configurações avançadas", onBack) {\n'
if "WudroidGraphicsSettingsPanel()" not in s:
    if advanced_marker not in s:
        raise SystemExit("Could not find AdvancedSettingsScreen")
    s = s.replace(
        advanced_marker,
        advanced_marker + "        WudroidGraphicsSettingsPanel()\n",
        1
    )

s = re.sub(
    r'\n\s*var vsync by remember \{ mutableIntStateOf\(safeInt \{ NativeSettings\.getVsyncMode\(\) \}\) \}\n',
    '\n',
    s,
    count=1
)

s = re.sub(
    r'\n\s*SectionLabel\("VSync"\)\n\s*ChoiceButtons\(\n'
    r'\s*choices = listOf\(\n'
    r'\s*NativeSettings\.VSyncMode\.OFF to "Desligado",\n'
    r'\s*NativeSettings\.VSyncMode\.DOUBLE_BUFFERING to "Duplo",\n'
    r'\s*NativeSettings\.VSyncMode\.TRIPLE_BUFFERING to "Triplo"\n'
    r'\s*\),\n'
    r'\s*selected = vsync\n'
    r'\s*\) \{\n'
    r'\s*vsync = it\n'
    r'\s*safeRun \{ NativeSettings\.setVsyncMode\(it\); NativeSettings\.saveSettings\(\) \}\n'
    r'\s*\}\n',
    '\n',
    s,
    count=1
)

reset_marker = '        Text("${alpha.roundToInt()}/255", color = WMuted, fontSize = 12.sp)\n'
if "Restaurar layout Wudroid" not in s:
    if reset_marker not in s:
        raise SystemExit("Could not find Controls alpha label insertion point")
    reset_block = reset_marker + '''        Spacer(Modifier.height(8.dp))
        SettingsEntry(
            WIcon.Controller,
            "Restaurar layout Wudroid",
            "Reposiciona os botões para o preset novo e esconde Home/microfone",
        ) {
            overlaySettings = resetWudroidTouchLayout()
            alpha = overlaySettings.alpha.toFloat()
        }
'''
    s = s.replace(reset_marker, reset_block, 1)

path.write_text(s)
print("Wudroid graphics/touch UI patch applied")
