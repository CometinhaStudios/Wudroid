# Wudroid 0.1.1 — Save Station Test11

Test11 começa a segunda camada do sistema de estados depois da validação real do Quick State Test10/BuildFix5.

## O que entra
- botão `Save Game • 6 slots` no menu principal;
- janela flutuante `SAVE STATION`;
- 6 slots em grade 3 x 2;
- slot vazio: toque para salvar;
- slot preenchido: toque para carregar;
- slot preenchido: segure para apagar e reutilizar;
- data/hora pelo `lastModified` do arquivo de state;
- diretório separado por jogo;
- trava contra dois saves/loads concorrentes;
- input do jogo fica bloqueado enquanto a Save Station está aberta;
- a pausa criada pelo menu permanece enquanto a janela está aberta e só é liberada ao fechar/carregar.

## Compatibilidade com Test10
O backend nativo NÃO foi reescrito. Test11 reutiliza exatamente:
- `NativeEmulation.saveQuickState(path)`;
- `NativeEmulation.loadQuickState(path)`.

Isso reduz o risco: o motor que o usuário já confirmou como rápido e funcional continua sendo o mesmo.

## Limitação importante
O Quick State Test10 ainda valida PID/base e só carrega states da mesma sessão do app. Por isso Test11 grava um sidecar `.session` com o PID atual e mostra states antigos como `SESSÃO ANTERIOR`, sem fingir que já são saves persistentes entre reinicializações.

## Thumbnail
Test11 cria o espaço visual de preview no card, mas ainda usa um tile de status (`SALVAR`, `PRONTO`, `SESSÃO ANTERIOR`). A captura real do frame do jogo fica para a etapa seguinte, depois que o fluxo 6-slot compilar e for validado em runtime. Isso evita mexer no SurfaceView/PixelCopy junto com a primeira introdução dos slots.

## Arquivos afetados
- `wudroid-overlay/apply-v011s-savestation.py` (novo)
- `.github/workflows/build-wudroid.yml`

## Como validar
1. Build do GitHub Actions precisa ficar verde.
2. Abrir um jogo e abrir o menu com Back.
3. Entrar em `Save Game • 6 slots`.
4. Confirmar grade 3 x 2.
5. Tocar em slot vazio e confirmar mensagem `Slot N salvo`.
6. Voltar ao jogo, alterar algo e tocar no mesmo slot para carregar.
7. Segurar um slot preenchido e confirmar que ele volta a vazio.
8. Confirmar que Quick Save/Carregar rápido continuam funcionando normalmente.
