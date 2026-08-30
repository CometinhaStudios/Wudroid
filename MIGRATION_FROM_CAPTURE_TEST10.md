# Migração do Capture Test10

1. Remover do workflow o checkout `FrankBarretta/LSFG-Android`.
2. Não copiar/usar `WudroidLsfgCapture.kt`.
3. Não executar `apply-v011c-lsfg-capture.py`.
4. Não exigir `Lossless.dll`.
5. Copiar os arquivos deste pacote para `wudroid-overlay/`.
6. Após instalar Android SDK/NDK, executar:
   - `python3 wudroid-overlay/compile-framegen-shader.py`
   - `python3 wudroid-overlay/apply-v011-native-framegen.py`
7. Manter a versão pública `0.1.1`; use o sufixo de build `native-framegen-test1`.

O novo painel é anexado diretamente à `EmulationActivity`, portanto não precisa de permissão de sobreposição do Android.
