from pathlib import Path

app_file = Path(
    "cemu-engine/src/android/app/src/main/java/info/cemu/cemu/CemuApplication.kt"
)
s = app_file.read_text()

import_line = "import info.cemu.cemu.graphicpacks.WudroidBundledGraphicPacks\n"
if import_line not in s:
    package_anchor = "package info.cemu.cemu\n\n"
    if package_anchor not in s:
        raise SystemExit("CemuApplication package anchor not found")
    s = s.replace(package_anchor, package_anchor + import_line, 1)

call = "        WudroidBundledGraphicPacks.install(this)\n"
if call not in s:
    anchor = "        initializeSwkbd()\n        refreshGraphicPacks()"
    replacement = (
        "        initializeSwkbd()\n"
        "        // Wudroid compatibility packs must exist before GraphicPack2::LoadAll().\n"
        "        WudroidBundledGraphicPacks.install(this)\n"
        "        refreshGraphicPacks()"
    )
    if anchor not in s:
        raise SystemExit("CemuApplication graphic-pack initialization anchor not found")
    s = s.replace(anchor, replacement, 1)

app_file.write_text(s)

check = app_file.read_text()
if "WudroidBundledGraphicPacks.install(this)" not in check:
    raise SystemExit("Wudroid bundled graphic-pack hook failed")

print("Wudroid bundled graphic-pack hook applied")
