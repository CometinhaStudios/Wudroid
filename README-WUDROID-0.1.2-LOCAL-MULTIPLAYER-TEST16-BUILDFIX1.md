# Wudroid 0.1.2 — Local Multiplayer Test16 BuildFix1

Correção focada no GitHub Actions `91661422294`.

## Erro real
- `EmulationScreen.kt:157:5 Unresolved reference 'DisposableEffect'`
- `EmulationScreen.kt:158:9 Unresolved reference 'onDispose'`

## Causa
O multiplayer injeta um `DisposableEffect` no `EmulationScreen.kt`.
Antes, o patch do botão Turbo também adicionava o import de `DisposableEffect`.
No Test16 o Turbo foi removido do workflow, então o código continuou usando
`DisposableEffect`, mas o import deixou de ser garantido.

## Correção
O patch `apply-v012-local-multiplayer-test1.py` agora garante:

`import androidx.compose.runtime.DisposableEffect`

diretamente no `EmulationScreen.kt`.

## Mantido sem alterações
- Monitor 16:9 do Test16
- 360p60
- pacing do Test14
- ultra-low-latency
- rolagem da configuração inicial
- Turbo continua removido

Mantém `versionCode 45`, pois é BuildFix da mesma Test16.
