# Wudroid 0.0.9 — Resolution + Box Art — Test 1

Este patch é incremental e deve ser aplicado por cima do estado atual do Wudroid.

## Resolução real

O seletor agora salva e aplica uma escala real usando a API de Graphic Packs do Cemu (`NativeGraphicPacks`) no momento em que o jogo é aberto.

Escalas:

- 0.25X
- 0.5X
- 0.75X
- 1X
- 1.25X
- 1.5X
- 2X
- 3X
- 4X

Esta build inclui um pack de resolução para New Super Mario Bros. U / New Super Luigi U baseado no Graphic Pack v980 enviado para o projeto. TV e GamePad são reduzidos/aumentados juntos.

O gerenciador também tenta aplicar a escala a outros Graphic Packs instalados quando eles expõem uma categoria contendo `Resolution`.

## Capas automáticas

A biblioteca agora usa cards verticais e tenta obter capas `cover3D` do GameTDB automaticamente.

- tenta aproveitar ID6 no caminho do jogo;
- senão consulta o banco de títulos do GameTDB e casa pelo nome;
- prioriza a região do jogo;
- tenta cover3D e depois capa frontal;
- salva em cache interno para não baixar novamente;
- se não achar capa ou estiver sem internet, usa o ícone interno do jogo.

## Mantido

- Vulkan X v0.1
- CrashFix do NSMBU
- Performance Overlay
- Wudroid Touch Layout
- VSync, filtros e escala da tela ligados ao NativeSettings

## APK esperado

`Wudroid-0.0.9-ResolutionBoxArt-Test1.apk`
