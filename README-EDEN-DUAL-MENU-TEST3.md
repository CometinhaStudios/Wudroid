# Wudroid 0.1.1 — Eden Dual Menu Test3

Continuation of the working Original Sidebar Interaction Test2.

## Left side
The REAL Cemu Android in-game drawer remains the base and now behaves more like the Eden reference:
- Pause / resume emulation
- Hide / show touch controller
- Quick Settings
- Controls / input overlay edit
- Emulated USB devices
- Wii U motion
- Replace TV with GamePad
- Show GamePad
- Reset overlay
- Exit emulation

The temporary `Função teste` button/dialog was removed.

## Right side
A second Material3 drawer is anchored to the right edge using RTL start-edge behavior. Swipe from the right edge toward the center to open it.

Reference options included (Switch-only TV Mode intentionally omitted):
- Turbo speed (visible but disabled until native Cemu speed hook is implemented)
- Slow speed (visible but disabled until native Cemu speed hook is implemented)
- Speed limit + percentage (visible but disabled for same reason)
- GPU Mode: Fast / Balanced / Accurate — wired to Async Shader Compile + Accurate Barriers
- Window Adaptation Filter — wired to Cemu upscaling filter
- Anti-aliasing — displayed as game/Graphic Pack controlled for now
- Async shader compile — functional
- VSync — functional
- Accurate barriers — functional

This build deliberately does not fake speed-control behavior. Those controls are present but disabled until the native core hook exists.
