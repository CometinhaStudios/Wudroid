# Wudroid 0.1.1 - LibraryFix + KeyboardMouse Test1

## 1. Fix ao adicionar pasta de jogos
O launcher de pasta do Wudroid iniciava `NativeGameTitles.reloadGameTitles()` imediatamente e, ao voltar para a tela, `Lifecycle.State.RESUMED` iniciava outra varredura. Este teste remove o reload duplicado e serializa pedidos de atualização com um pequeno debounce.

## 2. Teclado + mouse na emulação
- W/A/S/D -> analógico esquerdo.
- Movimento relativo do mouse -> analógico direito (Z/RZ Android).
- Pointer capture durante a emulação; ESC solta o mouse.
- As demais teclas continuam indo para `InputHandler`, preservando o sistema normal de mapeamento do Cemu para botões do gamepad.

## Observação
Este é Test1 do bridge teclado/mouse. Drivers Android podem anunciar eixos de mouse/joystick de formas diferentes; o código tenta `AXIS_RELATIVE_X/Y` e usa delta de posição como fallback.
