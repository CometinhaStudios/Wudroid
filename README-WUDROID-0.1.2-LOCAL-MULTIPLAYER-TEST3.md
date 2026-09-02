# Wudroid 0.1.2 — Local Multiplayer Test3

## Foco
Controle remoto LAN antes do streaming de tela.

## O que entra
- `versionCode 32`
- mantém salas LAN do Test2
- quando o cliente entra, ele recebe uma tela de controle remoto
- Host ativa o slot Cemu Player 2 como Pro Controller
- comandos UDP em tempo real: A/B/X/Y, D-pad, L/R/ZL/ZR, +/−, L3/R3 e dois analógicos
- socket do cliente permanece aberto depois do JOIN para reduzir custo/latência
- ao sair da partida, o cliente avisa o Host e os comandos presos são liberados

## Teste esperado
1. Host abre um jogo e cria Multiplayer.
2. Cliente encontra e entra na sala.
3. Host vê o nome do Jogador 2 e toca OK.
4. Cliente usa o controle virtual olhando a tela do Host.
5. O jogo deve receber os comandos como Player 2.

## Ainda fora deste Test3
- transmissão da imagem do Host
- transmissão do áudio
- otimizações finais de latência / perda de pacote

Save Station continua desativado.
