#!/usr/bin/env python3
from pathlib import Path

path = Path("cemu-engine/src/android/app/src/main/java/info/cemu/cemu/MainActivity.kt")
s = path.read_text()

s = s.replace(
    '"Wudroid 0.1.0 • frontend independente"',
    '"Wudroid 0.1.1 • frontend independente"'
)
s = s.replace('InfoRow("Wudroid", "0.1.0")', 'InfoRow("Wudroid", "0.1.1")')
s = s.replace('Text("0.1.0", color = WBlue', 'Text("0.1.1", color = WBlue')

path.write_text(s)
print("Wudroid 0.1.1 Frame Generation UI applied")
