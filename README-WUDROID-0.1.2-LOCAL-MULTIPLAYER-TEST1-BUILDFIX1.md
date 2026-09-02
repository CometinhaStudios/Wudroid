# Wudroid 0.1.2 — Local Multiplayer Test1 BuildFix1

Correção focada no GitHub Actions `91036370766`.

## Primeiro erro real
`LibraryScreen root call anchor missing`

O Test1 procurava `LibraryScreen(...)` como um bloco de texto 100% idêntico. O BuildFix1 agora encontra a chamada estruturalmente e insere `onMultiplayer` sem depender de espaçamento ou formatação exata.

## Mantido
- Wudroid 0.1.2
- versionCode 30
- saves experimentais escondidos/desativados
- Perfil local
- Jogador 1 a Jogador 8
- botão Multiplayer na biblioteca
- hospedagem/descoberta LAN no mesmo Wi-Fi ou hotspot
- sem streaming de vídeo/áudio ainda
