package info.cemu.cemu

import android.os.Bundle
import androidx.activity.compose.setContent
import androidx.appcompat.app.AppCompatActivity
import androidx.compose.animation.EnterTransition
import androidx.compose.animation.ExitTransition
import androidx.compose.runtime.Composable
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.rememberNavController
import info.cemu.cemu.common.ui.components.ActivityContent
import info.cemu.cemu.common.ui.localization.TranslatableContent
import info.cemu.cemu.nativeinterface.NativeSettings
import info.cemu.cemu.settings.SettingsRoute
import info.cemu.cemu.settings.settingsNavigation

class WudroidSettingsActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            TranslatableContent {
                ActivityContent {
                    WudroidSettingsNav()
                }
            }
        }
    }

    override fun onPause() {
        super.onPause()
        NativeSettings.saveSettings()
    }
}

@Composable
private fun WudroidSettingsNav() {
    val navController = rememberNavController()
    NavHost(
        navController = navController,
        startDestination = SettingsRoute,
        enterTransition = { EnterTransition.None },
        exitTransition = { ExitTransition.None },
    ) {
        settingsNavigation(navController)
    }
}
