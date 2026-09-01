#!/usr/bin/env python3
from pathlib import Path
import re

path = Path('cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationScreen.kt')
if not path.exists():
    raise SystemExit('EmulationScreen.kt not found')

s = path.read_text()
marker = 'WUDROID_EDITOR_POLISH_SAVEUI_TEST9'
if marker in s:
    print('Wudroid Test9 already applied')
    raise SystemExit(0)

if 'WUDROID_GAMEPAD_EDITOR_TEST8_INDIVIDUAL' not in s:
    raise SystemExit('Test8 BuildFix1 must be applied before Test9')

# ---------------------------------------------------------------------------
# Structural helpers. Do not depend on whichever composable happens to follow.
# ---------------------------------------------------------------------------
def find_function_region(text: str, function_name: str):
    match = re.search(r'(?m)^[ \t]*(?:private[ \t]+)?(?:override[ \t]+)?fun[ \t]+' + re.escape(function_name) + r'[ \t]*\(', text)
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
    in_string = False
    in_char = False
    escape = False
    line_comment = False
    block_comment = False
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
    in_string = False
    in_char = False
    escape = False
    line_comment = False
    block_comment = False
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


def find_call_close(text: str, call_name: str):
    start = text.find(call_name + '(')
    if start < 0:
        return None
    p = text.find('(', start)
    depth = 0
    i = p
    in_string = False
    escape = False
    line_comment = False
    block_comment = False
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
        if ch == '/' and nxt == '/': line_comment = True; i += 2; continue
        if ch == '/' and nxt == '*': block_comment = True; i += 2; continue
        if ch == '"': in_string = True; i += 1; continue
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth == 0:
                return start, i
        i += 1
    return None

# Imports for the compact editor animation and save-state UI shell.
imports = [
    'import androidx.compose.animation.core.animateFloatAsState',
    'import androidx.compose.foundation.layout.height',
    'import androidx.compose.foundation.layout.widthIn',
]
for imp in imports:
    if imp not in s:
        s = s.replace('package info.cemu.cemu.emulation\n', 'package info.cemu.cemu.emulation\n' + imp + '\n', 1)

