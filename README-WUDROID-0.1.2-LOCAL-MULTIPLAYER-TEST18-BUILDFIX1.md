# Wudroid 0.1.2 — Local Multiplayer Test18 BuildFix1

Correção focada no GitHub Actions `91696048681`.

## Erro real
`WudroidLanVideoUi.kt:21:43 Cannot access 'val RowColumnParentData?.weight: Float': it is internal in file.`

## Causa
O arquivo importava explicitamente:

`import androidx.compose.foundation.layout.weight`

Nesta revisão do Compose, `Modifier.weight()` deve ser usado dentro de `RowScope`
sem importar diretamente essa propriedade interna.

## Correção
O import explícito foi removido.

## Mantido sem alterações
- overlay de controles do Player 2;
- Wii Remote estilo Dolphin;
- GamePad;
- menu central no botão Voltar;
- Editar Controle;
- troca Wii Remote / GamePad;
- Sair da emulação;
- crop 16:9 do Test17;
- 360p60, pacing e baixa latência.

Mantém `versionCode 47` e `versionName 0.1.2-local-multiplayer-test18`.
