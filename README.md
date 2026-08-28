# Wudroid 0.0.8 — Performance Overlay Stats 1

Correção e expansão do monitor de desempenho durante a emulação.

## Corrige

O Wudroid já conseguia marcar "Mostrar FPS", mas o Cemu mantém a posição do overlay como `Disabled` por padrão. Portanto o FPS podia estar habilitado e mesmo assim nada ser desenhado na tela.

Agora, ao ativar qualquer estatística, o Wudroid liga automaticamente o overlay no canto superior esquerdo se ele estiver desativado. O mesmo reparo é feito ao iniciar um jogo para configurações antigas.

## Estatísticas disponíveis

- FPS
- uso de CPU do processo
- uso de CPU por núcleo
- RAM usada pelo processo
- VRAM reportada pelo renderer, quando o driver/backend disponibilizar o valor
- draw calls por frame
- debug do renderer

Também adiciona seleção de posição (quatro cantos) e escala do texto de 75% a 175%.

## Implementação

O Cemu já calcula essas estatísticas em `LatteOverlay.cpp`. O patch não cria um contador paralelo: ele corrige a ativação do overlay nativo e expõe ao Kotlin duas chamadas JNI que já existem no Android port (`CPUPerCore` e `VRAM`).

Mantém Vulkan X v0.1 e o Graphic Pack v980 de compatibilidade do NSMBU adicionados nos testes anteriores.
