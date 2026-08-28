package info.cemu.cemu

import android.os.Bundle
import androidx.activity.compose.setContent
import androidx.appcompat.app.AppCompatActivity
import info.cemu.cemu.common.ui.components.ActivityContent
import info.cemu.cemu.common.ui.localization.TranslatableContent
import info.cemu.cemu.nativeinterface.NativeSettings
import info.cemu.cemu.settings.gamespath.GamePathsScreen

class WudroidGamePathsActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            TranslatableContent {
                ActivityContent {
                    GamePathsScreen(navigateBack = { finish() })
                }
            }
        }
    }

    override fun onPause() {
        super.onPause()
        NativeSettings.saveSettings()
    }
}
