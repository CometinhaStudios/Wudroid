# Wudroid 0.1.1 — Turbo Test13

## Objetivo
Adicionar Fast Forward real ao gamepad do Wudroid sem substituir o sistema de input do Wii U.

## Implementado
- botão flutuante **⚡** sobre o gamepad;
- toque alterna entre **1×** e **3×**;
- usa o controle de timing nativo do Cemu (`ActiveSettings::TimerShiftFactor`), o mesmo mecanismo usado pelo fast-forward do Cemu desktop;
- no editor do gamepad o botão ⚡ pode ser arrastado;
- posição do botão é persistida em `SharedPreferences`;
- ao destruir a tela de emulação, o turbo volta automaticamente para 1×;
- versionCode: **29**;
- versionName: **0.1.1-turbo-test13**.

## Observação
Este Test13 é focado no Turbo. Ele mantém as alterações do Save Station Test12 BuildFix1 sem declarar que o savestate cross-process está resolvido. O motor Quick State atual ainda é dependente da sessão para restauração confiável.
