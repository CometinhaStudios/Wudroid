# Wudroid 0.1.1 — Eden Dual Menu Right Swipe Fix Test4

Continuação direta do Test3.

## Correção

O Quick Settings já abria pelo botão, mas o gesto da direita não era confiável porque o drawer esquerdo e o drawer RTL direito disputavam o mesmo gesto horizontal do Material3.

Este teste mantém os dois drawers e adiciona um detector explícito no drawer externo:

- iniciar o gesto nos 40dp da borda física direita;
- arrastar da direita para o centro;
- após 56dp de deslocamento horizontal, abrir `quickDrawerState`;
- o gesto nativo do Quick Settings continua ativo quando ele está aberto, permitindo fechá-lo naturalmente;
- o botão Quick Settings continua funcionando como fallback;
- nenhuma configuração do menu foi removida ou alterada.

O detector não consome um toque simples; só consome o gesto depois de atingir o limiar de abertura.
