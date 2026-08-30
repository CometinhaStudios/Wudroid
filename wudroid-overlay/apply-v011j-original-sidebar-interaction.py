#!/usr/bin/env python3
from pathlib import Path

path = Path("cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationScreen.kt")
if not path.exists():
    raise SystemExit("EmulationScreen.kt not found")

s = path.read_text()
marker = "WUDROID_SIDEBAR_INTERACTION_TEST2"
if marker in s:
    print("Wudroid original sidebar interaction Test2 already applied")
    raise SystemExit(0)

if "WUDROID_SIDEBAR_THEME_TEST1" not in s:
    raise SystemExit("Wudroid sidebar Theme Test1 must be applied before Interaction Test2")

# 1) Extra state for the clickable test function.
state_anchor = "    var showQuitConfirmationDialog by remember { mutableStateOf(false) }\n"
if state_anchor not in s:
    raise SystemExit("Quit-dialog state anchor missing")
s = s.replace(
    state_anchor,
    state_anchor + "    var showWudroidTestDialog by remember { mutableStateOf(false) } // WUDROID_SIDEBAR_INTERACTION_TEST2\n",
    1,
)

# 2) Back button no longer opens/toggles the drawer.
#    - drawer open: Back closes it
#    - drawer closed: Back asks for exit confirmation
old_back = '''    BackHandler {
        if (drawerState.isAnimationRunning) {
            return@BackHandler
        }

        scope.launch {
            toggleMenu()
        }
    }
'''
new_back = '''    BackHandler {
        if (drawerState.isAnimationRunning) {
            return@BackHandler
        }

        if (drawerState.isOpen) {
            closeDrawer()
        } else {
            showQuitConfirmationDialog = true
        }
    }
'''
if old_back not in s:
    raise SystemExit("Original BackHandler menu-toggle anchor missing")
s = s.replace(old_back, new_back, 1)

# 3) Let Material3's real drawer handle swipe gestures while closed and open.
old_gesture = "        gesturesEnabled = drawerState.isOpen,\n"
if old_gesture not in s:
    raise SystemExit("ModalNavigationDrawer gesturesEnabled anchor missing")
s = s.replace(
    old_gesture,
    "        gesturesEnabled = true, // Wudroid: swipe to open/close original drawer\n",
    1,
)

# 4) Connect a real callback from the original drawer to our test function.
call_anchor = '''                        onResetInputOverlay = {
                            viewModel.resetInputOverlayLayout()
                            closeDrawer()
                        },
                        onQuit = {
'''
call_replacement = '''                        onResetInputOverlay = {
                            viewModel.resetInputOverlayLayout()
                            closeDrawer()
                        },
                        onWudroidTest = {
                            showWudroidTestDialog = true
                            closeDrawer()
                        },
                        onQuit = {
'''
if call_anchor not in s:
    raise SystemExit("EmulationSideMenuContent callback anchor missing")
s = s.replace(call_anchor, call_replacement, 1)

# 5) Add callback parameter to the ORIGINAL EmulationSideMenuContent.
param_anchor = '''    onEditInputOverlay: () -> Unit,
    onResetInputOverlay: () -> Unit,
    onQuit: () -> Unit,
) {
'''
param_replacement = '''    onEditInputOverlay: () -> Unit,
    onResetInputOverlay: () -> Unit,
    onWudroidTest: () -> Unit,
    onQuit: () -> Unit,
) {
'''
if param_anchor not in s:
    raise SystemExit("EmulationSideMenuContent parameter anchor missing")
s = s.replace(param_anchor, param_replacement, 1)

# 6) Put a visible, clickable Test Function directly above Exit.
exit_anchor = '''    TextButtonItem(
        label = tr("Exit"),
        onClick = onQuit,
    )
'''
test_item = '''    TextButtonItem(
        label = "Função teste",
        onClick = onWudroidTest,
    )

    TextButtonItem(
        label = tr("Exit"),
        onClick = onQuit,
    )
'''
if exit_anchor not in s:
    raise SystemExit("Original Exit item anchor missing")
s = s.replace(exit_anchor, test_item, 1)

# 7) Show a Wudroid-styled functional test dialog.
quit_call = '''    if (showQuitConfirmationDialog) {
        EmulationQuitConfirmationDialog(
            onQuit = onQuit,
            onDismiss = { showQuitConfirmationDialog = false },
        )
    }

'''
quit_and_test_calls = '''    if (showQuitConfirmationDialog) {
        EmulationQuitConfirmationDialog(
            onQuit = onQuit,
            onDismiss = { showQuitConfirmationDialog = false },
        )
    }

    if (showWudroidTestDialog) {
        WudroidTestDialog(
            onDismiss = { showWudroidTestDialog = false },
        )
    }

'''
if quit_call not in s:
    raise SystemExit("Quit confirmation invocation anchor missing")
