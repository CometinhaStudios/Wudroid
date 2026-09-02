package info.cemu.cemu

import android.content.ClipData
import android.content.Context
import android.content.Intent
import android.content.res.Configuration
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.compose.setContent
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBars
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBars
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Checkbox
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Slider
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.ReadOnlyComposable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.TextFieldValue
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.view.WindowCompat
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.documentfile.provider.DocumentFile
import info.cemu.cemu.emulation.EmulationActivity
import info.cemu.cemu.graphics.WudroidVulkanX
import info.cemu.cemu.games.list.GamesListViewModel
import info.cemu.cemu.common.settings.AppSettingsStore
import info.cemu.cemu.common.settings.InputOverlaySettings
import info.cemu.cemu.nativeinterface.NativeActiveSettings
import info.cemu.cemu.nativeinterface.NativeGameTitles
import info.cemu.cemu.nativeinterface.NativeGameTitles.Game
import info.cemu.cemu.nativeinterface.NativeInput
import info.cemu.cemu.nativeinterface.NativeSettings
import java.io.File
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import kotlin.math.roundToInt

private val WBlue = Color(0xFF00B8F5)
private val WBlue2 = Color(0xFF0386E8)
private val WBg = Color(0xFF0D0F12)
private val WCard = Color(0xFF15181D)
private val WCard2 = Color(0xFF1C2026)
private val WText = Color(0xFFF4F7FA)
private val WMuted = Color(0xFF9DA8B4)
private val WLine = Color(0xFF303641)
private val WGreen = Color(0xFF36D17C)
private val WRed = Color(0xFFFF5A63)

private const val SETUP_PREFS = "wudroid_setup"
private const val SETUP_DONE = "setup_done_008"
private const val GAME_PROFILE_PREFS = "wudroid_game_profiles"
private const val GRAPHICS_PREFS = "wudroid_graphics"
private const val GRAPHICS_ENGINE_KEY = "graphics_engine"
private const val GRAPHICS_ENGINE_CEMU_VULKAN = 0
private const val GRAPHICS_ENGINE_WUDROID_VULKAN_X = 1

private enum class Screen {
    Library, Settings, Advanced, Controls, GameFolders, SystemInfo, About
}

private enum class WIcon {
    Search, View, Filter, Settings, Folder, Gamepad, Key, Cpu, App, Check,
    Info, Back, Audio, Display, Trash, Star, Play, Controller, Sliders
}

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        WindowCompat.setDecorFitsSystemWindows(window, false)
        if (WudroidVulkanX.recoverPreviousSession(this)) {
            Toast.makeText(
                this,
                "A sessão anterior do Vulkan X terminou de forma inesperada. O diagnóstico foi preservado.",
                Toast.LENGTH_LONG
            ).show()
        }

        // First real Wudroid controller bootstrap:
        // if Cemu has Controller 1 disabled, configure it as Wii U GamePad.
        try {
            if (NativeInput.isControllerDisabled(0)) {
                NativeInput.setControllerType(0, NativeInput.EmulatedControllerType.VPAD)
                NativeInput.saveInputs()
                NativeSettings.saveSettings()
            }
        } catch (_: Throwable) {}

        // Make the touch overlay genuinely visible by default.
        try {
            val overlay = getOverlaySettings()
            if (!overlay.isOverlayEnabled || overlay.controllerIndex != 0 || overlay.alpha < 150) {
                updateOverlaySettings {
                    it.copy(
                        isOverlayEnabled = true,
                        controllerIndex = 0,
                        alpha = maxOf(it.alpha, 150),
                    )
                }
            }
        } catch (_: Throwable) {}

        setContent {
            WudroidTheme {
                WudroidRoot()
            }
        }
    }

    override fun onPause() {
        super.onPause()
        try { NativeSettings.saveSettings() } catch (_: Throwable) {}
    }
}

@Composable
private fun WudroidTheme(content: @Composable () -> Unit) {
    val dark = darkColorScheme(
        primary = WBlue,
        secondary = WBlue2,
        background = WBg,
        surface = WCard,
        surfaceVariant = WCard2,
        onPrimary = Color.Black,
        onBackground = WText,
        onSurface = WText,
        outline = WLine,
    )
    MaterialTheme(colorScheme = dark, content = content)
}

@Composable
private fun WudroidRoot() {
    val context = LocalContext.current
    val setupPrefs = remember {
        context.getSharedPreferences(SETUP_PREFS, Context.MODE_PRIVATE)
    }
    var setupDone by remember {
        mutableStateOf(setupPrefs.getBoolean(SETUP_DONE, false))
    }
    var screen by remember { mutableStateOf(Screen.Library) }
    var keysMessage by remember { mutableStateOf<String?>(null) }
    var selectedProfileGame by remember { mutableStateOf<Game?>(null) }

    val keysLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.OpenDocument()
    ) { uri ->
        if (uri != null) {
            val result = importKeysFile(context, uri)
            keysMessage = result.second
        }
    }

    var refreshLibraryRequest by remember { mutableIntStateOf(0) }

    val folderLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.OpenDocumentTree()
    ) { uri ->
        if (uri != null && addGameFolder(context, uri)) {
            // Do not reload native titles inside the SAF callback.
            // Let the ViewModel refresh after the picker has returned.
            refreshLibraryRequest++
        }
    }

    if (!setupDone) {
        SetupWizard(
            keysPresent = hasImportedKeys(),
            gameFolderPresent = safeGamePaths().isNotEmpty(),
            keysMessage = keysMessage,
            onImportKeys = {
                keysLauncher.launch(arrayOf("text/plain", "application/octet-stream", "*/*"))
            },
            onChooseFolder = { folderLauncher.launch(null) },
            onFinish = {
                setupPrefs.edit().putBoolean(SETUP_DONE, true).apply()
                setupDone = true
            }
        )
        return
    }

    BackHandler(enabled = screen != Screen.Library) {
        screen = Screen.Library
    }

    when (screen) {
        Screen.Library -> LibraryScreen(
            refreshRequest = refreshLibraryRequest,
            onSettings = { screen = Screen.Settings },
            onChooseFolder = { folderLauncher.launch(null) },
            onGameProfile = { selectedProfileGame = it }
        )
        Screen.Settings -> SettingsScreen(
            onBack = { screen = Screen.Library },
            onAdvanced = { screen = Screen.Advanced },
            onControls = { screen = Screen.Controls },
            onGameFolders = { screen = Screen.GameFolders },
            onImportKeys = {
                keysLauncher.launch(arrayOf("text/plain", "application/octet-stream", "*/*"))
            },
            keysStatus = if (hasImportedKeys()) "Importada" else "Ausente",
            onSystemInfo = { screen = Screen.SystemInfo },
            onAbout = { screen = Screen.About },
        )
        Screen.Advanced -> AdvancedSettingsScreen(onBack = { screen = Screen.Settings })
        Screen.Controls -> ControlsScreen(onBack = { screen = Screen.Settings })
        Screen.GameFolders -> GameFoldersScreen(
            onBack = { screen = Screen.Settings },
            onAdd = { folderLauncher.launch(null) },
            onChanged = { refreshLibraryRequest++ }
        )
        Screen.SystemInfo -> SystemInfoScreen(onBack = { screen = Screen.Settings })
        Screen.About -> AboutScreen(onBack = { screen = Screen.Settings })
    }

    if (selectedProfileGame != null) {
        GameProfileDialog(
            game = selectedProfileGame!!,
            onDismiss = { selectedProfileGame = null },
            onPlay = {
                val game = selectedProfileGame!!
                selectedProfileGame = null
                startGame(context, game)
            }
        )
    }

    if (keysMessage != null && screen != Screen.Library) {
        AlertDialog(
            onDismissRequest = { keysMessage = null },
            confirmButton = {
                Button(onClick = { keysMessage = null }) { Text("OK") }
            },
            title = { Text("keys.txt") },
            text = { Text(keysMessage!!) }
        )
    }
}

