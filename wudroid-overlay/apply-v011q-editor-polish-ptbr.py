#!/usr/bin/env python3
from pathlib import Path
import re

path = Path('cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationScreen.kt')
if not path.exists():
    raise SystemExit('EmulationScreen.kt not found')

s = path.read_text()
marker = 'WUDROID_EDITOR_POLISH_PTBR_TEST9_BUILDFIX1'
if marker in s:
    print('Wudroid editor polish PT-BR Test9 BuildFix1 already applied')
    raise SystemExit(0)

if 'WUDROID_GAMEPAD_EDITOR_TEST8_INDIVIDUAL' not in s:
    raise SystemExit('Test8 BuildFix1 must be applied before this patch')

# Structural Kotlin function replacement: walk the full parameter list before
# looking for the function body, so default lambdas do not confuse the parser.
def find_function_region(text: str, function_name: str):
    match = re.search(
        r'(?m)^[ \t]*(?:private[ \t]+)?(?:override[ \t]+)?fun[ \t]+'
        + re.escape(function_name) + r'[ \t]*\(', text
    )
    if not match:
        return None

    start = match.start()
    scan = text.rfind('\n', 0, start) + 1
    while scan > 0:
        prev_end = scan - 1
        prev_start = text.rfind('\n', 0, prev_end) + 1
        prev_line = text[prev_start:prev_end].strip()
        if prev_line.startswith('@'):
            start = prev_start
            scan = prev_start
            continue
        if prev_line == '':
            scan = prev_start
            continue
        break

    paren = text.find('(', match.start(), match.end())
    if paren < 0:
        return None

    pdepth = 0
    i = paren
    in_string = in_char = escape = line_comment = block_comment = False
    signature_end = None
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ''
        if line_comment:
            if ch == '\n': line_comment = False
            i += 1; continue
        if block_comment:
            if ch == '*' and nxt == '/': block_comment = False; i += 2
            else: i += 1
            continue
        if in_string:
            if escape: escape = False
            elif ch == '\\': escape = True
            elif ch == '"': in_string = False
            i += 1; continue
        if in_char:
            if escape: escape = False
            elif ch == '\\': escape = True
            elif ch == "'": in_char = False
            i += 1; continue
        if ch == '/' and nxt == '/': line_comment = True; i += 2; continue
        if ch == '/' and nxt == '*': block_comment = True; i += 2; continue
        if ch == '"': in_string = True; i += 1; continue
        if ch == "'": in_char = True; i += 1; continue
        if ch == '(':
            pdepth += 1
        elif ch == ')':
            pdepth -= 1
            if pdepth == 0:
                signature_end = i + 1
                break
        i += 1
    if signature_end is None:
        return None

    brace = text.find('{', signature_end)
    if brace < 0:
        return None

    depth = 0
    i = brace
    in_string = in_char = escape = line_comment = block_comment = False
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ''
        if line_comment:
            if ch == '\n': line_comment = False
            i += 1; continue
        if block_comment:
            if ch == '*' and nxt == '/': block_comment = False; i += 2
            else: i += 1
            continue
        if in_string:
            if escape: escape = False
            elif ch == '\\': escape = True
            elif ch == '"': in_string = False
            i += 1; continue
        if in_char:
            if escape: escape = False
            elif ch == '\\': escape = True
            elif ch == "'": in_char = False
            i += 1; continue
        if ch == '/' and nxt == '/': line_comment = True; i += 2; continue
        if ch == '/' and nxt == '*': block_comment = True; i += 2; continue
        if ch == '"': in_string = True; i += 1; continue
        if ch == "'": in_char = True; i += 1; continue
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                if end < len(text) and text[end] == '\n': end += 1
                return start, end
        i += 1
    return None


def replace_function(text: str, function_name: str, replacement: str):
    region = find_function_region(text, function_name)
    if region is None:
        return text, 0
    start, end = region
    return text[:start] + replacement + text[end:], 1

# Only imports needed by the compact/fading editor. No Save State UI and no
# Modifier.height import are introduced in this build fix.
for imp in [
    'import androidx.compose.animation.core.animateFloatAsState',
    'import androidx.compose.foundation.layout.widthIn',
]:
    if imp not in s:
        s = s.replace('package info.cemu.cemu.emulation\n', 'package info.cemu.cemu.emulation\n' + imp + '\n', 1)

