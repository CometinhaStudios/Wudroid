# Wudroid 0.1.2 — Local Multiplayer Test17

Base: Test16 BuildFix1.

## Correção principal
O Host não envia mais a SurfaceView inteira.

Antes:
- PixelCopy copiava toda a Surface do emulador;
- barras pretas/pillarbox/letterbox também entravam no frame;
- o cliente recebia 640x360, mas o conteúdo útil podia estar "quadrado" dentro dele.

Agora:
- calculamos um retângulo 16:9 central no Host;
- PixelCopy recebe esse `srcRect`;
- somente esse retângulo é escalado para 640x360;
- o corte acontece ANTES da conversão YUV, encode H.264 e rede.

## Preservado
- 640x360
- 60 FPS alvo
- pacing real do Test14
- ultra-low-latency do Test13
- Monitor Mode
- fullscreen landscape
- Turbo removido
- rolagem da configuração inicial

## Observação
Este Test17 remove conteúdo que esteja fora do viewport 16:9 do jogo.
Se um contador/FPS ou mensagem de shader for desenhado pelo próprio Cemu
DENTRO do framebuffer 16:9, ele ainda poderá aparecer; nesse caso a etapa
seguinte será capturar o framebuffer antes dos overlays internos do Cemu.

versionCode 46
versionName 0.1.2-local-multiplayer-test17
