# Wudroid 0.0.8 — Graphics + Touch v1

Patch para o estado atual do Wudroid (Vulkan X v0.1 + Graphic Packs v980 Test1 + Stats1).

## Gráficos funcionais
- VSync: desligado / duplo / triplo
- Upscaling: Nearest Neighbor / Bilinear / Bicubic / Bicubic Hermite
- Downscaling: mesmas 4 opções
- Escala da tela: manter proporção / esticar

Resolução interna e anti-aliasing aparecem de forma honesta:
- resolução 1X / Graphic Pack por jogo
- anti-aliasing padrão do jogo / Graphic Pack

FSR, Lanczos, MMPX, Mitchell, Mailbox e FIFO Relaxed não são mostrados como funcionais enquanto o core Android/Vulkan X ainda não os implementa.

## Wudroid Touch Layout v1
- ZL/L no alto à esquerda
- ZR/R no alto à direita
- sticks nas laterais
- L3/R3 compactos
- D-pad menor
- ABXY em diamante
- +/- no centro inferior
- Home e Blow Mic ocultos
- transparência inicial 112/255

Na primeira execução desta build, o Wudroid limpa as posições antigas uma vez para o novo preset aparecer.
Em Controles existe `Restaurar layout Wudroid`.

## APK
Wudroid-0.0.8-GraphicsTouch1.apk
