# Wudroid 0.1.2 — Local Multiplayer Test10

Base funcional: Test9 BuildFix1.

Este teste altera somente a qualidade do streaming H.264:
- 1280x720
- alvo de 30 FPS
- ~4.0 Mbps
- keyframe ~1 s
- captura a cada ~34 ms
- buffer UDP do Host: 2 MB
- limite de Access Unit: 2.5 MB

Mantido sem alterações:
- multiplayer LAN
- Wi-Fi do Host
- Pro Controller
- Wii Remote
- captura da SurfaceView
- H.264/MediaCodec
- decoder low-latency
- sem áudio por enquanto

Objetivo: medir fluidez, atraso, estabilidade e impacto no FPS do Host
antes de tentar 720p60 ou 1080p.

versionCode 39
versionName 0.1.2-local-multiplayer-test10
