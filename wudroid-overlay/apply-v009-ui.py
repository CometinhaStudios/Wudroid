#!/usr/bin/env python3
from pathlib import Path

path = Path("cemu-engine/src/android/app/src/main/java/info/cemu/cemu/MainActivity.kt")
s = path.read_text()

aspect_import = "import androidx.compose.foundation.layout.aspectRatio\n"
if aspect_import not in s:
    anchor = "import androidx.compose.foundation.layout.Arrangement\n"
    if anchor not in s:
        raise SystemExit("Could not find layout import anchor")
    s = s.replace(anchor, anchor + aspect_import, 1)

old_height = ".height(if (compact) 105.dp else 150.dp)"
new_height = ".aspectRatio(if (compact) 0.72f else 0.70f)"
if old_height in s:
    s = s.replace(old_height, new_height, 1)
elif new_height not in s:
    raise SystemExit("Could not find GameTile cover height")

old_image = '''            if (game.icon != null) {
                Image(
                    bitmap = game.icon!!,
                    contentDescription = game.name,
                    modifier = Modifier.fillMaxSize(),
                    contentScale = ContentScale.Crop
                )
            } else {
                WudroidIcon(WIcon.Gamepad, Modifier.size(58.dp), WBlue)
            }
'''
new_image = '''            WudroidGameCover(
                game = game,
                modifier = Modifier.fillMaxSize(),
            )
'''
if "WudroidGameCover(" not in s:
    if old_image not in s:
        raise SystemExit("Could not find old GameTile image block")
    s = s.replace(old_image, new_image, 1)

resolution_call = "WudroidResolutionManager.applyForGame(context, game)"
if resolution_call not in s:
    anchor = '    val prefs = context.getSharedPreferences(GAME_PROFILE_PREFS, Context.MODE_PRIVATE)\n'
    if anchor not in s:
        raise SystemExit("Could not find startGame profile anchor")
    hook = '''    // Apply the selected Wudroid resolution profile to real Graphic Pack presets.
    WudroidResolutionManager.applyForGame(context, game)

'''
    s = s.replace(anchor, hook + anchor, 1)

path.write_text(s)
print("Wudroid 0.0.9 library + real resolution hook applied")
