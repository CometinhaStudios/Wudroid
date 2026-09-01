# Wudroid 0.1.1 — Save Station Test12 BuildFix1

BuildFix1 corrige a falha do GitHub Actions ocorrida durante o passo **Apply Wudroid independent frontend**.

## Primeiro erro real do log

`EmulationViewModel initializeEmulation anchor missing`

O Test12 procurava o corpo inteiro de `initializeEmulation()` por comparação textual exata. A revisão atual do projeto continua tendo a função, mas patches anteriores podem alterar espaçamento/estrutura ao redor dela, fazendo o apply abortar antes da compilação.

## Correção

- `apply-v011t-savestation-runtimefix.py` agora localiza `initializeEmulation()` estruturalmente pelo nome e por chaves balanceadas.
- Apenas a região dessa função é substituída.
- Se a função realmente desaparecer numa revisão futura, o Actions imprime candidatos úteis em vez de falhar com um anchor genérico.

## O que não mudou

- comportamento planejado do Save Station Test12;
- 6 slots 3x2;
- thumbnails via PixelCopy;
- correção de resume após Load;
- Quick Save/Load;
- backend Quick State Test10;
- menus e editor de gamepad.

## Próximo passo

Aplicar este pacote sobre o repositório Wudroid, commit/push e deixar o GitHub Actions chegar à compilação real. Se surgir outro erro, corrigir somente o primeiro erro real seguinte.