@Composable
private fun SetupWizard(
    keysPresent: Boolean,
    gameFolderPresent: Boolean,
    keysMessage: String?,
    onImportKeys: () -> Unit,
    onChooseFolder: () -> Unit,
    onFinish: () -> Unit,
) {
    var step by remember { mutableIntStateOf(0) }
    val currentKeysPresent = hasImportedKeys() || keysPresent
    val currentFolderPresent = safeGamePaths().isNotEmpty() || gameFolderPresent

    Scaffold(
        contentWindowInsets = WindowInsets.safeDrawing,
        containerColor = WBg
    ) { pad ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(pad)
                .padding(horizontal = 26.dp, vertical = 24.dp),
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            Column {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    WudroidMark(64.dp)
                    Spacer(Modifier.width(16.dp))
                    Column {
                        Text("Wudroid", fontWeight = FontWeight.Bold, fontSize = 30.sp)
                        Text("Configuração inicial", color = WMuted)
                    }
                }
                Spacer(Modifier.height(34.dp))

                when (step) {
                    0 -> {
                        SetupTitle("Bem-vindo ao Wudroid")
                        SetupBody(
                            "Antes da primeira inicialização, vamos configurar apenas o necessário: " +
                                "as chaves do seu próprio Wii U e a pasta onde seus jogos estão."
                        )
                        Spacer(Modifier.height(18.dp))
                        StatusPill("Emulador", true, "Core ARM64 / Vulkan pronto")
                        Spacer(Modifier.height(10.dp))
                        StatusPill("Interface", true, "Frontend Wudroid")
                    }
                    1 -> {
                        SetupTitle("Importar keys.txt")
                        SetupBody(
                            "Selecione o seu keys.txt. O Wudroid copia o arquivo para o diretório " +
                                "correto do Cemu automaticamente. O Wudroid não fornece chaves."
                        )
                        Spacer(Modifier.height(20.dp))
                        SetupActionCard(
                            icon = WIcon.Key,
                            title = "Selecionar keys.txt",
                            subtitle = if (currentKeysPresent)
                                "Arquivo importado e validado"
                            else
                                "Necessário para jogos WUD/WUX",
                            good = currentKeysPresent,
                            onClick = onImportKeys
                        )
                        if (keysMessage != null) {
                            Spacer(Modifier.height(12.dp))
                            Text(keysMessage, color = if (currentKeysPresent) WGreen else WRed, fontSize = 13.sp)
                        }
                    }
                    2 -> {
                        SetupTitle("Pasta dos jogos")
                        SetupBody(
                            "Escolha a pasta onde seus jogos Wii U estão ou serão organizados. " +
                                "Ela ficará salva na biblioteca do Wudroid."
                        )
                        Spacer(Modifier.height(20.dp))
                        SetupActionCard(
                            icon = WIcon.Folder,
                            title = "Selecionar pasta",
                            subtitle = if (currentFolderPresent)
                                "${safeGamePaths().size} pasta(s) configurada(s)"
                            else
                                "Nenhuma pasta configurada",
                            good = currentFolderPresent,
                            onClick = onChooseFolder
                        )
                    }
                    else -> {
                        SetupTitle("Tudo pronto")
                        SetupBody(
                            "O Wudroid já pode carregar sua biblioteca. Você pode alterar as chaves, " +
                                "pastas, controles e configurações depois pelo menu."
                        )
                        Spacer(Modifier.height(18.dp))
                        StatusPill("keys.txt", currentKeysPresent, if (currentKeysPresent) "Importada" else "Pular por enquanto")
                        Spacer(Modifier.height(10.dp))
                        StatusPill("Pasta de jogos", currentFolderPresent, if (currentFolderPresent) "Configurada" else "Pode adicionar depois")
                    }
                }
            }

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                if (step > 0) {
                    Button(
                        modifier = Modifier.weight(1f),
                        onClick = { step-- },
                        colors = ButtonDefaults.buttonColors(containerColor = WCard2)
                    ) { Text("Voltar") }
                }
                Button(
                    modifier = Modifier.weight(1f),
                    onClick = {
                        if (step < 3) step++ else onFinish()
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = WBlue)
                ) {
                    Text(if (step < 3) "Continuar" else "Entrar no Wudroid", color = Color.Black)
                }
            }
        }
    }
}

@Composable
private fun SetupTitle(text: String) {
    Text(text, fontSize = 27.sp, fontWeight = FontWeight.Bold)
}

