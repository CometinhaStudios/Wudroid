# Wudroid 0.1.1 — Turbo Test13 BuildFix5

## Corrigido
- Usa o `MainActivity.kt` atual do repositório como fonte, evitando regressão da tela inicial.
- `keys.txt` e pasta de jogos aparecem juntos já na primeira tela.
- Ao selecionar uma pasta, o estado da interface é atualizado imediatamente e o indicador fica verde.
- Turbo mantém `ActiveSettings::SetTimerShiftFactor(3)` ativo enquanto o ⚡ estiver ligado e lê `GetTimerShiftFactor()` de volta para mostrar o fator real do backend.
- O fator é reaplicado a cada 250 ms enquanto o turbo estiver ativo para impedir reset silencioso em resume/recriação da superfície Android.

## Preservado
Quick State, Save Station, menus, gamepad/editor e os patches anteriores do Test13.

`versionCode 29` mantido: BuildFix da mesma Test13.
