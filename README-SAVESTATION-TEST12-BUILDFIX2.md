# Wudroid 0.1.1 — Save Station Test12 BuildFix2

Correção baseada no teste real após o BuildFix1.

## 1. Salvar rápido fechando/travando a emulação
O backend Quick State pausa o CafeSystem enquanto copia/restaura a RAM. Antes a interface dependia do fechamento/animação do drawer para retomar o título.

BuildFix2 faz Quick Save e Quick Load retomarem explicitamente o título (`NativeEmulation.resumeTitle()`), sincronizando também `isWudroidPaused` e `pausedByMenu`.

## 2. Slot de processo anterior bloqueando a Save Station
O motor Test10 ainda é RAM-only e valida a sessão nativa. Um arquivo criado antes de o processo Android morrer não pode ser restaurado com segurança.

Em vez de bloquear o usuário com a frase de “sessão anterior”, o card é apresentado como reutilizável e pode ser salvo novamente na sessão atual. O retorno normal biblioteca -> mesmo jogo continua usando os slots da sessão viva.

## 3. Configuração inicial
A primeira tela “Bem-vindo ao Wudroid” passa a mostrar diretamente:
- seletor de `keys.txt`;
- seletor da pasta de jogos.

Os launchers já existentes são reutilizados, então a cópia/validação de keys e a permissão SAF da pasta continuam no fluxo original.

## 4. Pasta não ficava verde
Ao o seletor de pasta retornar uma URI válida, a primeira tela atualiza imediatamente o estado visual para:

`✓ Pasta de jogos selecionada`

em verde.

## Versão
- versionCode: 29
- versionName: `0.1.1-savestation-test12-buildfix2`

## Limite conhecido
O Save Station ainda não é um savestate completo cross-process. Persistência mesmo após `Forçar parada`, reinício do app/processo ou morte pelo Android exige a próxima fase do engine (CPU/JIT + GPU + áudio + sincronização), não apenas remover a proteção de sessão.
