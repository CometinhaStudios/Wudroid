# Wudroid 0.1.2 — Local Multiplayer Test19 BuildFix1

Correção focada no GitHub Actions `91704682104`.

## Primeiro erro real

```text
EmulationScreen.kt:504:2 Syntax error: Expecting an element.
EmulationScreen.kt:505:13 @Composable invocations can only happen from the context of a @Composable function
```

## Causa

O patch Test19 precisava substituir o wrapper inteiro criado pelo Test5:

```kotlin
if (wudroidPlayer1IsWiimote ...) {
    ...
} else {
    InputOverlaySurface(...)
}
```

A detecção antiga fazia brace matching a partir do primeiro `if {` e parava
no fechamento da primeira ramificação, antes do `else`.

Assim o `else` antigo permanecia depois do novo bloco, produzindo Kotlin inválido.

## Correção

O Test19 agora usa o `InputOverlaySurface(...)` já localizado dentro do `else`
e remove o wrapper até a chave de fechamento imediatamente posterior à chamada.
Foi adicionado também um guard para recusar o patch caso um `else` órfão permaneça.

## Escopo preservado

- novo Wii + Nunchuk;
- eixo analógico do Nunchuk;
- Wii Player 1;
- Wii Player 2 multiplayer;
- GamePad visual do multiplayer como padrão local;
- editor mantendo o tipo de controle selecionado;
- streaming/crop 16:9/360p60/low-latency.

Mantém:
- `versionCode 48`
- `versionName 0.1.2-local-multiplayer-test19`