@Composable
private fun SetupBody(text: String) {
    Spacer(Modifier.height(10.dp))
    Text(text, color = WMuted, fontSize = 15.sp, lineHeight = 22.sp)
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
private fun SetupActionCard(
    icon: WIcon,
    title: String,
    subtitle: String,
    good: Boolean,
    onClick: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .combinedClickable(onClick = onClick, onLongClick = {}),
        colors = CardDefaults.cardColors(containerColor = WCard),
        shape = RoundedCornerShape(18.dp)
    ) {
        Row(
            modifier = Modifier.padding(18.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            IconBubble(icon)
            Spacer(Modifier.width(16.dp))
            Column(Modifier.weight(1f)) {
                Text(title, fontWeight = FontWeight.Bold)
                Spacer(Modifier.height(3.dp))
                Text(subtitle, color = WMuted, fontSize = 13.sp)
            }
            WudroidIcon(
                if (good) WIcon.Check else WIcon.Back,
                Modifier.size(24.dp),
                if (good) WGreen else WMuted
            )
        }
    }
}

@Composable
private fun StatusPill(title: String, good: Boolean, detail: String) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(WCard, RoundedCornerShape(14.dp))
            .padding(14.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        WudroidIcon(if (good) WIcon.Check else WIcon.Info, Modifier.size(22.dp), if (good) WGreen else WMuted)
        Spacer(Modifier.width(12.dp))
        Column {
            Text(title, fontWeight = FontWeight.SemiBold)
            Text(detail, color = WMuted, fontSize = 12.sp)
        }
    }
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
private fun LibraryScreen(
    refreshRequest: Int,
    onSettings: () -> Unit,
    onChooseFolder: () -> Unit,
    onGameProfile: (Game) -> Unit,
) {
    val context = LocalContext.current
    val gameListViewModel: GamesListViewModel = viewModel()
    val games by gameListViewModel.games.collectAsState()
    var search by remember { mutableStateOf(TextFieldValue("")) }
    var compact by remember { mutableStateOf(false) }
    var favoritesOnly by remember { mutableStateOf(false) }

    LaunchedEffect(refreshRequest) {
        if (refreshRequest > 0 && gameListViewModel.gamePathsHaveChanged()) {
            // SAF has already returned and the Activity is stable here.
            kotlinx.coroutines.delay(150)
            gameListViewModel.refreshGames()
        }
    }

    val shownGames = remember(games, favoritesOnly) {
        if (favoritesOnly) games.filter { it.isFavorite } else games
    }

    Scaffold(
        contentWindowInsets = WindowInsets.safeDrawing,
        containerColor = WBg,
        floatingActionButton = {
            FloatingActionButton(
                onClick = onChooseFolder,
                containerColor = WBlue,
                contentColor = Color.Black,
                shape = RoundedCornerShape(18.dp)
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 18.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    WudroidIcon(WIcon.Folder, Modifier.size(23.dp), Color.Black)
                    Spacer(Modifier.width(10.dp))
                    Text("Pasta", fontWeight = FontWeight.Bold)
                }
            }
        }
    ) { pad ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(pad)
        ) {
            WudroidTopBar(
                onView = { compact = !compact },
                onFilter = { favoritesOnly = !favoritesOnly },
                onSettings = onSettings,
                filterActive = favoritesOnly
            )

            OutlinedTextField(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 20.dp, vertical = 10.dp),
                value = search,
                onValueChange = {
                    search = it
                    gameListViewModel.setFilterText(it.text)
                },
                leadingIcon = {
                    WudroidIcon(WIcon.Search, Modifier.size(25.dp), WBlue)
                },
                placeholder = { Text("Procurar jogos", color = WMuted) },
                singleLine = true,
                shape = RoundedCornerShape(28.dp)
            )

            if (shownGames.isEmpty()) {
                EmptyLibrary(onChooseFolder)
            } else {
                LazyVerticalGrid(
                    columns = GridCells.Adaptive(if (compact) 115.dp else 150.dp),
                    contentPadding = PaddingValues(18.dp, 14.dp, 18.dp, 110.dp),
                    horizontalArrangement = Arrangement.spacedBy(18.dp),
                    verticalArrangement = Arrangement.spacedBy(20.dp)
                ) {
                    items(shownGames, key = { it.titleId }) { game ->
                        GameTile(
                            game = game,
                            compact = compact,
                            onClick = { startGame(context, game) },
                            onLongClick = { onGameProfile(game) }
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun WudroidTopBar(
    onView: () -> Unit,
    onFilter: () -> Unit,
    onSettings: () -> Unit,
    filterActive: Boolean,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 22.dp, vertical = 16.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Row(
            modifier = Modifier.weight(1f),
            verticalAlignment = Alignment.CenterVertically
        ) {
            WudroidMark(44.dp)
            Spacer(Modifier.width(12.dp))
            Text("Wudroid", fontSize = 28.sp, fontWeight = FontWeight.Bold)
        }
        RoundTopButton(WIcon.View, onView)
        Spacer(Modifier.width(10.dp))
        RoundTopButton(WIcon.Filter, onFilter, active = filterActive)
        Spacer(Modifier.width(10.dp))
        RoundTopButton(WIcon.Settings, onSettings)
    }
}

@Composable
private fun RoundTopButton(icon: WIcon, onClick: () -> Unit, active: Boolean = false) {
    IconButton(
        modifier = Modifier
            .size(48.dp)
            .background(if (active) WBlue.copy(alpha = .16f) else WCard, CircleShape),
        onClick = onClick
    ) {
        WudroidIcon(icon, Modifier.size(25.dp), if (active) WBlue else WText)
    }
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
private fun GameTile(
    game: Game,
    compact: Boolean,
    onClick: () -> Unit,
    onLongClick: () -> Unit
) {
    Column(
        modifier = Modifier.combinedClickable(
            onClick = onClick,
            onLongClick = onLongClick
        )
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(if (compact) 105.dp else 150.dp)
                .background(WCard2, RoundedCornerShape(18.dp)),
            contentAlignment = Alignment.Center
        ) {
            if (game.icon != null) {
                Image(
                    bitmap = game.icon!!,
                    contentDescription = game.name,
                    modifier = Modifier.fillMaxSize(),
                    contentScale = ContentScale.Crop
                )
            } else {
                WudroidIcon(WIcon.Gamepad, Modifier.size(58.dp), WBlue)
            }
            if (game.isFavorite) {
                Box(
                    modifier = Modifier
                        .align(Alignment.TopEnd)
                        .padding(8.dp)
                        .size(28.dp)
                        .background(Color.Black.copy(alpha = .6f), CircleShape),
                    contentAlignment = Alignment.Center
                ) {
                    WudroidIcon(WIcon.Star, Modifier.size(17.dp), WBlue)
                }
            }
        }
        Spacer(Modifier.height(8.dp))
        Text(
            game.name ?: "Jogo",
            fontWeight = FontWeight.Bold,
            fontSize = if (compact) 13.sp else 15.sp,
            maxLines = 2,
            overflow = TextOverflow.Ellipsis
        )
    }
}

@Composable
private fun EmptyLibrary(onChooseFolder: () -> Unit) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(34.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        WudroidIcon(WIcon.Gamepad, Modifier.size(82.dp), WBlue)
        Spacer(Modifier.height(18.dp))
        Text("Sua biblioteca está vazia", fontSize = 22.sp, fontWeight = FontWeight.Bold)
        Spacer(Modifier.height(8.dp))
        Text(
            "Adicione uma pasta com seus jogos Wii U para começar.",
            color = WMuted
        )
        Spacer(Modifier.height(20.dp))
        Button(onClick = onChooseFolder) {
            WudroidIcon(WIcon.Folder, Modifier.size(20.dp), Color.Black)
            Spacer(Modifier.width(8.dp))
            Text("Adicionar pasta", color = Color.Black)
        }
    }
}

@Composable
private fun SettingsScreen(
    onBack: () -> Unit,
    onAdvanced: () -> Unit,
    onControls: () -> Unit,
    onGameFolders: () -> Unit,
    onImportKeys: () -> Unit,
    keysStatus: String,
    onSystemInfo: () -> Unit,
    onAbout: () -> Unit,
) {
    ScreenScaffold("Configurações", onBack) {
        SettingsEntry(
            WIcon.Sliders,
            "Configurações avançadas",
            "Gráficos, shaders, VSync e overlay",
            onAdvanced
        )
        SettingsEntry(
            WIcon.Controller,
            "Controles",
            "GamePad, Pro Controller e controles na tela",
            onControls
        )
        SettingsEntry(
            WIcon.Folder,
            "Gerenciador de jogos",
            "Adicionar ou remover pastas da biblioteca",
            onGameFolders
        )
        SettingsEntry(
            WIcon.Key,
            "Importar keys.txt",
            "Status: $keysStatus • copia para o diretório correto do Wudroid",
            onImportKeys
        )
        SettingsEntry(
            WIcon.Check,
            "Verificar keys.txt",
            if (hasImportedKeys()) "Arquivo encontrado e contém chaves AES-128 válidas" else "Nenhum keys.txt válido encontrado",
            {}
        )
        SettingsEntry(
            WIcon.Info,
            "Informações do sistema",
            "Android, dispositivo, ABI e Vulkan",
            onSystemInfo
        )
        SettingsEntry(
            WIcon.App,
            "Sobre",
            "Wudroid 0.0.8 • frontend independente",
            onAbout
        )
    }
}

@Composable
private fun AdvancedSettingsScreen(onBack: () -> Unit) {
    val context = LocalContext.current
    val graphicsPrefs = remember {
        context.getSharedPreferences(GRAPHICS_PREFS, Context.MODE_PRIVATE)
    }
    var graphicsEngine by remember {
        mutableIntStateOf(
            graphicsPrefs.getInt(GRAPHICS_ENGINE_KEY, GRAPHICS_ENGINE_CEMU_VULKAN)
        )
    }
    var asyncShader by remember { mutableStateOf(safeBool { NativeSettings.getAsyncShaderCompile() }) }
    var accurate by remember { mutableStateOf(safeBool { NativeSettings.getAccurateBarriers() }) }
    var fps by remember { mutableStateOf(safeBool { NativeSettings.isOverlayFPSEnabled() }) }
    var drawCalls by remember { mutableStateOf(safeBool { NativeSettings.isOverlayDrawCallsPerFrameEnabled() }) }
    var cpuUsage by remember { mutableStateOf(safeBool { NativeSettings.isOverlayCPUUsageEnabled() }) }
    var cpuPerCore by remember { mutableStateOf(safeBool { NativeSettings.isOverlayCPUPerCoreUsageEnabled() }) }
    var ramUsage by remember { mutableStateOf(safeBool { NativeSettings.isOverlayRAMUsageEnabled() }) }
    var vramUsage by remember { mutableStateOf(safeBool { NativeSettings.isOverlayVRAMUsageEnabled() }) }
    var overlayDebug by remember { mutableStateOf(safeBool { NativeSettings.isOverlayDebugEnabled() }) }
    var overlayPosition by remember { mutableIntStateOf(safeInt { NativeSettings.getOverlayPosition() }) }
    var overlayScale by remember {
        mutableFloatStateOf(safeInt { NativeSettings.getOverlayTextScalePercentage() }.coerceIn(75, 175).toFloat())
    }
    var vsync by remember { mutableIntStateOf(safeInt { NativeSettings.getVsyncMode() }) }

    fun makeOverlayVisible() {
        if (overlayPosition == NativeSettings.OverlayScreenPosition.DISABLED) {
            overlayPosition = NativeSettings.OverlayScreenPosition.TOP_LEFT
            safeRun { NativeSettings.setOverlayPosition(overlayPosition) }
        }
    }

    fun saveOverlay() {
        safeRun { NativeSettings.saveSettings() }
    }

    ScreenScaffold("Configurações avançadas", onBack) {
        SectionLabel("Motor gráfico")
        ChoiceButtons(
            choices = listOf(
                GRAPHICS_ENGINE_CEMU_VULKAN to "Vulkan padrão",
                GRAPHICS_ENGINE_WUDROID_VULKAN_X to "Vulkan X"
            ),
            selected = graphicsEngine
        ) { engine ->
            graphicsEngine = engine
            graphicsPrefs.edit().putInt(GRAPHICS_ENGINE_KEY, engine).apply()
        }
        Spacer(Modifier.height(8.dp))
        InfoRow(
            "${if (graphicsEngine == GRAPHICS_ENGINE_CEMU_VULKAN) "Vulkan padrão" else "Wudroid Vulkan X"}",
            if (graphicsEngine == GRAPHICS_ENGINE_CEMU_VULKAN)
                "Backend Vulkan atual do Cemu Android. É a opção estável e continua sendo o padrão."
            else
                "Vulkan X v0.1: usa a tradução Latte do Cemu, mas ativa um caminho nativo experimental no renderer Vulkan com scheduler de pipelines conservador e diagnóstico de sessão. Ainda é um primeiro teste."
        )
        Spacer(Modifier.height(12.dp))
        ToggleEntry(
            WIcon.Cpu,
            "Compilação assíncrona de shaders",
            "Reduz travamentos durante a compilação de shaders",
            asyncShader
        ) {
            asyncShader = it
            safeRun { NativeSettings.setAsyncShaderCompile(it); NativeSettings.saveSettings() }
        }
        ToggleEntry(
            WIcon.Display,
            "Barreiras precisas",
            "Pode corrigir bugs gráficos com possível custo de desempenho",
            accurate
        ) {
            accurate = it
            safeRun { NativeSettings.setAccurateBarriers(it); NativeSettings.saveSettings() }
        }
        SectionLabel("Monitor de desempenho")
        InfoRow(
            "Overlay de estatísticas",
            "Mostra dados em tempo real sobre a emulação. Ao ativar qualquer medidor, o Wudroid liga automaticamente o overlay no canto superior esquerdo se ele estiver desativado."
        )
        Spacer(Modifier.height(8.dp))
        ToggleEntry(
            WIcon.View,
            "Mostrar FPS",
            "Frames por segundo durante a emulação",
            fps
        ) {
            fps = it
            if (it) makeOverlayVisible()
            safeRun { NativeSettings.setOverlayFPSEnabled(it) }
            saveOverlay()
        }
        ToggleEntry(
            WIcon.Cpu,
            "Uso de CPU",
            "Percentual de CPU usado pelo processo do emulador",
            cpuUsage
        ) {
            cpuUsage = it
            if (it) makeOverlayVisible()
            safeRun { NativeSettings.setOverlayCPUUsageEnabled(it) }
            saveOverlay()
        }
        ToggleEntry(
            WIcon.Cpu,
            "CPU por núcleo",
            "Mostra a utilização individual dos núcleos do processador",
            cpuPerCore
        ) {
            cpuPerCore = it
            if (it) makeOverlayVisible()
            safeRun { NativeSettings.setOverlayCPUPerCoreUsageEnabled(it) }
            saveOverlay()
        }
        ToggleEntry(
            WIcon.App,
            "Uso de RAM",
            "Memória RAM usada pelo processo do Wudroid",
            ramUsage
        ) {
            ramUsage = it
            if (it) makeOverlayVisible()
            safeRun { NativeSettings.setOverlayRAMUsageEnabled(it) }
            saveOverlay()
        }
        ToggleEntry(
            WIcon.Display,
            "Uso de VRAM",
            "Memória gráfica reportada pelo backend Vulkan quando disponível",
            vramUsage
        ) {
            vramUsage = it
            if (it) makeOverlayVisible()
            safeRun { NativeSettings.setOverlayVRAMUsageEnabled(it) }
            saveOverlay()
        }
        ToggleEntry(
            WIcon.Sliders,
            "Draw calls",
            "Quantidade de chamadas de desenho feitas por frame",
            drawCalls
        ) {
            drawCalls = it
            if (it) makeOverlayVisible()
            safeRun { NativeSettings.setOverlayDrawCallsPerFrameEnabled(it) }
            saveOverlay()
        }
        ToggleEntry(
            WIcon.Info,
            "Debug do renderer",
            "Informações extras do backend gráfico para nossos testes",
            overlayDebug
        ) {
            overlayDebug = it
            if (it) makeOverlayVisible()
            safeRun { NativeSettings.setOverlayDebugEnabled(it) }
            saveOverlay()
        }

        SectionLabel("Posição do monitor")
        ChoiceButtons(
            choices = listOf(
                NativeSettings.OverlayScreenPosition.TOP_LEFT to "Sup. esq.",
                NativeSettings.OverlayScreenPosition.TOP_RIGHT to "Sup. dir."
            ),
            selected = overlayPosition
        ) {
            overlayPosition = it
            safeRun { NativeSettings.setOverlayPosition(it); NativeSettings.saveSettings() }
        }
        Spacer(Modifier.height(8.dp))
        ChoiceButtons(
            choices = listOf(
                NativeSettings.OverlayScreenPosition.BOTTOM_LEFT to "Inf. esq.",
                NativeSettings.OverlayScreenPosition.BOTTOM_RIGHT to "Inf. dir."
            ),
            selected = overlayPosition
        ) {
            overlayPosition = it
            safeRun { NativeSettings.setOverlayPosition(it); NativeSettings.saveSettings() }
        }

        SectionLabel("Tamanho do texto")
        Slider(
            value = overlayScale,
            onValueChange = { overlayScale = it },
            onValueChangeFinished = {
                safeRun {
                    NativeSettings.setOverlayTextScalePercentage(overlayScale.roundToInt())
                    NativeSettings.saveSettings()
                }
            },
            valueRange = 75f..175f
        )
        Text("${overlayScale.roundToInt()}%", color = WMuted, fontSize = 12.sp)

        SectionLabel("VSync")
        ChoiceButtons(
            choices = listOf(
                NativeSettings.VSyncMode.OFF to "Desligado",
                NativeSettings.VSyncMode.DOUBLE_BUFFERING to "Duplo",
                NativeSettings.VSyncMode.TRIPLE_BUFFERING to "Triplo"
            ),
            selected = vsync
        ) {
            vsync = it
            safeRun { NativeSettings.setVsyncMode(it); NativeSettings.saveSettings() }
        }
    }
}

@Composable
private fun ControlsScreen(onBack: () -> Unit) {
    var overlaySettings by remember { mutableStateOf(getOverlaySettings()) }
    var controllerType by remember {
        mutableIntStateOf(
            safeInt {
                if (NativeInput.isControllerDisabled(0))
                    NativeInput.EmulatedControllerType.DISABLED
                else NativeInput.getControllerType(0)
            }
        )
    }
    var alpha by remember { mutableFloatStateOf(overlaySettings.alpha.toFloat()) }

    ScreenScaffold("Controles", onBack) {
        SectionLabel("Controle 1")
        ChoiceButtons(
            choices = listOf(
                NativeInput.EmulatedControllerType.VPAD to "GamePad",
                NativeInput.EmulatedControllerType.PRO to "Pro Controller",
                NativeInput.EmulatedControllerType.DISABLED to "Desativado"
            ),
            selected = controllerType
        ) {
            controllerType = it
            safeRun {
                NativeInput.setControllerType(0, it)
                NativeInput.saveInputs()
                NativeSettings.saveSettings()
            }
            if (it != NativeInput.EmulatedControllerType.DISABLED && !overlaySettings.isOverlayEnabled) {
                overlaySettings = updateOverlaySettings { current ->
                    current.copy(
                        isOverlayEnabled = true,
                        controllerIndex = 0,
                        alpha = maxOf(current.alpha, 150)
                    )
                }
            }
        }

        ToggleEntry(
            WIcon.Gamepad,
            "Controles na tela",
            "Mostra os botões touch durante o jogo",
            overlaySettings.isOverlayEnabled
        ) {
            overlaySettings = updateOverlaySettings { current ->
                current.copy(
                    isOverlayEnabled = it,
                    controllerIndex = 0,
                    alpha = maxOf(current.alpha, 150)
                )
            }
            if (it && safeBool { NativeInput.isControllerDisabled(0) }) {
                safeRun {
                    NativeInput.setControllerType(0, NativeInput.EmulatedControllerType.VPAD)
                    NativeInput.saveInputs()
                }
                controllerType = NativeInput.EmulatedControllerType.VPAD
            }
        }

        ToggleEntry(
            WIcon.Controller,
            "Vibrar ao tocar",
            "Feedback tátil nos botões virtuais",
            overlaySettings.isVibrateOnTouchEnabled
        ) {
            overlaySettings = updateOverlaySettings { current ->
                current.copy(isVibrateOnTouchEnabled = it)
            }
        }

        SectionLabel("Transparência dos botões")
        Slider(
            value = alpha,
            onValueChange = { alpha = it },
            onValueChangeFinished = {
                overlaySettings = updateOverlaySettings { current ->
                    current.copy(alpha = alpha.roundToInt().coerceIn(0, 255))
                }
            },
            valueRange = 30f..255f
        )
        Text("${alpha.roundToInt()}/255", color = WMuted, fontSize = 12.sp)
        Spacer(Modifier.height(8.dp))
        Text(
            "Dica: segure um jogo na biblioteca para definir GamePad ou Pro Controller só para ele.",
            color = WMuted,
            fontSize = 13.sp
        )
    }
}

@Composable
private fun GameFoldersScreen(
    onBack: () -> Unit,
    onAdd: () -> Unit,
    onChanged: () -> Unit,
) {
    var paths by remember { mutableStateOf(safeGamePaths()) }

    ScreenScaffold("Pastas de jogos", onBack) {
        Button(
            modifier = Modifier.fillMaxWidth(),
            onClick = onAdd
        ) {
            WudroidIcon(WIcon.Folder, Modifier.size(20.dp), Color.Black)
            Spacer(Modifier.width(8.dp))
            Text("Adicionar pasta", color = Color.Black)
        }
        Spacer(Modifier.height(12.dp))

        if (paths.isEmpty()) {
            Text("Nenhuma pasta configurada.", color = WMuted)
        } else {
            paths.forEach { path ->
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(containerColor = WCard),
                    shape = RoundedCornerShape(16.dp)
                ) {
                    Row(
                        modifier = Modifier.padding(16.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        WudroidIcon(WIcon.Folder, Modifier.size(23.dp), WBlue)
                        Spacer(Modifier.width(12.dp))
                        Text(
                            path,
                            modifier = Modifier.weight(1f),
                            maxLines = 2,
                            overflow = TextOverflow.Ellipsis,
                            fontSize = 13.sp
                        )
                        IconButton(onClick = {
                            safeRun {
                                NativeSettings.removeGamesPath(path)
                                NativeSettings.saveSettings()
                            }
                            paths = safeGamePaths()
                            onChanged()
                        }) {
                            WudroidIcon(WIcon.Trash, Modifier.size(21.dp), WRed)
                        }
                    }
                }
                Spacer(Modifier.height(9.dp))
            }
        }
    }
}

@Composable
private fun SystemInfoScreen(onBack: () -> Unit) {
    val context = LocalContext.current
    ScreenScaffold("Informações do sistema", onBack) {
        InfoRow("Dispositivo", "${Build.MANUFACTURER} ${Build.MODEL}")
        InfoRow("Android", "${Build.VERSION.RELEASE} (API ${Build.VERSION.SDK_INT})")
        InfoRow("ABI", Build.SUPPORTED_ABIS.joinToString())
        InfoRow("Wudroid", "0.0.8")
        InfoRow("Diretório do usuário", safeString { NativeActiveSettings.getUserDataPath() })
        InfoRow("keys.txt", if (hasImportedKeys()) "Importada" else "Ausente")
        InfoRow("Pastas de jogos", safeGamePaths().size.toString())
    }
}

@Composable
private fun AboutScreen(onBack: () -> Unit) {
    ScreenScaffold("Sobre", onBack) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            WudroidMark(72.dp)
            Spacer(Modifier.width(18.dp))
            Column {
                Text("Wudroid", fontSize = 27.sp, fontWeight = FontWeight.Bold)
                Text("Wii U Emulator for Android", color = WMuted)
                Text("0.0.8", color = WBlue, fontWeight = FontWeight.Bold)
            }
        }
        Spacer(Modifier.height(20.dp))
        Text(
            "Frontend Wudroid independente usando o core de emulação do Cemu. " +
                "A interface, fluxo de configuração, biblioteca e integração Android são do Wudroid.",
            color = WMuted,
            lineHeight = 21.sp
        )
        Spacer(Modifier.height(14.dp))
        Text(
            "keys.txt deve ser obtido do seu próprio Wii U. O Wudroid não distribui chaves, jogos ou firmware.",
            color = WMuted,
            fontSize = 13.sp
        )
    }
}

@Composable
private fun ScreenScaffold(
    title: String,
    onBack: () -> Unit,
    content: @Composable ColumnScope.() -> Unit
) {
    Scaffold(
        contentWindowInsets = WindowInsets.safeDrawing,
        containerColor = WBg
    ) { pad ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(pad)
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 10.dp, vertical = 8.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                IconButton(onClick = onBack) {
                    WudroidIcon(WIcon.Back, Modifier.size(25.dp), WText)
                }
                Text(title, fontSize = 21.sp, fontWeight = FontWeight.Bold)
            }
            LazyColumn(
                modifier = Modifier.fillMaxSize(),
                contentPadding = PaddingValues(18.dp, 8.dp, 18.dp, 36.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                item {
                    Column {
                        content()
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
private fun SettingsEntry(
    icon: WIcon,
    title: String,
    subtitle: String,
    onClick: () -> Unit,
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .combinedClickable(onClick = onClick, onLongClick = {}),
        colors = CardDefaults.cardColors(containerColor = WCard),
        shape = RoundedCornerShape(15.dp)
    ) {
        Row(
            modifier = Modifier.padding(15.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            IconBubble(icon)
            Spacer(Modifier.width(14.dp))
            Column(Modifier.weight(1f)) {
                Text(title, fontWeight = FontWeight.Bold, fontSize = 15.sp)
                Spacer(Modifier.height(2.dp))
                Text(subtitle, color = WMuted, fontSize = 12.sp, lineHeight = 17.sp)
            }
        }
    }
}

@Composable
private fun ToggleEntry(
    icon: WIcon,
    title: String,
    subtitle: String,
    checked: Boolean,
    onChecked: (Boolean) -> Unit,
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = WCard),
        shape = RoundedCornerShape(15.dp)
    ) {
        Row(
            modifier = Modifier.padding(15.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            IconBubble(icon)
            Spacer(Modifier.width(14.dp))
            Column(Modifier.weight(1f)) {
                Text(title, fontWeight = FontWeight.Bold, fontSize = 15.sp)
                Text(subtitle, color = WMuted, fontSize = 12.sp)
            }
            Switch(checked = checked, onCheckedChange = onChecked)
        }
    }
}

@Composable
private fun SectionLabel(text: String) {
    Spacer(Modifier.height(8.dp))
    Text(text, color = WBlue, fontWeight = FontWeight.Bold, fontSize = 13.sp)
    Spacer(Modifier.height(6.dp))
}

@Composable
private fun ChoiceButtons(
    choices: List<Pair<Int, String>>,
    selected: Int,
    onSelected: (Int) -> Unit
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        choices.forEach { (value, label) ->
            Button(
                modifier = Modifier.weight(1f),
                onClick = { onSelected(value) },
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (value == selected) WBlue else WCard2,
                    contentColor = if (value == selected) Color.Black else WText
                ),
                contentPadding = PaddingValues(horizontal = 8.dp, vertical = 10.dp)
            ) {
                Text(label, fontSize = 11.sp, maxLines = 1)
            }
        }
    }
}

@Composable
private fun InfoRow(label: String, value: String) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = WCard),
        shape = RoundedCornerShape(14.dp)
    ) {
        Column(Modifier.padding(15.dp)) {
            Text(label, color = WBlue, fontSize = 12.sp, fontWeight = FontWeight.Bold)
            Spacer(Modifier.height(4.dp))
            Text(value, fontSize = 14.sp)
        }
    }
}

