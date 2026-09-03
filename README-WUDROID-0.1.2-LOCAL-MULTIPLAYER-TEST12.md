# Wudroid 0.1.2 — Local Multiplayer Test12

Base funcional: Test11.

Este teste sobe a fluidez do streaming H.264 mantendo a mesma resolução:
- 1280x720
- alvo de 60 FPS
- ~8.0 Mbps
- keyframe ~1 s
- captura a cada ~17 ms
- encoder realtime + low-latency quando suportado
- decoder realtime + low-latency quando suportado
- render do cliente continua priorizando somente o quadro mais novo

Mantido sem alterações:
- multiplayer LAN
- Wi-Fi do Host
- Pro Controller
- Wii Remote
- captura da SurfaceView
- H.264/MediaCodec
- descarte de frames antigos para evitar backlog
- sem áudio por enquanto

Objetivo: validar se o atraso percebido cai ainda mais e se a sensação de resposta
fica mais próxima do jogo a 60 FPS, sem perder estabilidade no Host e no Cliente.

versionCode 41
versionName 0.1.2-local-multiplayer-test12
