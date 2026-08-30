package info.cemu.cemu.settings.input.controller

import android.content.Context
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Slider
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp

private const val PREFS_NAME = "wudroid_keyboard_mouse"
private const val KEY_ENABLED = "enabled"
private const val KEY_MOUSE_RIGHT_STICK = "mouse_right_stick"
private const val KEY_SENSITIVITY = "mouse_sensitivity"
private const val KEY_INVERT_X = "invert_x"
private const val KEY_INVERT_Y = "invert_y"
private const val KEY_CAPTURE_POINTER = "capture_pointer"

/**
 * Keyboard + mouse settings shown directly inside the real Cemu controller
 * mapping page. Keyboard buttons are still bound by Cemu's native input mapper:
 * tap an input below and press the desired physical key.
 */
@Composable
fun WudroidKeyboardMouseSettings(controllerIndex: Int) {
    val context = LocalContext.current
    val prefs = remember {
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    }

    var enabled by remember { mutableStateOf(prefs.getBoolean(KEY_ENABLED, true)) }
    var mouseRightStick by remember {
        mutableStateOf(prefs.getBoolean(KEY_MOUSE_RIGHT_STICK, true))
    }
    var capturePointer by remember {
        mutableStateOf(prefs.getBoolean(KEY_CAPTURE_POINTER, true))
    }
    var invertX by remember { mutableStateOf(prefs.getBoolean(KEY_INVERT_X, false)) }
    var invertY by remember { mutableStateOf(prefs.getBoolean(KEY_INVERT_Y, false)) }
    var sensitivity by remember {
        mutableFloatStateOf(prefs.getFloat(KEY_SENSITIVITY, 0.035f))
    }

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 8.dp, vertical = 6.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.55f)
        ),
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Text(
                text = "Teclado + Mouse",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
            )
            Text(
                text = "Jogador ${controllerIndex + 1}",
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.primary,
            )
            Text(
                modifier = Modifier.padding(top = 8.dp),
                text = "Toque em qualquer entrada abaixo (A, B, X, Y, Direcional, Analógico esquerdo, gatilhos...) e pressione a tecla que deseja usar.",
                style = MaterialTheme.typography.bodySmall,
            )
            Text(
                modifier = Modifier.padding(top = 4.dp),
                text = "Exemplo: Analógico esquerdo Cima = W, Baixo = S, Esquerda = A, Direita = D. O mouse pode controlar o analógico direito.",
                style = MaterialTheme.typography.bodySmall,
            )

            SettingSwitch(
                title = "Ativar teclado + mouse",
                checked = enabled,
                onChanged = {
                    enabled = it
                    prefs.edit().putBoolean(KEY_ENABLED, it).apply()
                },
            )

            SettingSwitch(
                title = "Mouse → analógico direito",
                checked = mouseRightStick,
                enabled = enabled,
                onChanged = {
                    mouseRightStick = it
                    prefs.edit().putBoolean(KEY_MOUSE_RIGHT_STICK, it).apply()
                },
            )

            SettingSwitch(
                title = "Capturar ponteiro durante o jogo",
                checked = capturePointer,
                enabled = enabled && mouseRightStick,
                onChanged = {
                    capturePointer = it
                    prefs.edit().putBoolean(KEY_CAPTURE_POINTER, it).apply()
                },
            )

            Text(
                modifier = Modifier.padding(top = 10.dp),
                text = "Sensibilidade do mouse: ${(sensitivity * 1000).toInt()}",
                style = MaterialTheme.typography.bodyMedium,
            )
            Slider(
                value = sensitivity,
                onValueChange = {
                    sensitivity = it
                    prefs.edit().putFloat(KEY_SENSITIVITY, it).apply()
                },
                valueRange = 0.005f..0.100f,
                enabled = enabled && mouseRightStick,
            )

            SettingSwitch(
                title = "Inverter mouse horizontal",
                checked = invertX,
                enabled = enabled && mouseRightStick,
                onChanged = {
                    invertX = it
                    prefs.edit().putBoolean(KEY_INVERT_X, it).apply()
                },
            )
            SettingSwitch(
                title = "Inverter mouse vertical",
                checked = invertY,
                enabled = enabled && mouseRightStick,
                onChanged = {
                    invertY = it
                    prefs.edit().putBoolean(KEY_INVERT_Y, it).apply()
                },
            )

            Text(
                modifier = Modifier.padding(top = 8.dp),
                text = "Dica: toque em ‘Indefinido’ nas entradas abaixo para iniciar o mapeamento. Segure uma entrada para limpar o mapeamento atual.",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun SettingSwitch(
    title: String,
    checked: Boolean,
    enabled: Boolean = true,
    onChanged: (Boolean) -> Unit,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(top = 8.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            modifier = Modifier.weight(1f),
            text = title,
            style = MaterialTheme.typography.bodyMedium,
        )
        Spacer(modifier = Modifier.width(12.dp))
        Switch(
            checked = checked,
            onCheckedChange = onChanged,
            enabled = enabled,
        )
    }
}
