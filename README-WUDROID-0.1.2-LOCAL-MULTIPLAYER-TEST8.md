# Wudroid 0.1.2 — Local Multiplayer Test8

## Streaming LAN experimental

Primeiro teste real de imagem Host -> Player 2.

Host:
- captura somente a TV SurfaceView do Cemu via PixelCopy;
- não usa MediaProjection;
- não pede permissão de gravação de tela;
- máximo 480x270 neste teste;
- cerca de 10 FPS;
- JPEG qualidade 52;
- fragmenta quadros em UDP pequeno.

Player 2:
- recebe vídeo no mesmo socket da sessão multiplayer;
- remonta os pedaços;
- descarta quadros incompletos/velhos para não acumular atraso;
- mostra o jogo acima do controle virtual;
- controles continuam funcionando em paralelo.

Este NÃO é o streaming final.

Se funcionar, o próximo estágio é substituir JPEG por MediaCodec H.264
por hardware, subir resolução/FPS e depois adicionar áudio.

Versão:
- versionCode 37
- versionName 0.1.2-local-multiplayer-test8
