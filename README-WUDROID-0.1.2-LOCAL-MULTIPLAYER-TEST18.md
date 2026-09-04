# Wudroid 0.1.2 — Local Multiplayer Test18

Base: Test17 funcionando em runtime.

## Player 2 como emulação normal
- vídeo 16:9 do Test17 continua em fullscreen;
- controles ficam por cima do jogo;
- BACK abre uma janela central;
- janela possui: Sair da emulação, Wii Remote / GamePad e Editar Controle;
- Wii Remote usa layout touch inspirado no Dolphin/Nunchuk da referência enviada;
- Z, C, A, B, 1, 2, +, −, HOME e Nunchuk virtual estão presentes;
- GamePad mantém D-pad, ABXY, analógicos, gatilhos e +/−;
- Editar Controle mantém o tipo atualmente escolhido e permite arrastar os grupos;
- posições são persistidas no aparelho Player 2.

## Troca de controle ao vivo
Foi adicionado `WUDROID_CONTROLLER_KIND_V4` para o Cliente avisar ao Host quando
o Player 2 alterna entre Wii Remote e GamePad. O Host troca o Controller 2 sem
reconectar à sala.

## Sair da emulação
O botão chama o fluxo real de saída do multiplayer: para o decoder, fecha o socket,
avisa o Host, limpa o Player 2 e volta da tela Multiplayer. Ao entrar novamente,
não reaproveita aquela sessão de Cliente.

## Streaming preservado
- crop 16:9 na origem do Test17;
- 640x360;
- 60 FPS alvo;
- pacing do Test14;
- ultra-low-latency do Test13.

versionCode 47
versionName 0.1.2-local-multiplayer-test18
