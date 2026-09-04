package info.cemu.cemu

import android.app.Activity
import android.content.pm.ActivityInfo
import android.view.SurfaceHolder
import android.view.SurfaceView
import android.view.WindowManager
import androidx.activity.compose.BackHandler
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.compose.ui.window.Dialog
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat

private val LanMonitorBlue = Color(0xFF00B8F5)
private val LanMonitorCard = Color(0xF216191D)
private val LanMonitorMuted = Color(0xFF9DA8B4)

@Composable
private fun WudroidLanVideoSurface(
    modifier: Modifier,
) {
    AndroidView(
        modifier = modifier.background(Color.Black),
        factory = { context ->
            SurfaceView(context).apply {
                keepScreenOn = true
                holder.setFixedSize(640, 360)
                holder.addCallback(
                    object : SurfaceHolder.Callback {
                        override fun surfaceCreated(holder: SurfaceHolder) {
                            if (holder.surface.isValid) {
                                WudroidLanVideoClient.attachSurface(holder.surface)
                            }
                        }

                        override fun surfaceChanged(
                            holder: SurfaceHolder,
                            format: Int,
                            width: Int,
                            height: Int,
                        ) {
                            if (holder.surface.isValid) {
                                WudroidLanVideoClient.attachSurface(holder.surface)
                            }
                        }

                        override fun surfaceDestroyed(holder: SurfaceHolder) {
                            WudroidLanVideoClient.detachSurface()
                        }
                    }
                )
            }
        },
    )
}

@Composable
fun WudroidLanVideoPreview() {
    val status by WudroidLanVideoClient.statusFlow.collectAsState()

    Column(modifier = Modifier.fillMaxWidth()) {
        WudroidLanVideoSurface(
            modifier = Modifier
                .fillMaxWidth()
                .aspectRatio(16f / 9f)
                .clip(RoundedCornerShape(14.dp))
        )

        Text(
            text = status,
            color = Color(0xFF9CA3AF),
            fontSize = 11.sp,
            modifier = Modifier.padding(top = 5.dp, start = 2.dp),
        )
    }
}

@Composable
fun WudroidLanFullscreenMonitor(
    controllerKind: String,
    onControllerKindChange: (String) -> Unit,
    onLeave: () -> Unit,
) {
    val context = LocalContext.current
    val activity = context as? Activity
    val status by WudroidLanVideoClient.statusFlow.collectAsState()
    var menuVisible by remember { mutableStateOf(false) }
    var editing by remember { mutableStateOf(false) }

    BackHandler {
        when {
            editing -> editing = false
            menuVisible -> menuVisible = false
            else -> menuVisible = true
        }
    }

    DisposableEffect(activity) {
        if (activity == null) {
            onDispose { }
        } else {
            val oldOrientation = activity.requestedOrientation
            val hadKeepScreenOn =
                (activity.window.attributes.flags and
                    WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON) != 0

            WindowCompat.setDecorFitsSystemWindows(activity.window, false)
            val controller = WindowCompat.getInsetsController(
                activity.window,
                activity.window.decorView,
            )
            controller.systemBarsBehavior =
                WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
            controller.hide(WindowInsetsCompat.Type.systemBars())

            activity.window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
            activity.requestedOrientation = ActivityInfo.SCREEN_ORIENTATION_SENSOR_LANDSCAPE

            onDispose {
                controller.show(WindowInsetsCompat.Type.systemBars())
                activity.requestedOrientation = oldOrientation
                if (!hadKeepScreenOn) {
                    activity.window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
                }
            }
        }
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Black),
    ) {
        BoxWithConstraints(modifier = Modifier.fillMaxSize()) {
            val videoModifier =
                if (maxWidth > maxHeight * (16f / 9f)) {
                    Modifier.fillMaxHeight().aspectRatio(16f / 9f)
                } else {
                    Modifier.fillMaxWidth().aspectRatio(16f / 9f)
                }

            WudroidLanVideoSurface(
                modifier = videoModifier.align(Alignment.Center)
            )
        }

        // TEST18: controls stay over the streamed game like normal emulation.
        WudroidLanRemoteControllerOverlay(
            controllerKind = controllerKind,
            editing = editing,
        )

        if (editing) {
            Row(
                modifier = Modifier
                    .align(Alignment.TopCenter)
                    .padding(top = 10.dp)
                    .background(Color(0xDD111418), RoundedCornerShape(18.dp))
                    .padding(horizontal = 12.dp, vertical = 7.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                Text(
                    text = if (controllerKind == "WIIMOTE")
                        "Editando Wii Remote • arraste os grupos"
                    else
                        "Editando GamePad • arraste os grupos",
                    color = Color.White,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                )
                Button(
                    onClick = { editing = false },
                    colors = ButtonDefaults.buttonColors(containerColor = LanMonitorBlue),
                ) {
                    Text("Concluir", color = Color.Black)
                }
            }
        }
    }

    if (menuVisible) {
        Dialog(onDismissRequest = { menuVisible = false }) {
            Card(
                modifier = Modifier
                    .fillMaxWidth(.88f)
                    .widthIn(max = 430.dp),
                colors = CardDefaults.cardColors(containerColor = LanMonitorCard),
                shape = RoundedCornerShape(22.dp),
            ) {
                Column(
                    modifier = Modifier.padding(18.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    Text(
                        "Player 2",
                        color = Color.White,
                        fontSize = 20.sp,
                        fontWeight = FontWeight.Black,
                    )
                    Text(
                        status,
                        color = LanMonitorMuted,
                        fontSize = 11.sp,
                        maxLines = 1,
                    )

                    Text("Controle", color = Color.White, fontWeight = FontWeight.Bold)
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Button(
                            modifier = Modifier.weight(1f),
                            onClick = { onControllerKindChange("WIIMOTE") },
                            colors = ButtonDefaults.buttonColors(
                                containerColor = if (controllerKind == "WIIMOTE") LanMonitorBlue else Color(0xFF272C33)
                            ),
                        ) {
                            Text(
                                "Wii + Nunchuk",
                                color = if (controllerKind == "WIIMOTE") Color.Black else Color.White,
                            )
                        }
                        Button(
                            modifier = Modifier.weight(1f),
                            onClick = { onControllerKindChange("PRO") },
                            colors = ButtonDefaults.buttonColors(
                                containerColor = if (controllerKind != "WIIMOTE") LanMonitorBlue else Color(0xFF272C33)
                            ),
                        ) {
                            Text(
                                "GamePad",
                                color = if (controllerKind != "WIIMOTE") Color.Black else Color.White,
                            )
                        }
                    }

                    Button(
                        modifier = Modifier.fillMaxWidth(),
                        onClick = {
                            menuVisible = false
                            editing = true
                        },
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF272C33)),
                    ) {
                        Text("Editar Controle", color = Color.White)
                    }

                    Button(
                        modifier = Modifier.fillMaxWidth(),
                        onClick = {
                            menuVisible = false
                            onLeave()
                        },
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF3A2024)),
                    ) {
                        Text("Sair da emulação", color = Color.White)
                    }
                }
            }
        }
    }
}
