# Wudroid 0.1.1 - Keyboard/Mouse BuildFix3

Fixes the Kotlin compile failure introduced by calling `NativeEmulation.stopEmulation()`.
The current Cemu Android NativeEmulation interface does not export that method.
BuildFix3 restores the upstream-compatible quit path (`finish()` + `exitProcess(0)`) while
keeping the library scan fix and keyboard/mouse support from BuildFix2.
