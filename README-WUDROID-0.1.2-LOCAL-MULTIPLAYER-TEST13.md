# Wudroid 0.1.2 — Local Multiplayer Test13

Foco: atacar o atraso de aproximadamente 1 segundo relatado no Test12.

O Test12 pedia 720p60, mas o pipeline atual ainda faz:
SurfaceView -> PixelCopy -> Bitmap -> ARGB/YUV em CPU -> MediaCodec H.264.
O custo por frame estava alto demais para priorizar latência.

Mudanças deste teste:
- 640x360
- alvo de 60 FPS
- ~3.2 Mbps
- captura a cada ~16 ms
- buffer UDP do Cliente reduzido para ~96 KB
- no máximo 2 Access Units incompletas em montagem
- decoder não espera por buffer de entrada: se estiver ocupado, o frame novo é descartado em vez de criar fila
- mantém decoder low-latency e render apenas do quadro mais novo
- mantém B-frames desativados no encoder quando suportado

Objetivo:
priorizar resposta do controle e fluidez. Se a latência cair bastante neste teste, o gargalo fica confirmado no caminho de captura/conversão, e a próxima evolução deve substituir a conversão ARGB->YUV em Kotlin por uma rota nativa/GPU para recuperar 720p sem trazer o atraso de volta.

versionCode 42
versionName 0.1.2-local-multiplayer-test13
