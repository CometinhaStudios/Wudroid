# Wudroid 0.1.1 — Native FrameGen Test 1

Este teste muda completamente o caminho do Frame Generation anterior.

## O que NÃO existe mais neste teste

- Lossless.dll obrigatório
- LSFG-Android embutido
- MediaProjection / captura da tela do Android
- SYSTEM_ALERT_WINDOW
- AccessibilityService
- aplicativo externo processando a imagem

## Arquitetura

`Cemu/Wii U frame -> swapchain Vulkan -> captura interna GPU -> Wudroid Motion Compute -> frame intermediário -> vkQueuePresentKHR -> frame real`

O FrameGen roda dentro do renderer Vulkan do Cemu. O Test 1 cria um segundo `present` por frame real e mantém a ordem `interpolado -> real` usando a mesma fila de apresentação.

O algoritmo inicial é do próprio Wudroid: busca de movimento temporal em compute shader + warp simétrico + filtro de confiança/oclusão. Ele não usa código do GameHub nem do Lossless Scaling.

A pesquisa do GameHub serviu somente para confirmar a arquitetura de integração no renderer. Uma análise independente relata `VK_NV_optical_flow` e compute shaders no backend deles. O Wudroid Test 1 usa um compute fallback próprio para funcionar também quando esse extension não é exposto pelo driver. Se `VK_NV_optical_flow` for detectado, o menu apenas informa; um backend acelerado pode ser adicionado depois.

## Menu durante o jogo

Na borda direita aparece uma pequena alça. Toque ou arraste para a esquerda para abrir:

- Frame Generation ON/OFF ao vivo
- 2x
- Performance / Balanced / Quality
- força dos vetores
- FPS real / gerado / saída
- status do backend

Ativar/desativar solicita recriação segura da swapchain para FIFO sem fechar o jogo.

## Build

O workflow deve executar, depois de instalar o NDK:

```bash
python3 wudroid-overlay/compile-framegen-shader.py
python3 wudroid-overlay/apply-v011-native-framegen.py
```

O script de shader procura `glslc` nos `shader-tools` do NDK. Se o NDK da action não trouxer `glslc`, instale `glslc`/`glslangValidator` no runner e rode novamente.

## Observação de Test 1

Este é um backend experimental. Drivers Android diferem bastante em suporte de uso `TRANSFER_SRC` para imagens da swapchain e em custo de compute. Quando o caminho não é seguro, o Wudroid mantém o jogo rodando e mostra o backend como indisponível em vez de forçar a geração.
