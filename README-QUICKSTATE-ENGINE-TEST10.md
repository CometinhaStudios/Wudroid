# Wudroid 0.1.1 — Quick State Engine Test10

Primeira etapa nativa do Save State, inspirada na arquitetura de save/load por slots usada por emuladores como PCSX2/NetherSX2, mas implementada com código original para o core do Cemu/Wudroid.

## O que esta build testa

- `Salvar rápido` no menu lateral real da emulação.
- `Carregar rápido` para restaurar o snapshot criado na mesma sessão.
- Ponte JNI nova em `NativeEmulation`.
- Container `quick.wstate` em cache privado do Wudroid.
- Snapshot das regiões de RAM Wii U que estão realmente mapeadas como leitura/escrita pelo processo.
- Chunks de 64 KiB; chunks zerados não armazenam payload.
- Validação de PID + base da memória: Test10 não permite carregar um state criado por outra execução do app.
- Validação do mapa de memória antes de restaurar, para evitar aplicar metade de um arquivo em regiões que mudaram.

## Limite desta primeira etapa

Test10 ainda não é um Save State completo persistente de Cemu. Ele restaura guest RAM na mesma sessão, enquanto os serializadores dedicados de CPU Espresso, GPU/GX2/Latte, áudio, timers e demais estados host-side ainda precisam ser acrescentados. Por isso esta versão deve ser tratada como motor experimental de rewind/quick-state.

Os 6 slots manuais não entram nesta build; primeiro validamos a fundação Quick Save/Quick Load.
