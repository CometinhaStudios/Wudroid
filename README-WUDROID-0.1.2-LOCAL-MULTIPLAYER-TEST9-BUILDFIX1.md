# Wudroid 0.1.2 — Local Multiplayer Test9 BuildFix1

GitHub Actions: 91361441087

## Primeiro erro real
`WudroidLanMultiplayer.kt:480:36 No parameter with name 'clearFrame' found.`

## Causa
No Test8, `WudroidLanVideoClient.stop()` usava o parâmetro `clearFrame`.
No Test9 H.264 esse parâmetro virou `clearStatus`, mas uma chamada antiga
permaneceu no `leaveHost()`.

## Correção
- `stop(clearFrame = true)` -> `stop(clearStatus = true)`;
- nenhuma mudança no encoder H.264;
- nenhuma mudança no decoder H.264;
- nenhuma mudança no transporte UDP;
- multiplayer Test7 BuildFix1 preservado;
- versionCode continua 38.
