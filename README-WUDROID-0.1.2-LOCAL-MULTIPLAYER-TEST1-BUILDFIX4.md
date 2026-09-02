# Wudroid 0.1.2 — Local Multiplayer Test1 BuildFix4

GitHub Actions: 91043200877

## Primeiro erro real
`NameError: name 're' is not defined`

O BuildFix3 passou pelos anchors anteriores e chegou à normalização da versão,
mas o patch usava `re.sub(...)` sem importar o módulo `re`.

## Correção
- adicionado `import re` ao patch `apply-v012-local-multiplayer-test1.py`;
- validado que o próprio patch compila como Python antes de empacotar;
- mantém `versionCode 30`;
- nenhuma alteração na lógica LAN, Perfil, Jogadores 1–8 ou saves.

