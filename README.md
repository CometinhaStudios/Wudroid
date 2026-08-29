# Wudroid 0.1.0-B — BuildFix1

Corrige o erro do `Check Wudroid frontend Kotlin`:

`WudroidAntiAliasingManager.kt:79:53`
- recebido: `Array<String>`
- esperado: `List<String>`

Correção:
`group.presets.toList()`

É um patch incremental para aplicar por cima da 0.1.0-B.
