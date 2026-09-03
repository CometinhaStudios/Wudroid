# Wudroid 0.1.2 — Local Multiplayer Test15

Base funcional em runtime: Test14.

Relato do Test14:
- latência praticamente instantânea;
- fluidez ficou boa;
- Player 2 ainda aparecia dentro do layout normal, pequeno para uso como monitor.

Mudanças do Test15 — Monitor Mode:
- ao entrar na sala, Player 2 abre automaticamente em modo monitor;
- orientação landscape durante o monitor;
- modo imersivo com barras do Android ocultas;
- vídeo preserva 16:9, centralizado e sem esticar;
- usa toda a área possível, deixando barras pretas somente se a tela física não for 16:9;
- toque na imagem mostra/esconde a barra de ações;
- botão Controles volta ao layout remoto existente;
- botão Sair encerra a conexão;
- botão para reabrir tela cheia fica disponível no layout de controles;
- pipeline 360p60, pacing e buffers ultra-low-latency do Test14 ficam intactos.

Ainda pendente depois deste teste:
- áudio do jogo no Player 2;
- trocar PixelCopy + ARGB→YUV em Kotlin por rota nativa/GPU para recuperar 720p60 sem trazer latência;
- depois, qualidade/bitrate adaptativos.

versionCode 44
versionName 0.1.2-local-multiplayer-test15
