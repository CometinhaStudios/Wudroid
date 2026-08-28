# Wudroid 0.0.5 — APK build

Esta versão usa o frontend Wudroid e o port Android mantido em `SSimco/Cemu`.

O GitHub Actions possui **um único job de produto**: gerar um APK instalável ARM64 do Wudroid e publicar somente esse APK nos Artifacts.

## Mudanças da build

- Troca o fork intermediário quebrado pelo `SSimco/Cemu` atual.
- O `.gitmodules` atual do port aponta `ZArchive` para o repositório público `Exzap/ZArchive`.
- Usa JDK 21, seguindo a build Android atual do port.
- Compila `:app:assembleRelease`.
- Alinha e assina o APK automaticamente para teste/instalação.
- Corrige os insets da barra de status, recorte da câmera e barra de navegação/gestos.
- O Artifact final é apenas `Wudroid-0.0.5.apk`.

> A assinatura gerada no CI é uma chave de teste criada durante cada build. Para distribuição oficial futura, será necessário configurar uma chave estável de release.
