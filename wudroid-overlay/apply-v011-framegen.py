#!/usr/bin/env python3
from pathlib import Path

path = Path("cemu-engine/src/android/app/src/main/java/info/cemu/cemu/MainActivity.kt")
s = path.read_text()

# Put Frame Generation in Advanced Settings right after the graphics panel.
anchor = '        WudroidGraphicsSettingsPanel()\n'
if "WudroidFrameGenerationPanel()" not in s:
    if anchor not in s:
        raise SystemExit("Advanced settings graphics panel anchor not found")
    s = s.replace(
        anchor,
        anchor + "        WudroidFrameGenerationPanel()\n",
        1,
    )

# 0.1.1 identity.
s = s.replace(
    '"Wudroid 0.1.0 • frontend independente"',
    '"Wudroid 0.1.1 • frontend independente"'
)
s = s.replace('InfoRow("Wudroid", "0.1.0")', 'InfoRow("Wudroid", "0.1.1")')
s = s.replace('Text("0.1.0", color = WBlue', 'Text("0.1.1", color = WBlue')

path.write_text(s)
print("Wudroid 0.1.1 FrameGen Foundation UI applied")
