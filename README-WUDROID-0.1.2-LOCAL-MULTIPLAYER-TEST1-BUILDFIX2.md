# Wudroid 0.1.2 — Local Multiplayer Test1 BuildFix2

Correção focada no GitHub Actions `91039110327`.

## Primeiro erro real
`Library FAB anchor missing`

O BuildFix2 localiza o `floatingActionButton` dentro de `LibraryScreen` pela estrutura das chaves, sem depender da formatação exata. Ele adiciona o botão Multiplayer e preserva o botão Pasta.

Mantidos: Wudroid 0.1.2, versionCode 30, saves desativados, Perfil local, Jogadores 1–8 e descoberta/hospedagem LAN.
