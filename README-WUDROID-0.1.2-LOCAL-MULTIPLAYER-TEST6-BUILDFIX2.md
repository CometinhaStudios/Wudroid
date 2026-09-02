# Wudroid 0.1.2 — Local Multiplayer Test6 BuildFix2

GitHub Actions: 91241010405

## Primeiro erro real
`Manifest opening tag malformed`

## Causa
A regex do BuildFix1 foi gravada com duas barras antes do `b`,
fazendo o script procurar uma barra literal em vez da tag `<manifest>`.

## Correção
- regex corrigida para `r"<manifest\b[^>]*>"`;
- validada com AndroidManifest em uma linha e multilinha;
- permissões do Wi-Fi do Host continuam dentro de `<manifest ...>`;
- XML resultante continua sendo validado antes do Gradle;
- preserva D-pad horizontal, overlay somente com botões e Wi-Fi do Host;
- mantém versionCode 35.
