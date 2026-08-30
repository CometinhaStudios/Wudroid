#!/usr/bin/env python3
from pathlib import Path

path = Path("cemu-engine/src/android/app/src/main/java/info/cemu/cemu/settings/input/controller/ControllerInputSettingsScreen.kt")
if not path.exists():
    raise SystemExit("ControllerInputSettingsScreen.kt not found")

s = path.read_text()

# Remove the older add-on injection if a previous test already inserted it.
s = s.replace("\n        WudroidKeyboardMouseSettings(controllerIndex = controllerIndex)\n", "\n")
s = s.replace("\n    WudroidKeyboardMouseSettings(controllerIndex = controllerIndex)\n", "\n")

start = s.find("    ScreenContent(")
if start < 0:
    start = s.find("ScreenContent(")
if start < 0:
    raise SystemExit("ScreenContent anchor missing in ControllerInputSettingsScreen.kt")

end_anchor = s.find("    buttonToBind?.let", start)
if end_anchor < 0:
    end_anchor = s.find("buttonToBind?.let", start)
if end_anchor < 0:
    raise SystemExit("buttonToBind anchor missing in ControllerInputSettingsScreen.kt")

block = r'''    ScreenContent(
        snackbarHost = { SnackbarHost(hostState = snackbarHostState) },
        appBarText = "Jogador ${controllerIndex + 1}",
        navigateBack = navigateBack,
    ) {
        Text(
            modifier = Modifier.padding(start = 16.dp, end = 16.dp, top = 10.dp, bottom = 2.dp),
            text = "Configuração de controle",
            style = MaterialTheme.typography.titleLarge,
            fontWeight = FontWeight.Bold,
        )
        Text(
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 2.dp),
            text = "Mapeie gamepad, teclado e mouse diretamente para as entradas do Wii U.",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )

        Toggle(
            label = "Conectado",
            checked = controllerType != EmulatedControllerType.DISABLED,
            onCheckedChanged = { connected ->
                viewModel.setControllerType(
                    if (connected) EmulatedControllerType.PRO
                    else EmulatedControllerType.DISABLED
                )
            },
        )

        if (controllerType == EmulatedControllerType.DISABLED) {
            Text(
                modifier = Modifier.padding(16.dp),
                text = "Ative ‘Conectado’ para configurar o Jogador ${controllerIndex + 1}.",
                style = MaterialTheme.typography.bodyMedium,
            )
            return@ScreenContent
        }

        SingleSelection(
            isChoiceEnabled = viewModel::isControllerTypeAllowed,
            label = "Tipo de controle",
            initialChoice = { controllerType },
            choices = listOf(
                EmulatedControllerType.VPAD,
                EmulatedControllerType.PRO,
                EmulatedControllerType.CLASSIC,
                EmulatedControllerType.WIIMOTE,
            ),
            choiceToString = { controllerTypeToString(it) },
            onChoiceChanged = viewModel::setControllerType,
        )

        WudroidKeyboardMouseSettings(controllerIndex = controllerIndex)

        Header("Mapeamento")
        Row(
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Button(onClick = {
                refreshControllers { showMapAllInputsDialog = true }
            }) {
                Text("Mapear automaticamente")
            }
            Button(onClick = {
                refreshControllers { showControllerSettingsDialog = true }
            }) {
                Text("Config. do dispositivo")
            }
        }
        Text(
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp),
            text = "Toque em uma entrada para mapear. Segure para limpar.",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )

        when (controllerType) {
            EmulatedControllerType.VPAD -> VPADInputs(
                controllerIndex = controllerIndex,
                onInputClick = ::onInputClick,
                onInputLongClick = ::onInputLongClick,
                controlsMapping = controls,
            )
            EmulatedControllerType.PRO -> ProControllerInputs(
                onInputClick = ::onInputClick,
                onInputLongClick = ::onInputLongClick,
                controlsMapping = controls,
            )
            EmulatedControllerType.CLASSIC -> ClassicControllerInputs(
                onInputClick = ::onInputClick,
                onInputLongClick = ::onInputLongClick,
                controlsMapping = controls,
            )
            EmulatedControllerType.WIIMOTE -> WiimoteControllerInputs(
                onInputClick = ::onInputClick,
                onInputLongClick = ::onInputLongClick,
                controlsMapping = controls,
            )
        }
    }

'''

s = s[:start] + block + s[end_anchor:]
path.write_text(s)

check = path.read_text()
required = [
    'appBarText = "Jogador ${controllerIndex + 1}"',
    'WudroidKeyboardMouseSettings(controllerIndex = controllerIndex)',
    'Text("Mapear automaticamente")',
    'EmulatedControllerType.PRO -> ProControllerInputs(',
    'buttonToBind?.let',
]
missing = [item for item in required if item not in check]
if missing:
    raise SystemExit("Full controller UI verification failed: " + ", ".join(missing))

print("Wudroid 0.1.1 Full Controller UI Test1 applied")
print("- controller page replaced by unified mapper")
print("- keyboard + mouse integrated into controller page")
print("- native Cemu input binding popup preserved")
print("- VPAD/Pro/Classic/Wiimote mappings preserved")
