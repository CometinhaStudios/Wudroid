# Wudroid 0.1.1 — Quick State Test10 BuildFix4

Fixes the native Quick State overlay so its use of `fs::path`,
`create_directories()` and `remove()` has an explicit C++17 `<filesystem>`
include and `fs = std::filesystem` alias.

Also verifies those native declarations during the Apply step, so a future
regression fails early with a useful message instead of failing deep in the C++ build.

No menu or Save Station behavior was changed.
