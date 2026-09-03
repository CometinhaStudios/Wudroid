# Wudroid 0.1.2 — Local Multiplayer Test8 BuildFix1

GitHub Actions: 91348842609

Primeiro erro real:
`Test8 EmulationSurface callback anchor missing`

Correção:
- não substitui mais o callback original do Cemu;
- adiciona um SurfaceHolder.Callback independente só para streaming;
- surfaceCreated/surfaceChanged anexam a TV SurfaceView;
- surfaceDestroyed solta a captura;
- preserva a inicialização original do Cemu;
- preserva o Test7 BuildFix1;
- mantém versionCode 37.

O log anterior parou no Apply, então o streaming ainda não foi testado em runtime.
