#!/usr/bin/env python3
from pathlib import Path

path = Path("cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationScreen.kt")
if not path.exists():
    raise SystemExit("EmulationScreen.kt not found")

s = path.read_text()
marker = "WUDROID_SIDEBAR_THEME_TEST1"
if marker in s:
    print("Wudroid original sidebar theme already applied")
    raise SystemExit(0)

# Prove that this is the original in-game Cemu drawer the user showed.
required_original = [
    "ModalNavigationDrawer(",
    "ModalDrawerSheet {",
    "private fun EmulationSideMenuContent(",
    'label = tr("Enable motion")',
    'label = tr("Show input overlay")',
    'label = tr("Exit")',
]
missing = [x for x in required_original if x not in s]
if missing:
    raise SystemExit("Original Cemu in-game sidebar anchors missing: " + ", ".join(missing))

# Imports used only by the original drawer restyle.
imports = [
    "import androidx.compose.foundation.background",
    "import androidx.compose.foundation.shape.RoundedCornerShape",
    "import androidx.compose.material3.CheckboxDefaults",
    "import androidx.compose.ui.graphics.Color",
    "import androidx.compose.ui.text.font.FontWeight",
]
for imp in imports:
    if imp not in s:
        # Put Compose imports with the existing import block.
        anchor = "import androidx.compose.foundation.clickable\n"
        if imp.startswith("import androidx.compose.foundation") and anchor in s:
            s = s.replace(anchor, anchor + imp + "\n", 1)
        else:
            # Safe generic insertion immediately after package line.
            pkg = "package info.cemu.cemu.emulation\n"
            s = s.replace(pkg, pkg + "\n" + imp + "\n", 1)

# Wudroid palette. These constants live in the real Cemu EmulationScreen file.
constants = r'''
// WUDROID_SIDEBAR_THEME_TEST1
private val WudroidDrawerBackground = Color(0xFF08131C)
private val WudroidDrawerSurface = Color(0xFF0D1E2A)
private val WudroidDrawerSurfacePressed = Color(0xFF112B3A)
private val WudroidCyan = Color(0xFF00C7F2)
private val WudroidBlue = Color(0xFF0078D4)
private val WudroidDrawerText = Color(0xFFF8FBFF)
private val WudroidDrawerMuted = Color(0xFFA0AEC0)
private val WudroidDrawerOutline = Color(0xFF24485A)

'''
first_composable = s.find("@Composable")
if first_composable < 0:
    raise SystemExit("No @Composable found in EmulationScreen.kt")
s = s[:first_composable] + constants + s[first_composable:]

# Theme the actual ModalDrawerSheet from the original emulation screen.
s = s.replace(
    "        ModalDrawerSheet {",
    "        ModalDrawerSheet(\n"
    "            drawerContainerColor = WudroidDrawerBackground,\n"
    "            drawerContentColor = WudroidDrawerText,\n"
    "        ) {",
    1,
)

# Add a small Wudroid identity header INSIDE the original drawer.
menu_anchor = "                EmulationSideMenuContent("
if menu_anchor not in s:
    raise SystemExit("Original EmulationSideMenuContent call anchor missing")
header = r'''                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 10.dp, vertical = 12.dp),
                ) {
                    Text(
                        text = "WUDROID",
                        color = WudroidCyan,
                        fontSize = 20.sp,
                        fontWeight = FontWeight.Bold,
                    )
                    Text(
                        text = "Menu rápido",
                        color = WudroidDrawerMuted,
                        fontSize = 12.sp,
                    )
                }

'''
s = s.replace(menu_anchor, header + menu_anchor, 1)

# Replace only the two item renderers used by the ORIGINAL side menu.
check_start = s.find("@Composable\nprivate fun CheckboxItem(")
text_start = s.find("@Composable\nprivate fun TextButtonItem(", check_start)
surface_start = s.find("@Composable\nprivate fun EmulationSurfaces(", text_start)
if min(check_start, text_start, surface_start) < 0:
    raise SystemExit("Original sidebar item renderer anchors missing")

checkbox_fn = r'''@Composable
private fun CheckboxItem(
    label: String,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit,
    enabled: Boolean = true,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .alpha(if (enabled) 1f else 0.55f)
            .padding(vertical = 3.dp)
            .background(WudroidDrawerSurface, RoundedCornerShape(14.dp))
            .clickable(enabled) { onCheckedChange(!checked) }
            .padding(horizontal = 12.dp, vertical = 7.dp)
            .minimumInteractiveComponentSize(),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            text = label,
            modifier = Modifier
                .padding(end = 10.dp)
                .weight(1f),
            color = if (enabled) WudroidDrawerText else WudroidDrawerMuted,
            fontSize = 16.sp,
        )
        Checkbox(
            checked = checked,
            onCheckedChange = null,
            colors = CheckboxDefaults.colors(
                checkedColor = WudroidCyan,
                uncheckedColor = WudroidDrawerOutline,
                checkmarkColor = WudroidDrawerBackground,
            ),
        )
    }
}

'''

textbutton_fn = r'''@Composable
private fun TextButtonItem(
    label: String,
    onClick: () -> Unit,
    enabled: Boolean = true,
) {
    Text(
        text = label,
        color = if (enabled) WudroidDrawerText else WudroidDrawerMuted,
        modifier = Modifier
            .fillMaxWidth()
            .alpha(if (enabled) 1f else 0.55f)
            .padding(vertical = 3.dp)
            .background(WudroidDrawerSurface, RoundedCornerShape(14.dp))
            .clickable(enabled = enabled, onClick = onClick)
            .padding(horizontal = 12.dp, vertical = 8.dp)
            .heightIn(min = 48.dp)
            .wrapContentHeight(align = Alignment.CenterVertically),
        fontSize = 16.sp,
    )
}

'''

s = s[:check_start] + checkbox_fn + textbutton_fn + s[surface_start:]
path.write_text(s)

check = path.read_text()
verification = [
    marker,
    "drawerContainerColor = WudroidDrawerBackground",
    'text = "WUDROID"',
    "checkedColor = WudroidCyan",
    'label = tr("Enable motion")',
    'label = tr("Exit")',
]
missing = [x for x in verification if x not in check]
if missing:
    raise SystemExit("Wudroid original sidebar theme verification failed: " + ", ".join(missing))

print("Wudroid 0.1.1 Original Sidebar Theme Test1 applied")
print("- modified REAL Cemu EmulationScreen.kt")
print("- modified REAL ModalNavigationDrawer / ModalDrawerSheet")
print("- original menu actions preserved")
print("- Wudroid dark + cyan palette applied")