s = s.replace(quit_call, quit_and_test_calls, 1)

# 8) Theme the original exit confirmation with the same Wudroid palette/cards.
old_quit_fn = '''@Composable
private fun EmulationQuitConfirmationDialog(onQuit: () -> Unit, onDismiss: () -> Unit) {
    AlertDialog(
        title = { Text(tr("Exit confirmation")) },
        text = { Text(tr("Are you sure you want to exit?")) },
        confirmButton = { TextButton(onClick = onQuit) { Text(tr("Yes")) } },
        dismissButton = { TextButton(onClick = onDismiss) { Text(tr("No")) } },
        onDismissRequest = onDismiss,
    )
}
'''
new_quit_fn = '''@Composable
private fun EmulationQuitConfirmationDialog(onQuit: () -> Unit, onDismiss: () -> Unit) {
    AlertDialog(
        title = {
            Text(
                text = "Sair da emulação",
                color = WudroidDrawerText,
                fontWeight = FontWeight.Bold,
            )
        },
        text = {
            Text(
                text = "Tem certeza que deseja encerrar o jogo?",
                color = WudroidDrawerMuted,
            )
        },
        confirmButton = {
            TextButton(onClick = onQuit) {
                Text("Sair", color = WudroidCyan, fontWeight = FontWeight.Bold)
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancelar", color = WudroidDrawerText)
            }
        },
        onDismissRequest = onDismiss,
        containerColor = WudroidDrawerSurface,
        titleContentColor = WudroidDrawerText,
        textContentColor = WudroidDrawerMuted,
        shape = RoundedCornerShape(24.dp),
    )
}
'''
if old_quit_fn not in s:
    raise SystemExit("Original EmulationQuitConfirmationDialog anchor missing")
s = s.replace(old_quit_fn, new_quit_fn, 1)

# 9) Functional test dialog, using exactly the same palette as the drawer.
loading_anchor = '''@Composable
private fun EmulationLoadingDialog() {
'''
test_dialog = '''@Composable
private fun WudroidTestDialog(onDismiss: () -> Unit) {
    AlertDialog(
        title = {
            Text(
                text = "Função teste",
                color = WudroidCyan,
                fontWeight = FontWeight.Bold,
            )
        },
        text = {
            Text(
                text = "Funcionou! Esta ação veio diretamente do menu lateral original da emulação.",
                color = WudroidDrawerMuted,
            )
        },
        confirmButton = {
            TextButton(onClick = onDismiss) {
                Text("OK", color = WudroidCyan, fontWeight = FontWeight.Bold)
            }
        },
        onDismissRequest = onDismiss,
        containerColor = WudroidDrawerSurface,
        titleContentColor = WudroidDrawerText,
        textContentColor = WudroidDrawerMuted,
        shape = RoundedCornerShape(24.dp),
    )
}

@Composable
private fun EmulationLoadingDialog() {
'''
if loading_anchor not in s:
    raise SystemExit("EmulationLoadingDialog anchor missing")
s = s.replace(loading_anchor, test_dialog, 1)

path.write_text(s)

check = path.read_text()
verification = [
    marker,
    "gesturesEnabled = true",
    'label = "Função teste"',
    "onWudroidTest: () -> Unit",
    'text = "Sair da emulação"',
    'text = "Funcionou! Esta ação veio diretamente do menu lateral original da emulação."',
    "containerColor = WudroidDrawerSurface",
]
missing = [x for x in verification if x not in check]
if missing:
    raise SystemExit("Wudroid sidebar Interaction Test2 verification failed: " + ", ".join(missing))

# Ensure Back no longer invokes toggleMenu directly.
back_region = check[check.find("    BackHandler {"):check.find("    LaunchedEffect(drawerState.isClosed)")]
if "toggleMenu()" in back_region:
    raise SystemExit("BackHandler still toggles the drawer")

print("Wudroid 0.1.1 Original Sidebar Interaction Test2 applied")
print("- swipe gestures enabled on REAL ModalNavigationDrawer")
print("- Back no longer opens the side menu")
print("- Wudroid-styled exit confirmation")
print("- clickable Função teste added to original side menu")