@Composable
private fun IconBubble(icon: WIcon) {
    Box(
        modifier = Modifier
            .size(44.dp)
            .background(WBlue.copy(alpha = .13f), RoundedCornerShape(13.dp)),
        contentAlignment = Alignment.Center
    ) {
        WudroidIcon(icon, Modifier.size(24.dp), WBlue)
    }
}

@Composable
private fun WudroidMark(size: androidx.compose.ui.unit.Dp) {
    Box(
        modifier = Modifier
            .size(size)
            .background(WBlue, RoundedCornerShape(size / 4)),
        contentAlignment = Alignment.Center
    ) {
        Canvas(Modifier.size(size * .65f)) {
            val w = this.size.width
            val h = this.size.height
            val stroke = w * .085f
            drawLine(Color.White, Offset(w*.08f,h*.2f), Offset(w*.28f,h*.82f), stroke, StrokeCap.Round)
            drawLine(Color.White, Offset(w*.28f,h*.82f), Offset(w*.5f,h*.43f), stroke, StrokeCap.Round)
            drawLine(Color.White, Offset(w*.5f,h*.43f), Offset(w*.72f,h*.82f), stroke, StrokeCap.Round)
            drawLine(Color.White, Offset(w*.72f,h*.82f), Offset(w*.92f,h*.2f), stroke, StrokeCap.Round)
            drawCircle(Color.White, w*.055f, Offset(w*.5f,h*.68f))
        }
    }
}

