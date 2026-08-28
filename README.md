# Wudroid 0.0.8 — BuildFix 2

Corrige dois bugs observados no APK funcional:

1. **Nome no launcher**
   - força `Wudroid` diretamente no `AndroidManifest.xml`;
   - mantém `applicationId = com.cometinhastudios.wudroid`;
   - evita que traduções/recursos herdados mostrem `Cemu`.

2. **Crash ao adicionar pasta**
   - usa `DocumentFile.fromTreeUri(...)`, como o frontend Android upstream;
   - persiste a permissão SAF;
   - não chama `NativeSettings.saveSettings()` nem
     `NativeGameTitles.reloadGameTitles()` dentro do callback do seletor;
   - a biblioteca recarrega depois, pelo `GamesListViewModel`, após o seletor fechar;
   - trata pasta duplicada e erro de acesso sem fechar o app.

A emulação/core não foi alterada.
