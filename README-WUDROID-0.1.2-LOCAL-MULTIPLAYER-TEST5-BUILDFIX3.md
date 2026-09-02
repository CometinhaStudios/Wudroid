# Wudroid 0.1.2 — Local Multiplayer Test5 BuildFix3

GitHub Actions: 91199950928

## Primeiro erro real
`Test4 verification failed: const val ONE = 3`

## Causa
O Test5 centralizou os IDs do Wii Remote em `WudroidWiimoteMapping.kt`.
O patch antigo do Test4 ainda exigia que `const val ONE = 3` estivesse
declarado dentro do `MainActivity.kt`.

## Correção
- removida a verificação da localização antiga da constante;
- o Test4 agora verifica o uso de `WudroidWiimoteMapping.ONE` e `.HOME`;
- o pacote valida separadamente o arquivo canônico:
  A=1, B=2, 1=3, 2=4, +=7, -=8, direcional=9..12, Home=17;
- nenhuma lógica de controle foi alterada;
- mantém versionCode 34 e todo o Test5.
