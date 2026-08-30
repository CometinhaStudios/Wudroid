# Wudroid 0.1.1 - LibraryFix + Keyboard/Mouse BuildFix2

Fixes the GitHub Actions failure:

`Verification failed ... GamesListScreen.kt: RESUMED lifecycle performs the single game scan`

The previous verifier incorrectly required a comment string. BuildFix2 verifies behavior instead:
- no immediate `reloadGameTitles()` after Add Folder;
- lifecycle refresh path remains present;
- refresh is debounced in `GamesListViewModel`;
- keyboard/mouse hooks remain installed.

It also guarantees the `kotlinx.coroutines.delay` import when `delay(300)` is present and adds coroutine imports idempotently.
