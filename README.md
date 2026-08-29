# Wudroid 0.1.0-B — Minecraft + Per-game Graphics + AA + Importer UX

## Minecraft Wii U

Adiciona os arquivos oficiais do `cemu_graphic_packs` v980:

- Minecraft Wii U Mii Crash Fix
- Minecraft Wii U Resolution pack

O Wudroid ativa automaticamente o Crash Fix quando o Title ID é Minecraft Wii U.
O próprio pack informa que o workaround foi feito para a atualização mais recente v688.

## Gráficos individuais por jogo

Segure um jogo na biblioteca e abra `Configurações gráficas deste jogo`.
O perfil é salvo pelo Title ID e permite:

- Vulkan padrão / Vulkan X / usar global
- resolução individual
- VSync individual
- filtro de ampliação
- filtro de redução
- anti-aliasing real quando o Graphic Pack daquele jogo expõe presets

## Anti-aliasing

A configuração global agora oferece:

- Padrão do jogo
- Desativado
- FXAA
- NVIDIA FXAA

Esses modos usam presets reais de Graphic Packs. No perfil individual, o Wudroid lista
os nomes exatos dos presets encontrados para aquele jogo. Se não houver pack com AA,
a interface informa isso em vez de fingir que a opção funciona.

## Importador WUX

Durante a conversão a janela mostra apenas `Importando jogo` e o indicador de progresso.
Depois que a importação termina e é verificada, o Wudroid pergunta:

- `Apagar WUX`
- `Manter WUX`

O arquivo original só é apagado depois de confirmação explícita.

## APK esperado

`Wudroid-0.1.0B-Minecraft-PerGame-AA.apk`