# ---------------------------------------------------------------------------
# 1 + 2) Compact floating editor. While moving the SIZE slider the whole
# floating window fades smoothly so the selected button remains visible.
# ---------------------------------------------------------------------------
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
    // WUDROID_EDITOR_POLISH_SAVEUI_TEST9
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
                    .padding(top = 12.dp)
                    .fillMaxWidth(0.56f)
                    .widthIn(min = 310.dp, max = 470.dp)
                    .alpha(floatingPanelAlpha)
                    .background(WudroidDrawerSurface, RoundedCornerShape(24.dp))
                    .padding(horizontal = 16.dp, vertical = 10.dp),
            ) {
                Text(
                    text = "Editar controles",
                    color = WudroidCyan,
                    fontSize = 17.sp,
                    fontWeight = FontWeight.Bold,
                )

                Row(
                    modifier = Modifier.fillMaxWidth().padding(top = 5.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text("Transparência", color = WudroidDrawerText, fontSize = 13.sp, modifier = Modifier.weight(1f))
                    Text("${((alpha / 255f) * 100f).toInt()}%", color = WudroidCyan, fontSize = 12.sp, fontWeight = FontWeight.Bold)
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
                    Text("Tamanho", color = WudroidDrawerText, fontSize = 13.sp, modifier = Modifier.weight(1f))
                    Text(
                        if (hasSelection) "${sizePercent.toInt()}%" else "Selecione um botão",
                        color = if (hasSelection) WudroidCyan else WudroidDrawerMuted,
                        fontSize = 12.sp,
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
                        fontSize = 11.sp,
                        modifier = Modifier.padding(bottom = 2.dp),
                    )
                }

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(10.dp, Alignment.End),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    TextButton(onClick = onResetClick) {
                        Text("Reset", color = WudroidDrawerText, fontSize = 12.sp)
                    }
                    Button(onClick = onFinishClick) {
                        Text("Concluir", fontSize = 12.sp)
                    }
                }

                Box(modifier = Modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
                    TextButton(onClick = { onCollapseChange(true) }) {
                        Text("▲", color = WudroidCyan, fontSize = 17.sp, fontWeight = FontWeight.Bold)
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
    raise SystemExit('Test9 could not replace EditInputsLayout')

# ---------------------------------------------------------------------------
# 3) Translate the visible names in the RIGHT secondary menu.
# Internal native values stay unchanged; only what the user sees is translated.
# ---------------------------------------------------------------------------
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

# Translate values shown by GPU/scaling/VSync without changing native enum values.
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

# ---------------------------------------------------------------------------
# 4) Game + Save State UI shell.
# IMPORTANT: Cemu currently has no emulator-state serialization backend.
# Do not fake a save/load. The menu + 6-slot layout are added now and clearly
# shown as unavailable until a real native backend exists.
# ---------------------------------------------------------------------------
state_anchor = '    var wudroidEditorPanelCollapsed by rememberSaveable { mutableStateOf(false) }\n'
if state_anchor not in s:
    raise SystemExit('Test9 state anchor missing')
s = s.replace(
    state_anchor,
    state_anchor +
    '    var showWudroidGameSaveDialog by rememberSaveable { mutableStateOf(false) } // WUDROID_EDITOR_POLISH_SAVEUI_TEST9\n'
    '    var showWudroidSaveSlotsDialog by rememberSaveable { mutableStateOf(false) }\n',
    1,
)

# Add callback to the existing EmulationSideMenuContent invocation structurally.
call = find_call_close(s, 'EmulationSideMenuContent')
if call is None:
    raise SystemExit('Test9 EmulationSideMenuContent call missing')
call_start, call_close = call
call_text = s[call_start:call_close]
if 'onGameAndSave' not in call_text:
    s = s[:call_close] + '''                        onGameAndSave = {
                            showWudroidGameSaveDialog = true
                            closeDrawer()
                        },
''' + s[call_close:]

new_main_menu = r'''@Composable
private fun EmulationSideMenuContent(
    sideMenuState: SideMenuState,
    updateState: (SideMenuState) -> Unit,
    onShowEmulatedUSBDevices: () -> Unit,
    onEditInputOverlay: () -> Unit,
    onResetInputOverlay: () -> Unit,
    isPaused: Boolean,
    onPauseToggle: () -> Unit,
    onQuickSettings: () -> Unit,
    onGameAndSave: () -> Unit,
    onQuit: () -> Unit,
) {
    TextButtonItem(
        label = if (isPaused) "Retomar emulação" else "Pausar emulação",
        onClick = onPauseToggle,
    )
    TextButtonItem(
        label = if (sideMenuState.isInputOverlayVisible) "Ocultar controle" else "Mostrar controle",
        onClick = { updateState(sideMenuState.copy(isInputOverlayVisible = !sideMenuState.isInputOverlayVisible)) },
    )
    TextButtonItem(
        label = "Configurações rápidas",
        onClick = onQuickSettings,
    )
    TextButtonItem(
        label = "Jogo e Save State",
        onClick = onGameAndSave,
    )
    TextButtonItem(
        label = "Controles",
        enabled = sideMenuState.isInputOverlayVisible,
        onClick = onEditInputOverlay,
    )
    TextButtonItem(
        label = tr("Emulated USB Devices"),
        onClick = onShowEmulatedUSBDevices,
    )

    Text(
        text = "Recursos Wii U",
        color = WudroidCyan,
        fontWeight = FontWeight.Bold,
        fontSize = 12.sp,
        modifier = Modifier.padding(start = 12.dp, top = 12.dp, bottom = 4.dp),
    )
    CheckboxItem(
        label = tr("Enable motion"),
        checked = sideMenuState.isMotionEnabled,
        onCheckedChange = { updateState(sideMenuState.copy(isMotionEnabled = it)) },
    )
    CheckboxItem(
        label = tr("Replace TV with PAD"),
        checked = sideMenuState.isTVReplacedWithPad,
        onCheckedChange = { updateState(sideMenuState.copy(isTVReplacedWithPad = it)) },
    )
    CheckboxItem(
        label = tr("Show PAD"),
        checked = sideMenuState.isPadVisible,
        onCheckedChange = { updateState(sideMenuState.copy(isPadVisible = it)) },
    )
    TextButtonItem(
        label = tr("Reset input overlay"),
        enabled = sideMenuState.isInputOverlayVisible,
        onClick = onResetInputOverlay,
    )

    HorizontalDivider(color = WudroidDrawerOutline, modifier = Modifier.padding(vertical = 8.dp))
    TextButtonItem(label = "Sair da emulação", onClick = onQuit)
}
'''
s, count = replace_function(s, 'EmulationSideMenuContent', new_main_menu)
if count != 1:
    raise SystemExit('Test9 could not replace EmulationSideMenuContent')

# Dialog invocations live with the other in-emulation dialogs.
quit_anchor = '    if (showQuitConfirmationDialog) {\n'
if quit_anchor not in s:
    raise SystemExit('Test9 quit dialog invocation anchor missing')
dialog_calls = r'''    if (showWudroidGameSaveDialog) {
        WudroidGameSaveDialog(
            onDismiss = { showWudroidGameSaveDialog = false },
            onOpenSlots = {
                showWudroidGameSaveDialog = false
                showWudroidSaveSlotsDialog = true
            },
        )
    }

    if (showWudroidSaveSlotsDialog) {
        WudroidSaveSlotsDialog(
            onDismiss = { showWudroidSaveSlotsDialog = false },
        )
    }

'''
s = s.replace(quit_anchor, dialog_calls + quit_anchor, 1)

# New composables are inserted before the existing quit confirmation function.
quit_fn_pos = s.find('@Composable\nprivate fun EmulationQuitConfirmationDialog(')
if quit_fn_pos < 0:
    raise SystemExit('Test9 quit confirmation function anchor missing')

save_ui = r'''@Composable
private fun WudroidGameSaveDialog(
    onDismiss: () -> Unit,
    onOpenSlots: () -> Unit,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = WudroidDrawerSurface,
        shape = RoundedCornerShape(24.dp),
        title = {
            Text("Jogo e Save State", color = WudroidCyan, fontWeight = FontWeight.Bold)
        },
        text = {
            Column(modifier = Modifier.widthIn(min = 330.dp, max = 460.dp)) {
                WudroidDialogAction(
                    title = "Carregar jogo",
                    subtitle = "A troca segura de jogo ainda não é exposta pelo core durante a execução.",
                    enabled = false,
                    onClick = {},
                )
                WudroidDialogAction(
                    title = "Save State rápido",
                    subtitle = "Aguardando um backend real de Save State no core do Cemu.",
                    enabled = false,
                    onClick = {},
                )
                WudroidDialogAction(
                    title = "Save States",
                    subtitle = "Visualizar os 6 slots preparados no Wudroid.",
                    enabled = true,
                    onClick = onOpenSlots,
                )
                Text(
                    text = "O Wudroid não cria saves falsos: salvar/carregar o estado exato será ativado somente quando houver serialização real do estado do Cemu.",
                    color = WudroidDrawerMuted,
                    fontSize = 11.sp,
                    modifier = Modifier.padding(top = 8.dp),
                )
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) { Text("Fechar", color = WudroidCyan) }
        },
    )
}

@Composable
private fun WudroidDialogAction(
    title: String,
    subtitle: String,
    enabled: Boolean,
    onClick: () -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .alpha(if (enabled) 1f else 0.50f)
            .padding(vertical = 4.dp)
            .background(WudroidDrawerBackground, RoundedCornerShape(14.dp))
            .clickable(enabled = enabled, onClick = onClick)
            .padding(horizontal = 12.dp, vertical = 9.dp),
    ) {
        Text(title, color = WudroidDrawerText, fontWeight = FontWeight.Bold, fontSize = 14.sp)
        Text(subtitle, color = WudroidDrawerMuted, fontSize = 10.sp)
    }
}

@Composable
private fun WudroidSaveSlotsDialog(onDismiss: () -> Unit) {
    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = WudroidDrawerSurface,
        shape = RoundedCornerShape(24.dp),
        title = {
            Text("Save States", color = WudroidCyan, fontWeight = FontWeight.Bold)
        },
        text = {
            Column(modifier = Modifier.widthIn(min = 430.dp, max = 560.dp)) {
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    WudroidSaveSlotCard(1, Modifier.weight(1f))
                    WudroidSaveSlotCard(2, Modifier.weight(1f))
                    WudroidSaveSlotCard(3, Modifier.weight(1f))
                }
                Row(
                    modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    WudroidSaveSlotCard(4, Modifier.weight(1f))
                    WudroidSaveSlotCard(5, Modifier.weight(1f))
                    WudroidSaveSlotCard(6, Modifier.weight(1f))
                }
                Text(
                    text = "6 slots preparados • toque/carregar e segurar/apagar serão ligados ao backend real de Save State.",
                    color = WudroidDrawerMuted,
                    fontSize = 10.sp,
                    modifier = Modifier.padding(top = 8.dp),
                )
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) { Text("Fechar", color = WudroidCyan) }
        },
    )
}

@Composable
private fun WudroidSaveSlotCard(slot: Int, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .height(94.dp)
            .background(WudroidDrawerBackground, RoundedCornerShape(14.dp))
            .padding(10.dp),
        verticalArrangement = Arrangement.SpaceBetween,
    ) {
        Text("Slot $slot", color = WudroidCyan, fontWeight = FontWeight.Bold, fontSize = 12.sp)
        Text("Vazio", color = WudroidDrawerText, fontSize = 13.sp)
        Text("--:--  •  --/--/----", color = WudroidDrawerMuted, fontSize = 9.sp)
    }
}

'''
s = s[:quit_fn_pos] + save_ui + s[quit_fn_pos:]

path.write_text(s)

check = path.read_text()
required = [
    marker,
    'text = "Editar controles"',
    'targetValue = if (isSizeDragging) 0.22f else 0.98f',
    'label = "Configurações rápidas"',
    'title = "Modo da GPU"',
    'title = "Compilação assíncrona de shaders"',
    'label = "Jogo e Save State"',
    'private fun WudroidGameSaveDialog(',
    'private fun WudroidSaveSlotsDialog(',
    'WudroidSaveSlotCard(6',
]
missing = [x for x in required if x not in check]
if missing:
    raise SystemExit('Test9 verification failed: ' + ', '.join(missing))

print('Wudroid 0.1.1 Test9 applied')
print('- gamepad editor is smaller/floating')
print('- editor fades while individual SIZE slider is dragged')
print('- right Quick Settings visible labels translated to PT-BR')
print('- Jogo e Save State menu + 6-slot UI shell added')
print('- no fake save/load: Cemu state serialization backend is not available')
