# Wudroid 0.0.8 — Graphics Engine Selector

Adiciona em **Configurações avançadas > Motor gráfico**:

- **Vulkan padrão** — backend Vulkan atual do Cemu Android (padrão/estável).
- **Wudroid Vulkan X** — opção experimental/protótipo.

A escolha fica persistida em `wudroid_graphics` e também é enviada para a `EmulationActivity` pelo extra `wudroid.graphics_engine`, criando o gancho para conectar o futuro backend experimental.

> Importante: nesta etapa o Vulkan X ainda não substitui o renderer nativo. Ele prepara a seleção e o hand-off sem fingir que um segundo renderer já existe.
