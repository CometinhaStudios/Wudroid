# Wudroid 0.1.1 — Turbo Test13 BuildFix1

Correção focada nos dois erros Kotlin encontrados no GitHub Actions do Turbo Test13.

## Erros corrigidos
- `EmulationScreen.kt:499:18 Unresolved reference 'align'`
- `EmulationScreen.kt:698:14 Unresolved reference 'size'`

## Mudanças
- o botão ⚡ agora é inserido dentro de um `Box(modifier = Modifier.fillMaxSize())`, garantindo um `BoxScope` válido para `Modifier.align(Alignment.BottomCenter)`;
- adicionada a importação `androidx.compose.foundation.layout.size` usada pelo `.size(58.dp)`;
- backend nativo do turbo, Save Station, Quick State, menus e gamepad existente permanecem inalterados.

Mantém `versionCode 29` e `versionName 0.1.1-turbo-test13`, pois é um BuildFix da mesma etapa.
