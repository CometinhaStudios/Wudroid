# Wudroid 0.1.1 — Right Swipe Bridge Test5

This is a continuation of Eden Dual Menu Test3 / Right Swipe Fix Test4.

Test5 fixes only the right-edge Quick Settings opening gesture:

- observes touchscreen events in `EmulationActivity.dispatchTouchEvent()` before SurfaceView and InputOverlay;
- reserves a narrow center-right system gesture exclusion region on Android 10+;
- converts a deliberate right-edge -> center swipe into a Compose state token;
- `EmulationScreen` observes that token and opens the already-working Quick Settings drawer;
- sends ACTION_CANCEL to the game/input overlay after the menu gesture triggers;
- keeps the existing Quick Settings button as a fallback;
- does not change Quick Settings functionality or the left menu.

Gesture target: start at the physical right edge, preferably around the vertical middle of the screen, and swipe toward the center.
