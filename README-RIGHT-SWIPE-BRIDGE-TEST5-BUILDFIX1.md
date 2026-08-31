# Wudroid 0.1.1 — Right Swipe Bridge Test5 BuildFix1

Fixes the Test5 patcher's partial-application bug.

The old script used one global marker as an "already applied" condition. After the first edit inserted that marker, later edits were skipped, so the Activity touch bridge and Compose request effect were never installed.

BuildFix1 verifies/applies every component independently:
- `quickSettingsRequestToken` parameter in `EmulationScreen`
- `LaunchedEffect(quickSettingsRequestToken)` bridge
- Activity state token and right-edge tracking fields
- `dispatchTouchEvent()` touchscreen interception
- centered Android system-gesture exclusion rectangle
- token passed from `EmulationActivity` into `EmulationScreen`

No Quick Settings controls or visual design were changed in this fix.
