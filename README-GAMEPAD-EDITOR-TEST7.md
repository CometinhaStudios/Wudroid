# Wudroid 0.1.1 - Gamepad Editor Test7

Continuação direta do Menu Flow + Gamepad Test6.

Mudanças deste teste:

- Menu lateral/Quick Settings do Test6 preservados sem alterações.
- Remove o editor antigo com botões Done / mover / redimensionar.
- O editor de controles agora abre um painel Wudroid no topo com:
  - Transparência (0-100%, aplicada ao alpha 0-255)
  - Tamanho global (25-200%, relativo ao tamanho no início da edição)
  - Reset
  - Concluir
- Os controles continuam podendo ser arrastados para reposicionar.
- O redimensionamento individual foi removido deste editor.
- Remove o multiplicador automático de 1.60x introduzido no Test6.
  Esse multiplicador era reaplicado sobre os retângulos salvos e fazia o
  gamepad crescer novamente a cada vez que a edição era concluída.
- A escala global nova usa razão relativa à sessão de edição atual. Portanto,
  100% sempre representa o tamanho com que o editor foi aberto e pressionar
  Concluir repetidamente não aumenta mais os controles.
- Transparência é pré-visualizada em tempo real e persistida ao concluir.

Se um layout salvo já ficou exageradamente grande por causa do Test6, use
Reset uma vez no novo editor e então escolha o tamanho desejado.
