# Wudroid 0.1.1 - Gamepad Editor Test7 BuildFix1

Fixes the Test7 patch anchor for `EditInputsLayout`.

The old patch required `EmulationSideMenuContent` to immediately follow the editor function. The Eden/Wudroid menu patches changed surrounding function order, so the patch aborted even though `EditInputsLayout` still existed.

BuildFix1 finds the editor function itself and accepts any following private `@Composable`, leaving the Test6 menu flow unchanged.
