# Wudroid 0.1.1 - Gamepad Editor Test8 BuildFix1

Fixes the Kotlin compilation failure from Test8 where the structural function parser mistook a default lambda `{}` inside the `InputOverlaySurface` parameter list for the function body.

The fix now scans the full balanced Kotlin parameter list before locating the actual function-body brace. This prevents the old `AndroidView` body from being left behind, which caused unresolved references such as `isVisible`, `inputOverlaySettings`, `onEditFinished`, `onEditAlphaFinished`, `inputMode`, `editorAlpha`, and `editorScale`.

No menu-side behavior is changed. The Test8 editor design remains the same.
