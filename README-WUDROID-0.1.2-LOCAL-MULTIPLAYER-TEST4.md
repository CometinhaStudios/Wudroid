# Wudroid 0.1.2 — Local Multiplayer Test4

Foco: seleção do tipo de controle remoto do Jogador 2.

Incluído:
- versionCode 33
- Pro Controller preservado do Test3
- opção Wii Remote antes de entrar na sala
- Host configura Player 2 como PRO ou WIIMOTE conforme a escolha
- Wii Remote virtual: A, B, 1, 2, +, -, Home e D-pad
- Host mostra o tipo escolhido ao lado do Jogador 2

Reservado para depois:
- giroscópio/acelerômetro
- MotionPlus
- apontador/IR
- modo específico para Just Dance
- streaming da tela

IDs usados no Wii Remote seguem o enum WiimoteController::ButtonId do Cemu:
A=1, B=2, 1=3, 2=4, +=7, -=8, Up=9, Down=10, Left=11, Right=12, Home=17.

Save Station continua desativado.