@Composable
private fun WudroidIcon(type: WIcon, modifier: Modifier, color: Color) {
    Canvas(modifier) {
        val w = size.width
        val h = size.height
        val s = minOf(w, h)
        val stroke = s * .085f

        fun line(x1: Float, y1: Float, x2: Float, y2: Float) {
            drawLine(color, Offset(w*x1, h*y1), Offset(w*x2, h*y2), stroke, StrokeCap.Round)
        }
        when (type) {
            WIcon.Search -> {
                drawCircle(color, s*.29f, Offset(w*.43f,h*.43f), style=Stroke(stroke))
                line(.63f,.63f,.88f,.88f)
            }
            WIcon.Settings -> {
                drawCircle(color, s*.17f, Offset(w*.5f,h*.5f), style=Stroke(stroke))
                for (i in 0 until 8) {
                    val a = Math.PI * 2 * i / 8
                    val cx = .5f + kotlin.math.cos(a).toFloat()*.34f
                    val cy = .5f + kotlin.math.sin(a).toFloat()*.34f
                    drawCircle(color, s*.07f, Offset(w*cx,h*cy))
                }
            }
            WIcon.View -> {
                drawRoundRect(color, Offset(w*.12f,h*.18f), Size(w*.76f,h*.64f), CornerRadius(s*.12f), style=Stroke(stroke))
                drawLine(color, Offset(w*.5f,h*.18f), Offset(w*.5f,h*.82f), stroke)
                drawLine(color, Offset(w*.12f,h*.5f), Offset(w*.88f,h*.5f), stroke)
            }
            WIcon.Filter -> {
                line(.18f,.25f,.82f,.25f); line(.30f,.50f,.70f,.50f); line(.42f,.75f,.58f,.75f)
            }
            WIcon.Folder -> {
                val p = Path()
                p.moveTo(w*.12f,h*.32f); p.lineTo(w*.4f,h*.32f); p.lineTo(w*.49f,h*.22f)
                p.lineTo(w*.88f,h*.22f); p.lineTo(w*.88f,h*.78f); p.lineTo(w*.12f,h*.78f); p.close()
                drawPath(p,color,style=Stroke(stroke))
            }
            WIcon.Gamepad, WIcon.Controller -> {
                drawRoundRect(color, Offset(w*.12f,h*.30f), Size(w*.76f,h*.46f), CornerRadius(s*.18f), style=Stroke(stroke))
                line(.28f,.47f,.28f,.64f); line(.20f,.555f,.36f,.555f)
                drawCircle(color,s*.045f,Offset(w*.68f,h*.50f))
                drawCircle(color,s*.045f,Offset(w*.77f,h*.60f))
            }
            WIcon.Key -> {
                drawCircle(color,s*.18f,Offset(w*.32f,h*.38f),style=Stroke(stroke))
                line(.45f,.51f,.84f,.83f); line(.68f,.70f,.78f,.60f); line(.76f,.77f,.86f,.67f)
            }
            WIcon.Cpu -> {
                drawRoundRect(color,Offset(w*.27f,h*.27f),Size(w*.46f,h*.46f),CornerRadius(s*.08f),style=Stroke(stroke))
                for (i in 0..3) {
                    val p=.32f+i*.12f
                    line(p,.10f,p,.24f); line(p,.76f,p,.90f); line(.10f,p,.24f,p); line(.76f,p,.90f,p)
                }
            }
            WIcon.App -> {
                drawRoundRect(color,Offset(w*.20f,h*.14f),Size(w*.60f,h*.72f),CornerRadius(s*.16f),style=Stroke(stroke))
                drawCircle(color,s*.035f,Offset(w*.5f,h*.75f))
            }
            WIcon.Check -> {
                line(.18f,.52f,.40f,.74f); line(.40f,.74f,.84f,.24f)
            }
            WIcon.Info -> {
                drawCircle(color,s*.36f,Offset(w*.5f,h*.5f),style=Stroke(stroke))
                line(.5f,.44f,.5f,.70f)
                drawCircle(color,s*.045f,Offset(w*.5f,h*.28f))
            }
            WIcon.Back -> {
                line(.72f,.18f,.30f,.50f); line(.30f,.50f,.72f,.82f)
            }
            WIcon.Audio -> {
                val p=Path(); p.moveTo(w*.18f,h*.43f); p.lineTo(w*.36f,h*.43f); p.lineTo(w*.56f,h*.25f)
                p.lineTo(w*.56f,h*.75f); p.lineTo(w*.36f,h*.57f); p.lineTo(w*.18f,h*.57f); p.close()
                drawPath(p,color,style=Stroke(stroke)); line(.66f,.38f,.78f,.27f); line(.66f,.62f,.78f,.73f)
            }
            WIcon.Display -> {
                drawRoundRect(color,Offset(w*.12f,h*.18f),Size(w*.76f,h*.54f),CornerRadius(s*.08f),style=Stroke(stroke))
                line(.38f,.82f,.62f,.82f); line(.50f,.72f,.50f,.82f)
            }
            WIcon.Trash -> {
                drawRoundRect(color,Offset(w*.27f,h*.28f),Size(w*.46f,h*.58f),CornerRadius(s*.05f),style=Stroke(stroke))
                line(.20f,.24f,.80f,.24f); line(.38f,.15f,.62f,.15f)
            }
            WIcon.Star -> {
                val p=Path()
                val pts = listOf(
                    .50f to .10f, .61f to .37f, .90f to .39f, .68f to .57f, .76f to .86f,
                    .50f to .69f, .24f to .86f, .32f to .57f, .10f to .39f, .39f to .37f
                )
                p.moveTo(w*pts[0].first,h*pts[0].second)
                pts.drop(1).forEach{p.lineTo(w*it.first,h*it.second)}; p.close()
                drawPath(p,color,style=Stroke(stroke))
            }
            WIcon.Play -> {
                val p=Path(); p.moveTo(w*.30f,h*.18f); p.lineTo(w*.80f,h*.50f); p.lineTo(w*.30f,h*.82f); p.close()
                drawPath(p,color)
            }
            WIcon.Sliders -> {
                line(.18f,.27f,.82f,.27f); line(.18f,.50f,.82f,.50f); line(.18f,.73f,.82f,.73f)
                drawCircle(color,s*.06f,Offset(w*.38f,h*.27f)); drawCircle(color,s*.06f,Offset(w*.65f,h*.50f)); drawCircle(color,s*.06f,Offset(w*.48f,h*.73f))
            }
        }
    }
}

