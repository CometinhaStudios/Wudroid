# Wudroid 0.1.2 — Local Multiplayer Test6

## Mudanças

### Wii Remote deitado
O D-pad visual foi rotacionado para o uso horizontal:
- visual ↑ -> entrada Wii Remote RIGHT
- visual ↓ -> entrada Wii Remote LEFT
- visual ← -> entrada Wii Remote UP
- visual → -> entrada Wii Remote DOWN

Isso compensa a rotação física de 90 graus do Wii Remote deitado.

### Somente botões
Removida a carcaça branca/transparente:
- Player 1 Wii Remote: somente botões sobre o jogo
- Player 2 remoto: somente botões no layout do multiplayer
- centro do D-pad agora é transparente

### Wi-Fi do Host
Adicionado suporte ao Android LocalOnlyHotspot:
- Host pode tocar em "Criar Wi-Fi do Host"
- Android cria uma rede Wi-Fi local sem Internet
- Wudroid mostra SSID e senha
- Player 2 conecta nesse Wi-Fi nas configurações do aparelho
- ao voltar ao Multiplayer, a descoberta LAN continua funcionando na rede do Host
- cancelar o Host desliga o hotspot criado pelo Wudroid

Permissões adicionadas:
- ACCESS_WIFI_STATE
- CHANGE_WIFI_STATE
- NEARBY_WIFI_DEVICES (Android 13+)
- ACCESS_FINE_LOCATION até Android 12L

## Versão
- versionCode 35
- versionName 0.1.2-local-multiplayer-test6

Save Station continua desativado.
Streaming de tela ainda não entra neste Test6.
