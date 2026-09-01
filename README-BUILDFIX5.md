# Wudroid 0.1.1 — Quick State Test10 BuildFix5

BuildFix5 corrige os dois erros nativos encontrados no GitHub Actions do BuildFix4.

## Erros corrigidos

1. `JNIUtils::toString` não existe na revisão do Cemu Android usada pelo workflow.
   - A API correta em `JNIUtils.h` é `JNIUtils::FromJString(JNIEnv*, jstring)`.

2. `WudroidQuickState` é declarado dentro de `namespace NativeEmulation`, mas os métodos JNI ficam fora desse namespace.
   - As chamadas agora usam `NativeEmulation::WudroidQuickState::Save(...)` e `NativeEmulation::WudroidQuickState::Load(...)`.

## Arquivo alterado

- `wudroid-overlay/apply-v011r-quickstate-engine.py`

## O que NÃO mudou

- menu atual;
- UI do Save Station;
- planejamento dos 6 slots;
- formato experimental `quick.wstate`;
- regras de snapshot de RAM do Test10.

## Validação adicionada

O Apply step agora exige:
- `JNIUtils::FromJString(env, state_path)`;
- chamadas `NativeEmulation::WudroidQuickState::Save/Load`;
- ausência do antigo `JNIUtils::toString(env, state_path)`;
- ausência de chamadas Quick State sem o namespace `NativeEmulation`.

## Próximo passo

Aplicar este pacote no repositório real `~/storage/downloads/Wudroid`, fazer commit/push e verificar o GitHub Actions. Não gerar/baixar APK até o usuário pedir explicitamente.
