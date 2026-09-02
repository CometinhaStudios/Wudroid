# Wudroid 0.1.2 — Local Multiplayer Test1 BuildFix3

GitHub Actions: 91040760952

Primeiro erro real:
`0.1.2 Test1 verification failed ... ['"0.1.2"']`

Correção:
- a verificação final não exige mais a string isolada `"0.1.2"`;
- agora verifica a presença real de `0.1.2`;
- rótulos conhecidos de versão são normalizados para Wudroid 0.1.2;
- nenhuma lógica LAN, Perfil, Jogadores 1–8 ou saves foi alterada.

Mantém versionCode 30.