new_editor_fn = r'''@Composable
private fun EditInputsLayout(
    alpha: Float,
    sizePercent: Float,
    hasSelection: Boolean,
    isCollapsed: Boolean,
    onAlphaChange: (Float) -> Unit,
    onSizeChange: (Float) -> Unit,
    onCollapseChange: (Boolean) -> Unit,
    onResetClick: () -> Unit,
    onFinishClick: () -> Unit,
) {
    // WUDROID_EDITOR_POLISH_PTBR_TEST9_BUILDFIX1
    var isSizeDragging by remember { mutableStateOf(false) }
    val floatingPanelAlpha by animateFloatAsState(
        targetValue = if (isSizeDragging) 0.22f else 0.98f,
        animationSpec = tween(durationMillis = 150),
        label = "WudroidEditorPanelAlpha",
    )

    Box(modifier = Modifier.fillMaxSize()) {
        AnimatedVisibility(
            visible = !isCollapsed,
            modifier = Modifier.align(Alignment.TopCenter),
            enter = slideInVertically(
                animationSpec = tween(durationMillis = 230),
                initialOffsetY = { -it / 2 },
            ) + fadeIn(animationSpec = tween(180)),
            exit = slideOutVertically(
                animationSpec = tween(durationMillis = 230),
                targetOffsetY = { -it },
            ) + fadeOut(animationSpec = tween(150)),
        ) {
            Column(
                modifier = Modifier
                    .padding(top = 10.dp)
                    .fillMaxWidth(0.54f)
                    .widthIn(min = 300.dp, max = 450.dp)
                    .alpha(floatingPanelAlpha)
                    .background(WudroidDrawerSurface, RoundedCornerShape(22.dp))
                    .padding(horizontal = 14.dp, vertical = 8.dp),
            ) {
                Text(
                    text = "Editar controles",
                    color = WudroidCyan,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold,
                )

                Row(
                    modifier = Modifier.fillMaxWidth().padding(top = 3.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text("Transparência", color = WudroidDrawerText, fontSize = 12.sp, modifier = Modifier.weight(1f))
                    Text("${((alpha / 255f) * 100f).toInt()}%", color = WudroidCyan, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                }
                Slider(
                    value = alpha,
                    onValueChange = { onAlphaChange(it.coerceIn(0f, 255f)) },
                    valueRange = 0f..255f,
                    colors = SliderDefaults.colors(
                        thumbColor = WudroidCyan,
                        activeTrackColor = WudroidCyan,
                        inactiveTrackColor = WudroidDrawerOutline,
                    ),
                )

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text("Tamanho", color = WudroidDrawerText, fontSize = 12.sp, modifier = Modifier.weight(1f))
                    Text(
                        if (hasSelection) "${sizePercent.toInt()}%" else "Selecione um botão",
                        color = if (hasSelection) WudroidCyan else WudroidDrawerMuted,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                    )
                }
                Slider(
                    value = sizePercent,
                    onValueChange = {
                        isSizeDragging = true
                        onSizeChange(it.coerceIn(25f, 200f))
                    },
                    onValueChangeFinished = { isSizeDragging = false },
                    valueRange = 25f..200f,
                    enabled = hasSelection,
                    colors = SliderDefaults.colors(
                        thumbColor = WudroidCyan,
                        activeTrackColor = WudroidCyan,
                        inactiveTrackColor = WudroidDrawerOutline,
                        disabledThumbColor = WudroidDrawerOutline,
                        disabledActiveTrackColor = WudroidDrawerOutline,
                        disabledInactiveTrackColor = WudroidDrawerOutline,
                    ),
                )

                if (!hasSelection) {
                    Text(
                        text = "Toque no botão que deseja redimensionar.",
                        color = WudroidDrawerMuted,
                        fontSize = 10.sp,
                    )
                }

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp, Alignment.End),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    TextButton(onClick = onResetClick) {
                        Text("Reset", color = WudroidDrawerText, fontSize = 11.sp)
                    }
                    Button(onClick = onFinishClick) {
                        Text("Concluir", fontSize = 11.sp)
                    }
                }

                Box(modifier = Modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
                    TextButton(onClick = { onCollapseChange(true) }) {
                        Text("▲", color = WudroidCyan, fontSize = 16.sp, fontWeight = FontWeight.Bold)
                    }
                }
            }
        }

        AnimatedVisibility(
            visible = isCollapsed,
            modifier = Modifier.align(Alignment.TopCenter),
            enter = slideInVertically(animationSpec = tween(210), initialOffsetY = { -it }) + fadeIn(tween(160)),
            exit = slideOutVertically(animationSpec = tween(180), targetOffsetY = { -it }) + fadeOut(tween(120)),
        ) {
            TextButton(
                onClick = { onCollapseChange(false) },
                modifier = Modifier
                    .padding(top = 4.dp)
                    .background(WudroidDrawerSurface, RoundedCornerShape(18.dp)),
            ) {
                Text("▼", color = WudroidCyan, fontSize = 18.sp, fontWeight = FontWeight.Bold)
            }
        }
    }
}
'''