@Composable
private fun GameProfileDialog(
    game: Game,
    onDismiss: () -> Unit,
    onPlay: () -> Unit
) {
    val context = LocalContext.current
    val prefs = remember {
        context.getSharedPreferences(GAME_PROFILE_PREFS, Context.MODE_PRIVATE)
    }
    val defaultType = safeInt {
        if (NativeInput.isControllerDisabled(0)) NativeInput.EmulatedControllerType.VPAD
        else NativeInput.getControllerType(0)
    }
    var controller by remember {
        mutableIntStateOf(prefs.getInt("controller_${game.titleId}", defaultType))
    }
    var cpuMode by remember {
        mutableIntStateOf(safeInt { NativeGameTitles.getCpuModeForTitle(game.titleId) })
    }
    var favorite by remember { mutableStateOf(game.isFavorite) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text(game.name ?: "Perfil do jogo") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text("Controle deste jogo", color = WBlue, fontWeight = FontWeight.Bold)
                ChoiceButtons(
                    choices = listOf(
                        NativeInput.EmulatedControllerType.VPAD to "GamePad",
                        NativeInput.EmulatedControllerType.PRO to "Pro"
                    ),
                    selected = controller
                ) {
                    controller = it
                    prefs.edit().putInt("controller_${game.titleId}", it).apply()
                }

                Text("CPU", color = WBlue, fontWeight = FontWeight.Bold)
                ChoiceButtons(
                    choices = listOf(
                        NativeGameTitles.CPUMode.AUTO to "Auto",
                        NativeGameTitles.CPUMode.SINGLECORERECOMPILER to "1 núcleo",
                        NativeGameTitles.CPUMode.MULTICORERECOMPILER to "Multi"
                    ),
                    selected = cpuMode
                ) {
                    cpuMode = it
                    safeRun { NativeGameTitles.setCpuModeForTitle(game.titleId, it) }
                }

                Row(verticalAlignment = Alignment.CenterVertically) {
                    Checkbox(
                        checked = favorite,
                        onCheckedChange = {
                            favorite = it
                            safeRun { NativeGameTitles.setGameTitleFavorite(game.titleId, it) }
                        }
                    )
                    Text("Favorito")
                }

                Button(
                    modifier = Modifier.fillMaxWidth(),
                    onClick = {
                        safeRun { NativeGameTitles.removeShaderCacheFilesForTitle(game.titleId) }
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = WCard2)
                ) {
                    Text("Limpar shader cache")
                }
            }
        },
        confirmButton = {
            Button(onClick = {
                prefs.edit().putInt("controller_${game.titleId}", controller).apply()
                safeRun { NativeSettings.saveSettings() }
                onPlay()
            }) {
                WudroidIcon(WIcon.Play, Modifier.size(18.dp), Color.Black)
                Spacer(Modifier.width(7.dp))
                Text("Jogar", color = Color.Black)
            }
        },
        dismissButton = {
            Button(
                onClick = onDismiss,
                colors = ButtonDefaults.buttonColors(containerColor = WCard2)
            ) { Text("Fechar") }
        }
    )
}

