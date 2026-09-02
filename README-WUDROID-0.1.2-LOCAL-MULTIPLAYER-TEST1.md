# Wudroid 0.1.2 — Local Multiplayer Test1

Nova base de desenvolvimento. Não é BuildFix da 0.1.1.

## Incluído neste Test1
- versionCode 30
- versionName 0.1.2-local-multiplayer-test1
- Save Station / Quick Save / Quick Load escondidos e desativados no menu
- novo menu de Controles no estilo Eden com Jogador 1 a Jogador 8
- tela individual de cada jogador com ativar/desativar e tipo de controle
- configurações touch do Jogador 1 preservadas
- Perfil local: nome do jogador, nome da hospedagem e ID local automático
- botão Multiplayer na biblioteca, acima de Pasta
- descoberta LAN real por UDP broadcast
- entrada em sala por handshake UDP
- funciona no mesmo Wi‑Fi ou hotspot local, sem depender de Internet
- opção “Hospedar / encerrar multiplayer local” no menu durante a emulação

## Ainda NÃO entra neste Test1
- streaming da imagem/áudio do Host para o Jogador 2
- envio dos botões do telefone cliente para o controle 2 do Cemu
- mapeamento automático refinado de múltiplos controles físicos

Esses pontos entram depois que a descoberta/hospedagem Test1 compilar e for validada no aparelho.

## Save Station
O backend antigo permanece no código porque o Turbo Test13 ainda depende de partes dessa cadeia de patches, mas os botões de save state ficam inacessíveis na 0.1.2 Test1.
