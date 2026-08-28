# Wudroid 0.0.8 — Graphic Packs v980 Test 1

Primeiro teste de compatibilidade usando um Graphic Pack oficial dentro do Wudroid.

## O que entra neste patch

- mantém o **Wudroid Vulkan X v0.1 Test 1** já existente;
- adiciona o Graphic Pack oficial **New Super Mario Bros. U / New Super Luigi U — Title Screen Crash Fix** do `cemu_graphic_packs` Github980;
- copia o pack para a pasta de dados do Wudroid **antes** de `NativeGraphicPacks.refreshGraphicPacks()` / `GraphicPack2::LoadAll()`;
- mantém `rules.txt` e `patch_CrashFix.asm` originais, sem alterações;
- como o pack oficial possui `default = 1`, ele nasce habilitado quando é instalado pela primeira vez;
- não baixa ROMs, keys, arquivos de sistema ou conteúdo de jogos.

## Objetivo do teste

Separar duas hipóteses para o crash de New Super Mario Bros. U:

1. crash conhecido na tela de título causado pela checagem de dados Mii/arquivos de sistema;
2. crash real no backend Vulkan/driver.

Se o jogo passar do ponto onde caía, o problema não era o Vulkan X. Se continuar caindo, o próximo passo é registrar o crash nativo e trabalhar em sincronização/driver.

## Fonte e licença do pack

Os dois arquivos do workaround foram extraídos do upload/repositório oficial `cemu-project/cemu_graphic_packs`, versão Github980. O repositório declara CC0 1.0 Universal; uma cópia da licença está em `wudroid-overlay/GRAPHIC_PACKS_LICENSE.md`.
