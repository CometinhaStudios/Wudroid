# Wudroid 0.1.1 — FrameGen Capture — Test 3

Correção incremental da **0.1.1**. A versão pública continua `0.1.1`; `Test 3` identifica apenas esta tentativa de correção do Frame Generation.

## O que muda neste teste

- Mantém o popup de Frame Generation com rolagem e a lógica `Target FPS` x `multiplicador` corrigida.
- Troca o antigo backend-placeholder por uma integração do backend Android real do projeto **LSFG-Android**.
- O GitHub Actions baixa `FrankBarretta/LSFG-Android` com os submódulos `LSFG-Android-Application` e `lsfg-vk-android`.
- O módulo LSFG é convertido em biblioteca Android e incorporado ao mesmo APK do Wudroid.
- Ao importar a `Lossless.dll` do usuário, o Wudroid chama o extractor nativo real (`NativeBridge.extractShaders`) e testa o cache SPIR-V (`NativeBridge.probeShaders`).
- Quando um jogo com FG ativado abre, o Wudroid arma a sessão e solicita, quando necessário, permissão de sobreposição e consentimento de captura de tela.
- A captura usa o caminho MediaProjection -> AHardwareBuffer -> Vulkan/LSFG -> overlay.
- O serviço LSFG é ajustado para **não relançar o Wudroid** quando o próprio Wudroid é o alvo; ele mantém a `EmulationActivity` atual.
- O contador de FPS do backend é ativado para comparar FPS reais com os frames apresentados.

## Teste esperado

1. Importe sua própria `Lossless.dll` na configuração de Frame Generation.
2. Aguarde aparecer que os shaders foram preparados.
3. Ative FG para o jogo.
4. Abra o jogo.
5. Na primeira execução, permita sobreposição e aceite a captura de tela do Android.
6. Observe o overlay do backend. Se o hardware aceitar o pipeline completo, ele deve indicar atividade de LSFG e FPS reais/apresentados.

## Importante

Este pacote é **código-fonte/patch de teste**. O primeiro teste real ainda é o GitHub Actions compilar o APK e depois testar no aparelho. Não considere o Frame Generation confirmado até o APK compilar e o overlay mostrar frames gerados no jogo.

O backend LSFG-Android documenta Frame Generation completo principalmente em GPUs Adreno 7xx ou mais novas; hardware sem as extensões Vulkan exigidas pode cair em modo de espelhamento/captura sem interpolação.

O Wudroid não inclui, baixa ou distribui `Lossless.dll`. O arquivo continua sendo fornecido pelo próprio usuário.

## Arquivos novos/alterados desta correção

- `wudroid-overlay/WudroidFrameGeneration.kt`
- `wudroid-overlay/WudroidFrameGenerationUi.kt`
- `wudroid-overlay/WudroidLsfgCapture.kt`
- `wudroid-overlay/WudroidFrameGenerationNative.kt`
- `wudroid-overlay/WudroidFrameGenerationNative.cpp`
- `wudroid-overlay/apply-v011b-framegen-native.py`
- `wudroid-overlay/apply-v011c-lsfg-capture.py`
- `.github/workflows/build-wudroid.yml`

Os demais arquivos do ZIP são mantidos porque fazem parte da sequência de patches da 0.1.1 já usada pelo repositório.


## Test8 build fix

- fixes the LSFG embed Gradle plugin block that failed during `Check Wudroid frontend Kotlin`;
- uses explicit plugin ids instead of `libs.plugins.*` accessors in the external LSFG module;
- keeps the Wudroid product version at **0.1.1**; only the test/build identifier changes.


## Test8 build fix

- Pins `FrankBarretta/LSFG-Android` to the official `0.1.2` tag.
- Keeps recursive submodules so `LSFG-Android-Application` and `lsfg-vk-android` are actually checked out.
- Removes the incorrect Test4 check against Cemu's empty root `build.gradle.kts`.
- Adds `android-library` to Cemu's version catalog using the same AGP `version.ref` already used by `android-application`.
- Uses Cemu's existing Compose plugin instead of requiring a nonexistent `kotlin.android` alias.


## Test8 fix

The LSFG embed depends on `com.github.topjohnwu.libsu:core/service:5.3.0`.
Those artifacts are hosted on JitPack. Because Cemu uses
`RepositoriesMode.FAIL_ON_PROJECT_REPOS`, this test patches Cemu's
`dependencyResolutionManagement.repositories` and adds a content-filtered
JitPack repository for `com.github.topjohnwu.libsu`.


## Test8 — BuildConfig bridge

Fixes the Kotlin compile failure seen after Test6 when the upstream LSFG Android application is converted into an Android library. Android library modules do not automatically expose application-only `BuildConfig.APPLICATION_ID`, `BuildConfig.VERSION_CODE`, or `BuildConfig.VERSION_NAME`. The embedded LSFG module now defines those fields explicitly using the Wudroid host identity/version so `BenchmarkLogWriter.kt` and `ShizukuCaptureEngine.kt` compile without changing the upstream call sites.


## Test9 — Vulkan loader fix
Test8 reached Cemu native C++ compilation. Test9 registers vkCmdDispatch and vkCreateComputePipelines in Cemu VulkanAPI device dispatch table so WudroidFrameGenVk can compile against the Android Vulkan loader.


## Test10 — VulkanAPI branch-compatible loader patch

Fixes the Test9 preparation failure `Cannot patch VulkanAPI.cpp: no line containing vkCreateGraphicsPipelines`. The Android Cemu branch does not necessarily list every device function explicitly in `VulkanAPI.cpp`. Test10 patches the `VKFUNC_DEVICE(...)` declaration table in `VulkanAPI.h` and only duplicates loader lines in `.cpp` when a compatible explicit loader layout is actually detected. Header-driven/generated layouts are allowed to continue to the real compile step.
