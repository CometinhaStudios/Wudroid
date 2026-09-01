# Wudroid 0.1.1 — Save Station Test12 BuildFix3

Corrige o erro Kotlin do BuildFix2 sem alterar o backend do Save Station.

- `keysLauncher` e `folderLauncher` permanecem no `WudroidRoot()`.
- Estados visuais de keys/pasta também ficam no `WudroidRoot()`.
- O primeiro passo do `SetupWizard` usa apenas `onImportKeys` e `onChooseFolder` já existentes.
- A primeira tela já mostra os seletores de `keys.txt` e pasta dos jogos.
- Uma pasta adicionada com sucesso muda imediatamente para estado verde.
- Keys válidas também mudam imediatamente para estado verde.
- O fluxo inicial vai da página de seleção para o resumo.
- Mantém as correções do BuildFix2 para Quick Save/Quick Load e slots antigos.

Build: versionCode 30 / `0.1.1-savestation-test12-buildfix3`.
