#!/usr/bin/env python3
from pathlib import Path

path = Path("cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationScreen.kt")
if not path.exists():
    raise SystemExit("EmulationScreen.kt not found")

s = path.read_text()
marker = "WUDROID_LAYOUT_NAME_TEST14"

if marker in s:
    print("Wudroid Layout Name Test14 already applied")
    raise SystemExit(0)

# This patch runs after the existing sidebar/editor patches. Keep the
# visibility toggle (Mostrar/Ocultar controle) unchanged; only rename the
# menu entry that opens the touch-layout editor and the editor title itself.
sidebar_old = '        label = "Controles",\n        enabled = sideMenuState.isInputOverlayVisible,\n        onClick = onEditInputOverlay,\n'
sidebar_new = '        label = "Editar layout", // WUDROID_LAYOUT_NAME_TEST14\n        enabled = sideMenuState.isInputOverlayVisible,\n        onClick = onEditInputOverlay,\n'

if sidebar_old not in s:
    raise SystemExit('Layout Test14: sidebar "Controles" entry anchor missing')
s = s.replace(sidebar_old, sidebar_new, 1)

editor_old = '                    text = "Editar controles",\n'
editor_new = '                    text = "Editar layout", // WUDROID_LAYOUT_NAME_TEST14\n'

if editor_old not in s:
    raise SystemExit('Layout Test14: editor title "Editar controles" anchor missing')
s = s.replace(editor_old, editor_new, 1)

path.write_text(s)

check = path.read_text()
if 'label = "Editar layout"' not in check:
    raise SystemExit("Layout Test14 verification failed: sidebar label")
if 'text = "Editar layout"' not in check:
    raise SystemExit("Layout Test14 verification failed: editor title")
if 'label = "Controles"' in check:
    raise SystemExit('Layout Test14 verification failed: stale sidebar "Controles" entry')

print("Wudroid 0.1.1 Layout Test14 applied")
print('- sidebar editor entry: "Controles" -> "Editar layout"')
print('- editor panel title: "Editar controles" -> "Editar layout"')
print('- Mostrar/Ocultar controle remains unchanged')
