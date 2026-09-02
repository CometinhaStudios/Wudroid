# Wudroid 0.1.2 — Local Multiplayer Test2

Base: Local Multiplayer Test1 BuildFix4, que já compilou no GitHub Actions.

## Perfil
- corrige o campo que prendia o texto `Jogador`;
- agora usa texto editável normal;
- placeholder `Inserir` aparece quando vazio e some ao digitar;
- nome continua salvo localmente no aparelho.

## Multiplayer dentro da emulação
- item do menu agora se chama apenas `Multiplayer`;
- abre uma janela para definir o nome da partida;
- sala Pública = sem senha;
- sala Privada = senha obrigatória;
- ao hospedar, a janela permanece aberta aguardando alguém entrar;
- seção `Jogadores conectados` mostra o nome do cliente;
- primeiro cliente remoto recebe o papel de Jogador 2;
- botão `OK` só fica habilitado quando houver Jogador 2;
- `Cancelar host` fecha a sala;
- `OK` fecha a janela e volta ao jogo mantendo a hospedagem ativa.

## Multiplayer na biblioteca
- mostra `Buscando partidas na rede` com indicador circular;
- cada sala mostra nome da partida;
- mostra Público ou Privado em texto menor;
- mostra o nome do Host do outro lado;
- salas privadas pedem senha antes de entrar.

## Descoberta LAN
- broadcast UDP continua;
- adicionado fallback por sondagem direta da sub-rede /24;
- isso ajuda em hotspots/roteadores que filtram broadcast;
- não depende de Internet;
- senha não é anunciada na descoberta e é comparada por hash SHA-256 no handshake.

## Ainda fora deste Test2
- transmissão dos botões do aparelho cliente para o Player 2 do Cemu;
- streaming da imagem/áudio do Host para o cliente.

O Test2 valida primeiro a criação, descoberta, entrada, senha e lobby em dois aparelhos.

## Versão
- versionCode 31
- versionName 0.1.2-local-multiplayer-test2
