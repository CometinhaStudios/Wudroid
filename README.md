# Wudroid 0.0.9 — BuildFix 1

Corrige a falha no passo `Check Wudroid frontend Kotlin`.

## Correções
- `WudroidCoverArt.kt` não tenta mais acessar `WudroidIcon` e `WIcon`.
  Esses símbolos são `private` dentro de `MainActivity.kt`, portanto outro
  arquivo Kotlin não pode usá-los.
- O fallback de capa agora é autocontido.
- Loops do gerenciador de resolução foram deixados com controle explícito,
  removendo `return@forEach` ambíguo em loops aninhados.

Este patch é incremental: aplique por cima da 0.0.9 Resolution + Box Art Test 1.
