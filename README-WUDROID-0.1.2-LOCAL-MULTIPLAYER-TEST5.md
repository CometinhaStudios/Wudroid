# Wudroid 0.1.2 — Local Multiplayer Test5

## Player 1 / solo
- Jogador 1 agora oferece GamePad ou Wii Remote.
- Pro Controller foi removido das escolhas do Jogador 1.
- Ao escolher Wii Remote, ele vira o tipo padrão ativo do slot 1 e é salvo pelo NativeInput.
- Ao segurar um jogo na biblioteca, o perfil por jogo agora oferece GamePad ou Wii Remote.
- Jogos com perfil Wii Remote abrem com o slot 1 em WIIMOTE.
- Na emulação, o overlay touch do Wii Remote é horizontal/deitado.

## Multiplayer
- Mantém Pro Controller ou Wii Remote para o Jogador 2 remoto.
- O Wii Remote remoto também foi redesenhado horizontalmente.

## Mapeamento oficial usado do Cemu WiimoteController::ButtonId
- A = 1
- B = 2
- 1 = 3
- 2 = 4
- Nunchuk Z = 5
- Nunchuk C = 6
- + = 7
- - = 8
- Up = 9
- Down = 10
- Left = 11
- Right = 12
- Nunchuk Up/Down/Left/Right = 13/14/15/16
- Home = 17

Power não é exposto pelo Cemu como botão emulado de jogo e por isso não é enviado como Home.

## Futuro
Movimento, MotionPlus, apontador/IR e Nunchuk ficam para a etapa de sensores/Just Dance.

versionCode 34.
