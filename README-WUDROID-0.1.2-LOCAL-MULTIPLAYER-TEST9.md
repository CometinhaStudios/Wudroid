# Wudroid 0.1.2 — Local Multiplayer Test9

Etapa 2 do streaming.

Base:
- Test8 BuildFix1 comprovado funcionando em runtime.

Host:
- PixelCopy continua capturando somente a TV SurfaceView do Cemu;
- JPEG removido;
- frame convertido para YUV420;
- preferência por encoder H.264 de hardware via MediaCodec;
- 640x360;
- alvo 24 FPS;
- 1.8 Mbps;
- keyframe ~1 s;
- SPS/PPS reenviado antes dos keyframes.

Player 2:
- SurfaceView dedicada;
- decoder MediaCodec H.264;
- low-latency solicitado no Android 11+;
- render direto na Surface;
- status H.264 na tela.

Rede:
- UDP continua independente dos controles;
- access units H.264 fragmentadas em pacotes pequenos;
- frames incompletos são descartados para evitar fila/latência.

Ainda não:
- áudio;
- 720p/1080p;
- 60 FPS;
- bitrate automático;
- layout final do controle.

Versão:
- versionCode 38
- versionName 0.1.2-local-multiplayer-test9
