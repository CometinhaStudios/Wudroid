# Wudroid 0.1.1 — Turbo Test13 BuildFix2

BuildFix focado no erro do GitHub Actions run `90938952594`.

## Erro real

O workflow parou em **Apply Wudroid independent frontend**, antes da compilação:

```text
Unable to insert import: import androidx.compose.foundation.layout.size
Process completed with exit code 1
```

## Correção

`apply-v011u-turbo-test13.py` agora insere qualquer import ausente no fim do bloco de imports Kotlin, sem depender de um import vizinho específico. Isso cobre `layout.size` e torna os demais imports do Turbo Test13 mais resistentes a mudanças de ordem no `EmulationScreen.kt`.

Nenhuma lógica do Turbo, Save Station, Quick State, menus ou gamepad foi alterada neste BuildFix.

- versionCode: 29
- versionName: 0.1.1-turbo-test13
