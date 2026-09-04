# Wudroid 0.1.2 — Local Multiplayer Test19

Base: Test18 BuildFix1.

## Correção do Wii Remote
A implementação foi revisada contra o Cemu Android e contra a arquitetura do overlay do Dolphin.

O erro principal do Test18 estava no Nunchuk: os IDs NUNCHUCK_UP/DOWN/LEFT/RIGHT
são eixos analógicos no Cemu Android e devem ir por `NativeInput.onOverlayAxis()`.
O Test18 estava tratando esses quatro IDs como botões digitais.

Test19 agora usa:
- botões A/B/1/2/C/Z/+/-/HOME/D-pad -> `onOverlayButton`;
- Nunchuk stick -> quatro eixos contínuos via `onOverlayAxis`;
- multiplayer envia os eixos por um pacote próprio `WUDROID_INPUT_AXIS_V5`;
- Host aplica os eixos no Controller 2 como Wii Remote.

## Player 1
- Wii Remote + Nunchuk recebe o mesmo layout novo usado no multiplayer;
- o editor mantém o Wii visível durante a edição;
- grupos do Wii podem ser arrastados e ficam persistidos;
- GamePad padrão da emulação foi trocado pelo visual do GamePad do multiplayer;
- GamePad local usa IDs VPAD nativos e eixos VPAD nativos.

## Player 2
- Wii Remote + Nunchuk atualizado com D-pad completo;
- Nunchuk analógico corrigido;
- GamePad do multiplayer preservado;
- menu central preservado.

## Ainda não incluído nesta etapa
IR/pointer e simulação de shake/tilt do Wii Remote são caminhos de motion separados dos
botões/Nunchuk e ficam para uma etapa própria.

versionCode 48
versionName 0.1.2-local-multiplayer-test19
