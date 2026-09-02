# Wudroid 0.1.1 — Turbo Test13 BuildFix4

Correção focada no erro real do GitHub Actions `90949560144`.

## Erro
`NativeEmulation.cpp:775:21: error: no member named 'TimerShiftFactor' in 'ActiveSettings'`

A implementação anterior tentava escrever diretamente:

`ActiveSettings::TimerShiftFactor = ...`

## Correção
Nesta revisão do Cemu o fast-forward deve usar o setter:

`ActiveSettings::SetTimerShiftFactor(enabled == JNI_TRUE ? 3 : 1);`

## Escopo
- Mantém o botão ⚡.
- Mantém alternância 1x / 3x.
- Sem mudanças no Save Station.
- Sem mudanças no Quick State.
- Sem mudanças nos demais controles/gamepad.
- Mantém `versionCode 29`, pois é BuildFix da mesma Test13.
