package info.cemu.cemu.emulation

/**
 * Process-local native emulation session ownership for Wudroid.
 *
 * Test12 deliberately stops killing the Android process when the user leaves
 * emulation for the library. Cemu already pauses when the main SurfaceView is
 * destroyed, so keeping the process alive lets the same native title be
 * reattached when the user opens the same game again.
 *
 * This is not a disk serializer. Android process death still clears this
 * object and requires a fresh Cemu title boot.
 */
object WudroidEmulationSession {
    @Volatile
    var activeGamePath: String? = null
        private set

    @Volatile
    var suspended: Boolean = false
        private set

    @Volatile
    var systemsInitialized: Boolean = false

    @Volatile
    var rendererInitialized: Boolean = false

    fun markLaunched(gamePath: String) {
        activeGamePath = gamePath
        suspended = false
    }

    fun markSuspended(gamePath: String) {
        activeGamePath = gamePath
        suspended = true
    }

    fun canResume(gamePath: String): Boolean =
        suspended && activeGamePath == gamePath

    fun markResumed() {
        suspended = false
    }

    fun clearTitle() {
        activeGamePath = null
        suspended = false
    }
}
