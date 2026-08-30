# Wudroid 0.1.1 — Original Sidebar Interaction Test2

Continuação direta do `OriginalSidebar-WudroidTheme-Test1` que já alterou com sucesso a barra original do Cemu durante a emulação.

Mudanças deste teste:

- `ModalNavigationDrawer` original: `gesturesEnabled = true`
  - deslizar da esquerda para a direita abre o menu;
  - deslizar o menu para a esquerda fecha.
- botão Voltar não abre mais o menu:
  - se a gaveta estiver aberta, fecha;
  - se estiver fechada, abre a confirmação de saída.
- item funcional `Função teste` adicionado diretamente ao `EmulationSideMenuContent` original.
  - ao tocar, abre um popup Wudroid confirmando que o callback funcionou.
- `EmulationQuitConfirmationDialog` original redesenhado com:
  - `#08131C` / `#0D1E2A`;
  - ciano `#00C7F2`;
  - cantos arredondados;
  - textos em português;
  - botões `Cancelar` e `Sair`.

Arquivo original modificado durante a build:

`cemu-engine/src/android/app/src/main/java/info/cemu/cemu/emulation/EmulationScreen.kt`
