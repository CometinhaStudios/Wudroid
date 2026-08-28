# Wudroid 0.0.4 Experimental

First Wudroid build with a real Wii U emulation engine behind the custom Wudroid frontend.

## What changed

- Real Cemu Android core is fetched and compiled by GitHub Actions.
- Wudroid remains the launcher/frontend.
- **ABRIR JOGO** opens Android's document picker and sends the selected Wii U file to Cemu's real `EmulationActivity`.
- ARM64, Vulkan, Android Surface handling, Cemu JIT, filesystem bridge and the existing Android emulation lifecycle come from the Cemu Android port for this bootstrap.
- Status bar, display cutout and navigation bar insets are applied to the actual WebView viewport, not just CSS/padding.
- Samsung gesture/navigation area should no longer overlap the Wudroid menu.

## Supported test files

The inherited Cemu Android engine declares support for Wii U launch paths such as WUA, WUD, WUX, WUHB, ELF and RPX. Compatibility is experimental.

## Build

Push the project to the root of the `Wudroid` repository. GitHub Actions runs **Build Wudroid 0.0.4 Emulation** and uploads `Wudroid-0.0.4-Experimental.apk` as an artifact.

The workflow intentionally clones the native engine recursively during CI so the Wudroid repository does not lose Cemu's required Git submodules when transferred as a ZIP.
