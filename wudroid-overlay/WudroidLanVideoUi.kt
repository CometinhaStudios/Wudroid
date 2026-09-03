package info.cemu.cemu

import android.view.SurfaceHolder
import android.view.SurfaceView
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView

@Composable
fun WudroidLanVideoPreview() {
    val status by
        WudroidLanVideoClient.statusFlow
            .collectAsState()

    Column(
        modifier = Modifier.fillMaxWidth()
    ) {
        AndroidView(
            modifier = Modifier
                .fillMaxWidth()
                .aspectRatio(16f / 9f)
                .clip(RoundedCornerShape(14.dp))
                .background(Color.Black),
            factory = { context ->
                SurfaceView(context).apply {
                    keepScreenOn = true

                    holder.addCallback(
                        object :
                            SurfaceHolder.Callback {
                            override fun surfaceCreated(
                                holder: SurfaceHolder
                            ) {
                                if (
                                    holder.surface.isValid
                                ) {
                                    WudroidLanVideoClient
                                        .attachSurface(
                                            holder.surface
                                        )
                                }
                            }

                            override fun surfaceChanged(
                                holder: SurfaceHolder,
                                format: Int,
                                width: Int,
                                height: Int,
                            ) {
                                if (
                                    holder.surface.isValid
                                ) {
                                    WudroidLanVideoClient
                                        .attachSurface(
                                            holder.surface
                                        )
                                }
                            }

                            override fun surfaceDestroyed(
                                holder: SurfaceHolder
                            ) {
                                WudroidLanVideoClient
                                    .detachSurface()
                            }
                        }
                    )
                }
            },
        )

        Text(
            text = status,
            color = Color(0xFF9CA3AF),
            fontSize = 11.sp,
            modifier =
                Modifier.padding(
                    top = 5.dp,
                    start = 2.dp,
                ),
        )
    }
}
