# Wudroid 0.1.2 — Local Multiplayer Test11

Foco: reduzir latência mantendo a mesma qualidade do Test10.

Mantido:
- 1280x720
- 30 FPS alvo
- 4 Mbps
- H.264 / MediaCodec
- LAN / Wi-Fi do Host
- Pro Controller / Wii Remote

Mudanças:
- encoder: prioridade realtime;
- encoder: operating rate 30;
- encoder: B-frames = 0 quando suportado;
- encoder: low-latency quando suportado;
- decoder: prioridade realtime + low-latency;
- decoder: operating rate 60;
- decoder renderiza só o quadro mais novo disponível;
- Access Units antigas são ignoradas;
- assemblies incompletos reduzidos para 3;
- receive buffer UDP ~384 KB para evitar backlog de vídeo velho.

versionCode 40
versionName 0.1.2-local-multiplayer-test11
