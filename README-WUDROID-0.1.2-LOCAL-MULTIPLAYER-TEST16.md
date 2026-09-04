# Wudroid 0.1.2 — Local Multiplayer Test16

Base aprovada: Test14/Test15 com 360p60, pacing real e ultra-low-latency.

## Mudanças
- Player 2 mantém Monitor Mode fullscreen.
- SurfaceView do cliente recebe buffer fixo 640x360 (16:9).
- decoder MediaCodec força preenchimento da Surface 16:9 para evitar saída aparente 4:3/quadrada em alguns aparelhos.
- botão Turbo/raio não é mais aplicado no build.
- configuração inicial ganha rolagem vertical; botão de entrar permanece acessível em telas menores.

## Mantido
- 640x360
- 60 FPS alvo
- 3.2 Mbps
- pacing do Test14
- buffers ultra-low-latency do Test13
- Monitor Mode do Test15

versionCode 45
versionName 0.1.2-local-multiplayer-test16
