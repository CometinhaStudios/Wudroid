# Wudroid 0.1.1 Keyboard + Mouse Mapping BuildFix1

Fixes Kotlin compilation with the Compose version used by Cemu Android.

- Removed `import androidx.compose.foundation.layout.weight`.
- `Modifier.weight(1f)` remains inside the `RowScope`, where it is valid without that import.
- No behavior changes to keyboard/mouse mapping.