private fun startGame(context: Context, game: Game) {
    val path = game.path ?: return

    // Old Wudroid builds could enable FPS while leaving Cemu's overlay position
    // at Disabled, which makes every selected statistic invisible. Repair that
    // state automatically when launching a game.
    safeRun {
        val anyPerformanceStatEnabled =
            NativeSettings.isOverlayFPSEnabled() ||
            NativeSettings.isOverlayDrawCallsPerFrameEnabled() ||
            NativeSettings.isOverlayCPUUsageEnabled() ||
            NativeSettings.isOverlayCPUPerCoreUsageEnabled() ||
            NativeSettings.isOverlayRAMUsageEnabled() ||
            NativeSettings.isOverlayVRAMUsageEnabled() ||
            NativeSettings.isOverlayDebugEnabled()
        if (anyPerformanceStatEnabled &&
            NativeSettings.getOverlayPosition() == NativeSettings.OverlayScreenPosition.DISABLED
        ) {
            NativeSettings.setOverlayPosition(NativeSettings.OverlayScreenPosition.TOP_LEFT)
            NativeSettings.saveSettings()
        }
    }

    if ((path.endsWith(".wud", true) || path.endsWith(".wux", true)) && !hasImportedKeys()) {
        Toast.makeText(
            context,
            "Este formato precisa de keys.txt. Importe suas próprias chaves em Configurações.",
            Toast.LENGTH_LONG
        ).show()
        return
    }

    val prefs = context.getSharedPreferences(GAME_PROFILE_PREFS, Context.MODE_PRIVATE)
    val controllerType = prefs.getInt(
        "controller_${game.titleId}",
        NativeInput.EmulatedControllerType.VPAD
    )

    safeRun {
        NativeInput.setControllerType(0, controllerType)
        NativeInput.saveInputs()
        updateOverlaySettings { current ->
            current.copy(
                controllerIndex = 0,
                isOverlayEnabled = true,
                alpha = maxOf(current.alpha, 150),
            )
        }
        NativeSettings.saveSettings()
    }

    val graphicsEngine = context
        .getSharedPreferences(GRAPHICS_PREFS, Context.MODE_PRIVATE)
        .getInt(GRAPHICS_ENGINE_KEY, GRAPHICS_ENGINE_CEMU_VULKAN)

    Intent(context, EmulationActivity::class.java).apply {
        action = Intent.ACTION_VIEW
        putExtra(EmulationActivity.EXTRA_LAUNCH_PATH, path)
        putExtra("wudroid.graphics_engine", graphicsEngine)
        if (path.startsWith("content://")) {
            val uri = Uri.parse(path)
            data = uri
            clipData = ClipData.newRawUri("wiiu-game", uri)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        context.startActivity(this)
    }
}

private fun addGameFolder(context: Context, uri: Uri): Boolean {
    return try {
        val grantedFlags =
            Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION

        context.contentResolver.takePersistableUriPermission(uri, grantedFlags)

        // Match the Android port's own GamePathsScreen behavior.
        val documentFile = DocumentFile.fromTreeUri(context, uri)
            ?: run {
                Toast.makeText(context, "Não foi possível acessar essa pasta.", Toast.LENGTH_LONG).show()
                return false
            }

        val gamesPath = documentFile.uri.toString()
        if (safeGamePaths().contains(gamesPath)) {
            Toast.makeText(context, "Essa pasta já está na biblioteca.", Toast.LENGTH_SHORT).show()
            return false
        }

        NativeSettings.addGamesPath(gamesPath)

        // Important: do NOT call saveSettings()/reloadGameTitles() in this SAF callback.
        // The Activity/ViewModel handles refresh after returning from the picker.
        Toast.makeText(context, "Pasta adicionada.", Toast.LENGTH_SHORT).show()
        true
    } catch (t: Throwable) {
        Toast.makeText(
            context,
            "Falha ao adicionar pasta: ${t.javaClass.simpleName}",
            Toast.LENGTH_LONG
        ).show()
        false
    }
}

private fun importKeysFile(context: Context, uri: Uri): Pair<Boolean, String> {
    return try {
        val bytes = context.contentResolver.openInputStream(uri)?.use { it.readBytes() }
            ?: return false to "Não foi possível ler o arquivo."

        val text = bytes.toString(Charsets.UTF_8)
        val validKeyRegex = Regex("(?i)(^|[^0-9a-f])[0-9a-f]{32}([^0-9a-f]|$)")
        if (!validKeyRegex.containsMatchIn(text)) {
            return false to "O arquivo não parece conter nenhuma chave AES-128 válida de 32 caracteres hexadecimais."
        }

        val userDir = File(NativeActiveSettings.getUserDataPath())
        userDir.mkdirs()
        val target = File(userDir, "keys.txt")
        target.writeBytes(bytes)

        true to "keys.txt importado para o diretório do Wudroid. Se você trocar as chaves depois de iniciar um jogo, feche e abra o app para recarregá-las."
    } catch (t: Throwable) {
        false to "Falha ao importar keys.txt: ${t.javaClass.simpleName}"
    }
}

private fun hasImportedKeys(): Boolean {
    return try {
        val file = File(NativeActiveSettings.getUserDataPath(), "keys.txt")
        if (!file.isFile || file.length() == 0L) return false
        val text = file.readText()
        Regex("(?i)(^|[^0-9a-f])[0-9a-f]{32}([^0-9a-f]|$)").containsMatchIn(text)
    } catch (_: Throwable) {
        false
    }
}

private fun getOverlaySettings(): InputOverlaySettings =
    try {
        runBlocking {
            AppSettingsStore.dataStore.data.first().inputOverlaySettings
        }
    } catch (_: Throwable) {
        InputOverlaySettings()
    }

private fun updateOverlaySettings(
    transform: (InputOverlaySettings) -> InputOverlaySettings
): InputOverlaySettings =
    try {
        runBlocking {
            var updated = InputOverlaySettings()
            AppSettingsStore.dataStore.updateData { appSettings ->
                updated = transform(appSettings.inputOverlaySettings)
                appSettings.copy(inputOverlaySettings = updated)
            }
            updated
        }
    } catch (_: Throwable) {
        getOverlaySettings()
    }

private fun safeGamePaths(): List<String> =
    try { NativeSettings.getGamesPaths().toList() } catch (_: Throwable) { emptyList() }

private inline fun safeRun(block: () -> Unit) {
    try { block() } catch (_: Throwable) {}
}

private inline fun safeBool(block: () -> Boolean): Boolean =
    try { block() } catch (_: Throwable) { false }

private inline fun safeInt(block: () -> Int): Int =
    try { block() } catch (_: Throwable) { 0 }

private inline fun safeString(block: () -> String): String =
    try { block() } catch (_: Throwable) { "Indisponível" }
