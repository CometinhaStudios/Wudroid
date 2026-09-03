# Wudroid 0.1.2 — Local Multiplayer Test14

Base funcional em runtime: Test13.

Relato do Test13:
- atraso praticamente instantâneo / não perceptível;
- imagem ainda sem sensação de 60 FPS.

Causa encontrada no capture loop:
- Test13 aguardava 16 ms *depois* de PixelCopy + conversão ARGB→YUV + encode;
- o custo de processamento era somado aos 16 ms, reduzindo o FPS real.

Mudança do Test14:
- mantém 640x360;
- mantém alvo 60 FPS;
- mantém 3.2 Mbps;
- mantém buffers ultra-low-latency do Test13;
- remove a espera fixa pós-processamento;
- usa orçamento real de 16,67 ms por quadro;
- se o processamento usar menos que 16,67 ms, espera apenas o restante;
- se usar 16,67 ms ou mais, agenda a próxima captura imediatamente;
- sem fila extra de frames.

Objetivo: aumentar a cadência real percebida sem reintroduzir o atraso eliminado no Test13.

versionCode 43
versionName 0.1.2-local-multiplayer-test14
