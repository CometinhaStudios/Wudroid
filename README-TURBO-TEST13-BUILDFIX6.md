# Wudroid 0.1.1 — Turbo Test13 BuildFix6

Correção focada no GitHub Actions `90994081646`.

## Primeiro erro real
`Could not find folder launcher block`

O BuildFix5 mudava o `MainActivity.kt` cedo demais. O patch antigo de WUX/biblioteca ainda procurava o formato anterior do launcher e encerrava o Apply.

## BuildFix6
- Restaura o `MainActivity.kt` exato que estava no Git antes do BuildFix5 durante os patches antigos.
- Aplica keys + pasta na primeira tela somente no final do pipeline.
- Não reescreve `folderLauncher`, preservando a lógica de WUX/biblioteca.
- Atualiza o estado verde da pasta a partir de `safeGamePaths()` quando o seletor retorna.
- Corrige a verificação do Turbo que ainda procurava texto fixo `3×`.
- Mantém o backend 1x/3x, getter real e reaplicação periódica do BuildFix5.

Mantém `versionCode 29`, pois é BuildFix da mesma Test13.
