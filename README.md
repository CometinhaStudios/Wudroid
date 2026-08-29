# Wudroid 0.1.0-A — WUX Importer — Test 1

Primeiro APK de teste do novo sistema de importação da 0.1.0.

Ao tocar em **Adicionar** na biblioteca aparecem duas opções:

- **Adicionar pasta**
- **Importar arquivo WUX**

O importador usa o `WudEngine.java` do projeto
`CometinhaStudios/WudCompressAndroid` (WudCompressMobile).

Fluxo deste primeiro teste:

1. seleciona a pasta da biblioteca;
2. seleciona um `.wux`;
3. valida o cabeçalho WUX0;
4. converte WUX -> WUD dentro da pasta escolhida;
5. verifica o resultado byte a byte;
6. atualiza a biblioteca;
7. **mantém o WUX original**.

Se ocorrer erro, o WUD incompleto é removido e o WUX original fica intacto.

## Importante

Este é o **0.1.0-A Test 1**. Ainda não faz a etapa final WUD ->
`code/content/meta`. Primeiro vamos confirmar no aparelho real que a integração
WudCompressMobile + SAF + biblioteca é estável. Depois adicionamos a extração do
disco.

Um WUD reconstruído pode ocupar muito mais espaço que o WUX, então deixe espaço
livre suficiente no destino.

Artifact esperado:

`Wudroid-0.1.0A-WUX-Importer-Test1.apk`
