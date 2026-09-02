# Wudroid 0.1.2 — Local Multiplayer Test7

## Host Wi-Fi corrigido

O hotspot agora pertence à sessão multiplayer, não à janela.

Fluxo:
1. Escolha nome da partida.
2. Escolha Público ou Privado.
3. Escolha Mesmo Wi-Fi ou Wi-Fi do Host.
4. Toque Hospedar.

### Android 16 / API 36
Usa `startLocalOnlyHotspotWithConfiguration`.

Wi-Fi do Host:
- SSID = nome da partida
- Público = rede OPEN, sem senha
- Privado = WPA2-PSK usando a MESMA senha da partida
- nome de hotspot limitado a 32 bytes
- senha privada limitada a 8..63 bytes

### Android 15 e anteriores
A API pública antiga do Android escolhe SSID e credenciais.
O Wudroid mantém a reserva ativa e mostra os dados reais gerados.

### Ciclo de vida
- tocar OK e voltar ao jogo NÃO desliga o hotspot;
- fechar apenas a janela NÃO encerra uma sessão ativa;
- `Cancelar host` encerra a sala e fecha o hotspot;
- requisição de hotspot pendente pode ser cancelada com segurança;
- a reserva permanece guardada no objeto global da sessão.

## Mantido
- LAN normal / mesmo Wi-Fi
- hotspot local sem Internet
- Player 2 remoto
- Pro Controller / Wii Remote
- D-pad Wii Remote horizontal corrigido
- overlay Wii Remote apenas com botões
- Save Station desativado

## Versão
- versionCode 36
- versionName 0.1.2-local-multiplayer-test7
