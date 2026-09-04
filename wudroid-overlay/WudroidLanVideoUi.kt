package info.cemu.cemu

import android.app.Activity
import android.content.pm.ActivityInfo
import android.view.SurfaceHolder
import android.view.SurfaceView
import android.view.WindowManager
import androidx.activity.compose.BackHandler
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
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
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import kotlinx.coroutines.delay

private val LanMonitorBlue = Color(0xFF00B8F5)
private val LanMonitorOverlay = Color(0xB8000000)

@Composable
private fun WudroidLanVideoSurface(
    modifier: Modifier,
) {
    AndroidView(
        modifier = modifier.background(Color.Black),
        factory = { context ->
            SurfaceView(context).apply {
                keepScreenOn = true
                // TEST16: force the decoder target buffer to the transmitted 16:9 size.
                // This prevents some devices from keeping a stale/square Surface buffer.
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
    onShowControls: () -> Unit,
    onLeave: () -> Unit,
) {
    val context = LocalContext.current
    val activity = context as? Activity
    val status by WudroidLanVideoClient.statusFlow.collectAsState()
    var overlayVisible by remember { mutableStateOf(true) }

    BackHandler { onShowControls() }

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
            activity.requestedOrientation =
                ActivityInfo.SCREEN_ORIENTATION_SENSOR_LANDSCAPE

            onDispose {
                controller.show(WindowInsetsCompat.Type.systemBars())
                activity.requestedOrientation = oldOrientation
                if (!hadKeepScreenOn) {
                    activity.window.clearFlags(
                        WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON
                    )
                }
            }
        }
    }

    LaunchedEffect(overlayVisible) {
        if (overlayVisible) {
            delay(2800L)
            overlayVisible = false
        }
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color.Black)
            .clickable { overlayVisible = !overlayVisible },
    ) {
        BoxWithConstraints(modifier = Modifier.fillMaxSize()) {
            val videoModifier =
                if (maxWidth > maxHeight * (16f / 9f)) {
                    Modifier
                        .fillMaxHeight()
                        .aspectRatio(16f / 9f)
                } else {
                    Modifier
                        .fillMaxWidth()
                        .aspectRatio(16f / 9f)
                }

            WudroidLanVideoSurface(
                modifier = videoModifier.align(Alignment.Center)
            )
        }

        if (overlayVisible) {
            Row(
                modifier = Modifier
                    .align(Alignment.TopCenter)
                    .fillMaxWidth()
                    .background(LanMonitorOverlay)
                    .padding(horizontal = 14.dp, vertical = 10.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween,
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = "Player 2 • Monitor",
                        color = Color.White,
                        fontWeight = FontWeight.Bold,
                        fontSize = 14.sp,
                    )
                    Text(
                        text = status,
                        color = Color(0xFFB8C0CA),
                        fontSize = 10.sp,
                        maxLines = 1,
                    )
                }

                Spacer(Modifier.width(8.dp))
                Button(
                    onClick = onShowControls,
                    colors = ButtonDefaults.buttonColors(
                        containerColor = LanMonitorBlue
                    ),
                ) {
                    Text("Controles", color = Color.Black)
                }

                Spacer(Modifier.width(6.dp))
                Button(
                    onClick = onLeave,
                    colors = ButtonDefaults.buttonColors(
                        containerColor = Color(0xFF242A31)
                    ),
                ) {
                    Text("Sair", color = Color.White)
                }
            }
        }
    }
}
