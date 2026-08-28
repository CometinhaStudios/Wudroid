# Wudroid 0.0.6 Crash Fix

Small update package for the existing Wudroid repository.

Changes:
- keeps the upstream Cemu Android manifest instead of replacing it;
- fixes the DocumentsProvider manifest mismatch indirectly by preserving upstream declarations;
- launches EmulationActivity using the same EXTRA_LAUNCH_PATH contract as upstream;
- passes the content URI grant explicitly;
- saves Cemu settings before launching emulation;
- uses AppCompatActivity for the Wudroid launcher;
- keeps the status/navigation inset handling.

Copy this package over the current Wudroid repo, then commit and push.
