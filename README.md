# Wudroid 0.0.8 — Switch-style frontend + keys setup

This patch replaces the launcher/frontend with a Wudroid-owned Compose interface.

## Main changes
- Dark two-column emulator library inspired by common Nintendo Switch emulator frontends.
- Wudroid blue/cyan visual identity and custom-drawn icons (no emoji).
- No redirection to the old Cemu Android home/settings frontend.
- First-run setup wizard:
  1. import `keys.txt`;
  2. select the Wii U games folder;
  3. enter the Wudroid library.
- `keys.txt` is copied automatically to `NativeActiveSettings.getUserDataPath()/keys.txt`.
- Keys are validated locally by format only; their contents are never displayed.
- Game-folder management uses `NativeSettings.addGamesPath/removeGamesPath`.
- Game library uses the Cemu core's `GameListViewModel` and title metadata.
- Touch overlay is enabled for Controller 1 and Controller 1 is automatically set to Wii U GamePad if disabled.
- Wudroid-owned settings for:
  - async shaders;
  - accurate barriers;
  - VSync;
  - FPS overlay;
  - Controller 1 type;
  - touch controls, vibration and transparency;
  - game folders;
  - keys status;
  - system info.
- Long-press a game for a per-game mini profile:
  - GamePad / Pro Controller;
  - CPU mode;
  - favorite;
  - clear shader cache.
- APK identity:
  - app name: `Wudroid`
  - applicationId: `com.cometinhastudios.wudroid`
  - output: `Wudroid-0.0.8.apk`

## Keys note
Wudroid does not provide encryption keys. `keys.txt` must come from the user's own Wii U.
For WUD/WUX, the core reads `keys.txt` only once per process, so after replacing the
file from Settings, fully close and reopen Wudroid before retrying a game.
