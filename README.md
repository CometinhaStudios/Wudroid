# Wudroid Vulkan X v0.1 — Test 1

Primeiro teste nativo do novo caminho gráfico experimental do Wudroid.

## O que muda de verdade

- mantém a tradução da GPU Latte do Cemu;
- quando **Wudroid Vulkan X** está selecionado, a `EmulationActivity` ativa `WUDROID_VULKAN_X=1` antes do renderer iniciar;
- o `VulkanRenderer` detecta esse modo dentro do código nativo C++;
- ativa o primeiro perfil próprio: **Pipeline Safe Scheduler v0.1**, que desliga compilação multithread de pipelines no caminho Vulkan X para reduzir concorrência do compilador/driver durante este primeiro teste;
- mantém o Vulkan padrão totalmente separado: sem a variável, o renderer continua com o comportamento original;
- cria diagnóstico de sessão e marcador de encerramento inesperado para ajudar a descobrir em qual estágio o teste caiu.

## Objetivo

Não é ainda um renderer Latte completo reescrito. É o primeiro caminho nativo separado do Vulkan X, feito para validar seleção, comunicação Kotlin -> processo de emulação -> C++ Vulkan e uma política própria de scheduling antes de mexermos em memory manager, texture cache e command scheduler.
