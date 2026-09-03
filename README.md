# STATUS ATUAL: Wudroid 0.1.2 — Local Multiplayer Test13

Teste de ultra baixa latência 360p60 para confirmar/remover o gargalo do pipeline 720p60. Veja `README-WUDROID-0.1.2-LOCAL-MULTIPLAYER-TEST13.md`.

# STATUS ATUAL: Wudroid 0.1.2 — Local Multiplayer Test12

Teste 720p60 sobre a base low-latency do Test11. Veja `README-WUDROID-0.1.2-LOCAL-MULTIPLAYER-TEST12.md`.

# STATUS ATUAL: Wudroid 0.1.2 — Local Multiplayer Test9 BuildFix1

Corrige chamada antiga clearFrame -> clearStatus no cliente H.264.

# STATUS ATUAL: Wudroid 0.1.2 — Local Multiplayer Test9

Etapa 2: streaming H.264 / MediaCodec.

# STATUS ATUAL: Wudroid 0.1.2 — Local Multiplayer Test8 BuildFix1

Hook de SurfaceView corrigido sem alterar o callback original do Cemu.

# STATUS ATUAL: Wudroid 0.1.2 — Local Multiplayer Test8

Streaming experimental: Cemu SurfaceView → JPEG/UDP → Player 2.

# STATUS ATUAL: Wudroid 0.1.2 — Local Multiplayer Test7 BuildFix1

Corrige o ciclo de vida do hotspot e a permissão LAN do Android 16.

# STATUS ATUAL: Wudroid 0.1.2 — Local Multiplayer Test7

Corrige o Host Wi-Fi para sobreviver ao fechamento da janela e, no Android 16, usar o nome/segurança definidos pela própria sala.

# STATUS ATUAL: Wudroid 0.1.2 — Local Multiplayer Test6 BuildFix2

Corrige a regex usada para localizar a tag <manifest>.

# STATUS ATUAL: Wudroid 0.1.2 — Local Multiplayer Test6 BuildFix1

Corrige a posição das permissões do hotspot no AndroidManifest.xml.

# STATUS ATUAL: Wudroid 0.1.2 — Local Multiplayer Test6

Test6 corrige o D-pad do Wii Remote horizontal, remove a carcaça branca e adiciona Wi-Fi local criado pelo Host.

# STATUS ATUAL: Wudroid 0.1.2 — Local Multiplayer Test5 BuildFix3

Corrige a verificação antiga do mapeamento Wii Remote no patch Test4.

# STATUS ATUAL: Wudroid 0.1.2 — Local Multiplayer Test5 BuildFix2

Corrige as quebras de linha literais do BuildFix1.

# STATUS ATUAL: Wudroid 0.1.2 — Local Multiplayer Test5 BuildFix1

Corrige o Apply da entrada Controles/Perfil sem reverter o Test5.

# STATUS ATUAL: Wudroid 0.1.2 — Local Multiplayer Test5

Player 1: GamePad/Wii Remote, perfil por jogo atualizado e Wii Remote horizontal. Player 2 remoto mantém Pro/Wii Remote.

# STATUS ATUAL: Wudroid 0.1.2 — Local Multiplayer Test4

Seleção Pro Controller / Wii Remote para Player 2 remoto.

# STATUS ATUAL: Wudroid 0.1.2 — Local Multiplayer Test3

Test3 adiciona controle remoto LAN do Cliente como Player 2 do Host. Streaming de tela continua para a próxima etapa.

# STATUS ATUAL: Wudroid 0.1.2 — Local Multiplayer Test2

Perfil + lobby LAN V2. Veja `README-WUDROID-0.1.2-LOCAL-MULTIPLAYER-TEST2.md`.

# STATUS ATUAL: Wudroid 0.1.2 — Local Multiplayer Test1 BuildFix4

Corrige o import ausente de `re` no patch da 0.1.2.

# STATUS ATUAL: Wudroid 0.1.2 — Local Multiplayer Test1 BuildFix3

Corrige a verificação final de versão do Test1.

# STATUS ATUAL: Wudroid 0.1.2 — Local Multiplayer Test1 BuildFix2

Corrige o FAB da biblioteca sem alterar o escopo do Test1.

# STATUS ATUAL: Wudroid 0.1.2 — Local Multiplayer Test1 BuildFix1

Corrige o Apply da chamada LibraryScreen sem mudar o escopo do Test1.

# STATUS ATUAL: Wudroid 0.1.2 — Local Multiplayer Test1

Nova linha 0.1.2: perfil + Players 1–8 + fundação de multiplayer LAN. Veja `README-WUDROID-0.1.2-LOCAL-MULTIPLAYER-TEST1.md`.

# STATUS ATUAL: Turbo Test13 BuildFix6

Corrige a ordem do patch da configuração inicial sem quebrar WUX/biblioteca. Veja `README-TURBO-TEST13-BUILDFIX6.md`.

# STATUS ATUAL: Turbo Test13 BuildFix5

Corrige a tela inicial e reforça o Turbo 3× sem voltar o projeto para snapshot antigo.

# STATUS ATUAL: Turbo Test13 BuildFix4

Corrige o backend do Turbo para usar `ActiveSettings::SetTimerShiftFactor()` nesta revisão do Cemu. Veja `README-TURBO-TEST13-BUILDFIX4.md`.

# STATUS ATUAL: Turbo Test13 BuildFix3

Corrige o import de `Modifier.offset` ausente na compilação Kotlin. Veja `README-TURBO-TEST13-BUILDFIX3.md`.

# Wudroid 0.1.1 — Turbo Test13 BuildFix1

Pacote incremental sobre o Save Station Test12 BuildFix1.

Novidade principal: botão **⚡ Turbo** no gamepad, com fast-forward nativo 1×/3× e posição ajustável no editor.

Veja `README-TURBO-TEST13.md`.


BuildFix1: corrige os erros Kotlin de `Modifier.align` e `Modifier.size` do botão ⚡.
