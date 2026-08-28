# Wudroid 0.0.7 — Controls & Settings

Small update package for the working 0.0.6 repository.

Adds:
- functional native Cemu settings from the Wudroid settings cards;
- touch controls enabled by default (one-time migration for existing installs);
- direct touch overlay settings;
- direct Wii U game-folder manager;
- preserved upstream native library as `WudroidManagerActivity`, giving access to
  real game list, Graphic Packs, saves/title tools and Cemu per-game profiles;
- in-game quick menu discovery: Android Back opens the existing Cemu side menu
  for touch controls, TV/GamePad, motion, edit layout and exit;
- version 0.0.7.

Important:
The Android port currently exposes per-game CPU/shader/driver profiles, but it
does not expose desktop Cemu's per-game controller-profile selector in its
Android JNI/UI yet. This package does not fake that option. That requires a
Wudroid-specific native bridge and is the next controller-profile task.
