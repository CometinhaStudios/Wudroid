# LSFG / Lossless Scaling source notice

Wudroid **não inclui, baixa nem redistribui `Lossless.dll`**, nem inclui blobs proprietários extraídos dela. O usuário seleciona sua própria cópia.

## Backend usado neste teste

O build da `Wudroid 0.1.1 — FrameGen Capture — Test 2` busca o repositório público:

- `FrankBarretta/LSFG-Android`
  - submódulo `LSFG-Android-Application`
  - submódulo `lsfg-vk-android`

O código de `LSFG-Android-Application` é licenciado sob GNU GPL v3 ou posterior. O script de build preserva uma cópia da licença do projeto dentro dos assets do APK gerado. As licenças e avisos dos submódulos continuam sujeitos aos respectivos repositórios upstream.

O backend usa MediaProjection/AHardwareBuffer e um pipeline Vulkan próprio para executar LSFG sobre a imagem capturada e apresentar o resultado em uma sobreposição Android.

O patch do Wudroid altera somente a integração necessária para incorporar o módulo ao APK e impede que o serviço relance o aplicativo quando o alvo já é a `EmulationActivity` do próprio Wudroid.
