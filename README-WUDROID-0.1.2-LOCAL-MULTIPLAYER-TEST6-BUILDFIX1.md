# Wudroid 0.1.2 — Local Multiplayer Test6 BuildFix1

GitHub Actions: 91234313888

## Primeiro erro real
`The prefix "android" for attribute "android:name" ... is not bound`

## Causa
O Test6 usava `manifest.find(">")`. O primeiro `>` do AndroidManifest.xml
é normalmente o final de `<?xml ...?>`, então as permissões do hotspot eram
inseridas antes da tag `<manifest xmlns:android="...">`.

## Correção
- localiza a abertura real `<manifest ...>` com regex;
- insere as permissões somente depois da declaração `xmlns:android`;
- valida o AndroidManifest.xml com XML parser durante o Apply;
- se o XML quebrar novamente, o Actions falha imediatamente em vez de
  esperar toda a compilação;
- preserva D-pad corrigido, overlay sem carcaça e Wi-Fi do Host;
- mantém versionCode 35.
