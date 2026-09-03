# Wudroid 0.1.2 — Local Multiplayer Test7 BuildFix1

## Corrigido

1. `startHost()` não chama mais `stopHost()` completo.
   Reiniciar o servidor UDP preserva o Wi-Fi do Host.
   `Cancelar host` continua desligando sala + hotspot.

2. Android 16:
   - Host normal em Mesmo Wi-Fi pede Dispositivos próximos quando necessário.
   - Player 2 pede Dispositivos próximos antes de procurar salas.
   - sem permissão, a tela mostra botão Permitir em vez de buscar para sempre.

3. Busca LAN aumentada de 1100 ms para 1400 ms.

## Mantido
- versionCode 36
- Pro Controller / Wii Remote
- Wii Remote horizontal
- overlay somente com botões
- Público / Privado
- Wi-Fi do Host
