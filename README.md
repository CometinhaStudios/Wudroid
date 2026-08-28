# Wudroid 0.0.8 Build Fix 1

Fixes frontend compilation against the current SSimco/Cemu Android API:

- `GamesListViewModel` package/class name;
- `NativeInput.EmulatedControllerType`;
- `NativeSettings.VSyncMode`;
- `NativeGameTitles.CPUMode`;
- real touch-overlay persistence through `AppSettingsStore` DataStore;
- immutable `InputOverlaySettings.copy(...)` usage;
- `ColumnScope` receiver;
- Foundation opt-in for long-click cards;
- controller settings now call `NativeInput.saveInputs()`.

The workflow now compiles Kotlin first so frontend mistakes fail quickly instead
of waiting ~25 minutes for the native core build.