s, count = replace_function(s, 'EditInputsLayout', new_editor_fn)
if count != 1:
    raise SystemExit('Could not replace EditInputsLayout structurally')

# Translate the visible text in the right-side Quick Settings menu only.
translations = {
    'label = "Quick Settings"': 'label = "Configurações rápidas"',
    'text = "Quick Settings"': 'text = "Configurações rápidas"',
    'title = "Turbo speed"': 'title = "Velocidade turbo"',
    'title = "Slow speed"': 'title = "Velocidade lenta"',
    'title = "GPU Mode"': 'title = "Modo da GPU"',
    'subtitle = "Fast / Balanced / Accurate"': 'subtitle = "Rápido / Equilibrado / Preciso"',
    'title = "Filtro de Adaptação da Janela"': 'title = "Filtro de adaptação da janela"',
    'title = "Método de Anti-aliasing"': 'title = "Método de antisserrilhamento"',
    'title = "Async shader compile"': 'title = "Compilação assíncrona de shaders"',
    'title = "Accurate barriers"': 'title = "Barreiras precisas"',
}
for old, new in translations.items():
    s = s.replace(old, new)

s = s.replace(
    '            value = gpuModeLabel(),\n',
    '            value = when (gpuModeLabel()) { "Fast" -> "Rápido"; "Balanced" -> "Equilibrado"; else -> "Preciso" },\n',
    1,
)
s = s.replace('3 -> "Nearest Neighbor"', '3 -> "Vizinho mais próximo"', 1)
s = s.replace('1 -> "Bicubic"', '1 -> "Bicúbico"', 1)
s = s.replace('2 -> "Bicubic Hermite"', '2 -> "Bicúbico Hermite"', 1)
s = s.replace(
    'value = when (vsync) { 0 -> "Off"; 2 -> "Triple"; else -> "Double" },',
    'value = when (vsync) { 0 -> "Desligado"; 2 -> "Triplo"; else -> "Duplo" },',
    1,
)

path.write_text(s)

check = path.read_text()
required = [
    marker,
    'targetValue = if (isSizeDragging) 0.22f else 0.98f',
    '.widthIn(min = 300.dp, max = 450.dp)',
    'label = "Configurações rápidas"',
    'title = "Modo da GPU"',
]
missing = [x for x in required if x not in check]
if missing:
    raise SystemExit('Verification failed: ' + ', '.join(missing))

# Hard safety check for the exact broken Test9 feature: this patch must not
# introduce the Save State shell or the .height(94.dp) call that failed Kotlin.
for forbidden in ['WudroidGameSaveDialog', 'WudroidSaveSlotsDialog', '.height(94.dp)']:
    if forbidden in check:
        raise SystemExit('Unexpected removed Test9 code found: ' + forbidden)

print('Wudroid Test9 BuildFix1 applied')
print('- compact floating editor')
print('- editor fades while SIZE is being adjusted')
print('- right-side menu labels translated to PT-BR')
print('- Save State UI intentionally NOT included in this build')
