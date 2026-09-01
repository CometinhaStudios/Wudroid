# Wudroid 0.1.1 — Turbo Test13 BuildFix3

Correção focada no erro real do GitHub Actions `90944303428`.

## Erro
`EmulationScreen.kt:503:22 Unresolved reference 'offset'`

## Correção
Adicionado o import Compose:

`import androidx.compose.foundation.layout.offset`

O script do Turbo Test13 também verifica a presença desse import após aplicar o patch.

## Escopo
- Sem mudanças no backend 1x/3x.
- Sem mudanças no Save Station.
- Sem mudanças no Quick State.
- Sem mudanças nos demais controles/gamepad.
- Mantém `versionCode 29`, pois é BuildFix da mesma Test13.
