#!/usr/bin/env python3
from pathlib import Path

main_path = Path(
    "cemu-engine/src/android/app/src/main/java/info/cemu/cemu/MainActivity.kt"
)
if not main_path.exists():
    raise SystemExit("MainActivity.kt missing")

main = main_path.read_text()
marker = "WUDROID_012_LOCAL_MULTIPLAYER_TEST15"

main = main.replace(
    "Wudroid 0.1.2 • multiplayer local Test14",
    "Wudroid 0.1.2 • multiplayer local Test15",
)
main = main.replace(
    "multiplayer local Test14",
    "multiplayer local Test15",
)
main = main.replace(
    "Streaming H.264 360p60 paced ultra-low-latency • Test14",
    "Streaming H.264 360p60 fullscreen monitor • Test15",
)

if marker not in main:
    state_anchor = '    var joinControllerKind by remember { mutableStateOf("PRO") }\n'
    if state_anchor not in main:
        raise SystemExit("Test15 fullscreen state anchor missing")
    main = main.replace(
        state_anchor,
        state_anchor + '    var fullscreenMonitor by remember { mutableStateOf(false) }\n',
        1,
    )

    success_anchor = (
        '                    joinedControllerKind = controllerKind\n'
        '                    status = "Controle remoto conectado • Jogador $joinedPlayerNumber"\n'
    )
    if success_anchor not in main:
        raise SystemExit("Test15 join-success anchor missing")
    main = main.replace(
        success_anchor,
        '                    joinedControllerKind = controllerKind\n'
        '                    fullscreenMonitor = true\n'
        '                    status = "Controle remoto conectado • Jogador $joinedPlayerNumber"\n',
        1,
    )

    leave_anchor = (
        '    fun leaveMultiplayer() {\n'
        '        WudroidLanMultiplayer.leaveHost()\n'
        '        joinedHost = null\n'
        '        joinedPlayerNumber = 0\n'
        '        onBack()\n'
        '    }\n'
    )
    if leave_anchor not in main:
        raise SystemExit("Test15 leave function anchor missing")
    main = main.replace(
        leave_anchor,
        '    fun leaveMultiplayer() {\n'
        '        fullscreenMonitor = false\n'
        '        WudroidLanMultiplayer.leaveHost()\n'
        '        joinedHost = null\n'
        '        joinedPlayerNumber = 0\n'
        '        onBack()\n'
        '    }\n',
        1,
    )

    scaffold_anchor = '    ScreenScaffold("Multiplayer", ::leaveMultiplayer) {\n'
    if scaffold_anchor not in main:
        raise SystemExit("Test15 ScreenScaffold anchor missing")
    main = main.replace(
        scaffold_anchor,
        '    if (joinedHost != null && fullscreenMonitor) {\n'
        '        WudroidLanFullscreenMonitor(\n'
        '            onShowControls = { fullscreenMonitor = false },\n'
        '            onLeave = {\n'
        '                fullscreenMonitor = false\n'
        '                WudroidLanMultiplayer.leaveHost()\n'
        '                joinedHost = null\n'
        '                joinedPlayerNumber = 0\n'
        '                joinedControllerKind = "PRO"\n'
        '                status = "Buscando partidas na rede"\n'
        '            },\n'
        '        )\n'
        '        return\n'
        '    }\n\n'
        + scaffold_anchor,
        1,
    )

    info_anchor = (
        '            Text("${currentHost.hostName} • Jogador $joinedPlayerNumber • $controllerLabel", color = WMuted, fontSize = 12.sp)\n'
        '            Spacer(Modifier.height(6.dp))\n\n'
        '            WudroidLanVideoPreview()\n'
    )
    if info_anchor not in main:
        raise SystemExit("Test15 connected-room UI anchor missing")
    main = main.replace(
        info_anchor,
        '            Text("${currentHost.hostName} • Jogador $joinedPlayerNumber • $controllerLabel", color = WMuted, fontSize = 12.sp)\n'
        '            Spacer(Modifier.height(6.dp))\n\n'
        '            Button(\n'
        '                modifier = Modifier.fillMaxWidth(),\n'
        '                onClick = { fullscreenMonitor = true },\n'
        '                colors = ButtonDefaults.buttonColors(containerColor = WBlue),\n'
        '            ) {\n'
        '                Text("Abrir monitor em tela cheia", color = Color.Black)\n'
        '            }\n\n'
        '            Spacer(Modifier.height(6.dp))\n'
        '            WudroidLanVideoPreview()\n',
        1,
    )

    main += "\n// " + marker + "\n"

main_path.write_text(main)

for required in (
    marker,
    "fullscreenMonitor",
    "WudroidLanFullscreenMonitor(",
    "Abrir monitor em tela cheia",
):
    if required not in main:
        raise SystemExit("Test15 verification failed: " + required)

print("Wudroid 0.1.2 Local Multiplayer Test15 applied")
print("- immersive landscape monitor + preserved 16:9")
print("- tap overlay: Controles / Sair")
