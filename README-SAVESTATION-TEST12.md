# Wudroid 0.1.1 — Save Station Test12

Test12 é a correção de runtime/UI baseada no teste real do Test11.

## Bugs relatados e correções

### 1. Quick Load antigo
Antes, quando o `quick.wstate` vinha de outro processo, a interface dizia que o estado pertencia a outra sessão.

Agora Quick Load trata isso como estado inexistente e mostra apenas:

`Ainda não tem nada salvo`

Quick Save continua sendo temporário/rápido.

### 2. Save Station congelava ao carregar
O Test11 dependia do `LaunchedEffect` do menu para retomar a emulação depois do JNI de Load. Como o próprio `loadQuickState()` pausa o título, havia uma corrida de estado e o jogo podia permanecer congelado como se ainda estivesse pausado.

Test12, em load bem-sucedido:
- fecha a Save Station;
- limpa `pausedByMenu`;
- sincroniza `isWudroidPaused`;
- chama `NativeEmulation.resumeTitle()` explicitamente.

### 3. Sair da emulação e voltar
O `EmulationActivity.onQuit()` antigo fazia `finish()` + `exitProcess(0)`. Isso matava Cemu e obrigava todo slot a virar "sessão anterior".

Test12 remove o `exitProcess(0)` do fluxo normal de sair para a biblioteca:
- o título nativo é pausado;
- o processo Cemu continua vivo;
- ao abrir o MESMO jogo novamente, Wudroid reanexa a Surface e retoma o título existente;
- os slots continuam no mesmo PID/base e podem ser carregados;
- se outro jogo for aberto, o título anterior é encerrado com `CafeSystem::ShutdownTitle()` e o novo é iniciado sem matar o app inteiro.

**Escopo desta correção:** sair da emulação para a biblioteca e voltar ao jogo. Se o Android matar/forçar parar o processo inteiro, o motor Test10 ainda não tem serialização completa de CPU/GPU/áudio para um savestate realmente cross-process.

### 4. Menu maior
A Save Station agora usa `DialogProperties(usePlatformDefaultWidth = false)` e ocupa cerca de 60% da largura da tela em landscape, com limite maior para tablets/celulares largos.

### 5. Captura real por slot
Ao salvar um slot, Test12 captura o `SurfaceView` principal com `PixelCopy` antes do snapshot:
- a captura é do jogo, não da janela da Save Station;
- salva em `slot_N.jpg`;
- miniatura 480 px de largura, JPEG 82%;
- exibida com `ContentScale.Crop` no card;
- apagada junto com o slot.

## Arquivos novos/alterados
- `wudroid-overlay/WudroidEmulationSession.kt` (novo)
- `wudroid-overlay/apply-v011t-savestation-runtimefix.py` (novo)
- `.github/workflows/build-wudroid.yml`

O script Test12 altera no checkout do Cemu:
- `EmulationScreen.kt`
- `EmulationActivity.kt`
- `EmulationViewModel.kt`
- `NativeEmulation.kt`
- `NativeEmulation.cpp`

## Validação sugerida
1. GitHub Actions verde.
2. Abrir jogo e salvar Slot 1.
3. Confirmar thumbnail do momento salvo.
4. Alterar posição no jogo e carregar Slot 1.
5. Confirmar que o jogo retoma e não fica pausado.
6. Sair da emulação para biblioteca sem fechar/forçar parar Wudroid.
7. Abrir o mesmo jogo novamente e carregar Slot 1.
8. Confirmar que o slot segue disponível.
9. Testar Quick Load sem estado válido e confirmar `Ainda não tem nada salvo`.
10. Segurar slot e confirmar que `.wstate`, `.session` e `.jpg` são removidos.
