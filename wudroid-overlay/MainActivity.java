package info.cemu.cemu;

import android.content.ClipData;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.webkit.JavascriptInterface;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.core.view.WindowInsetsControllerCompat;

import info.cemu.cemu.emulation.EmulationActivity;
import info.cemu.cemu.nativeinterface.NativeSettings;

public class MainActivity extends AppCompatActivity {
    private static final int REQUEST_OPEN_GAME = 7001;
    private WebView webView;
    private FrameLayout root;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        WudroidBootstrap.applyFirstRunDefaults(this);

        WindowCompat.setDecorFitsSystemWindows(getWindow(), false);
        getWindow().setStatusBarColor(Color.TRANSPARENT);
        getWindow().setNavigationBarColor(Color.TRANSPARENT);

        WindowInsetsControllerCompat bars = WindowCompat.getInsetsController(
                getWindow(), getWindow().getDecorView());
        bars.setAppearanceLightStatusBars(true);
        bars.setAppearanceLightNavigationBars(true);

        root = new FrameLayout(this);
        root.setBackgroundColor(Color.WHITE);

        webView = new WebView(this);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        settings.setTextZoom(100);

        webView.setWebViewClient(new WebViewClient());
        webView.setBackgroundColor(Color.WHITE);
        webView.setOverScrollMode(View.OVER_SCROLL_NEVER);
        webView.addJavascriptInterface(new WudroidBridge(), "WudroidNative");

        root.addView(webView, new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT));
        setContentView(root);

        ViewCompat.setOnApplyWindowInsetsListener(root, (view, windowInsets) -> {
            Insets safe = windowInsets.getInsets(
                    WindowInsetsCompat.Type.statusBars()
                            | WindowInsetsCompat.Type.navigationBars()
                            | WindowInsetsCompat.Type.displayCutout());
            view.setPadding(safe.left, safe.top, safe.right, safe.bottom);
            return WindowInsetsCompat.CONSUMED;
        });
        ViewCompat.requestApplyInsets(root);

        webView.loadUrl("file:///android_asset/index.html");
    }

    @Override
    protected void onPause() {
        super.onPause();
        NativeSettings.saveSettings();
    }

    private void openGamePicker() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("*/*");
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION
                | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
        startActivityForResult(intent, REQUEST_OPEN_GAME);
    }

    private void launch(Class<?> activity) {
        startActivity(new Intent(this, activity));
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != REQUEST_OPEN_GAME || resultCode != RESULT_OK
                || data == null || data.getData() == null) {
            return;
        }

        Uri uri = data.getData();
        int takeFlags = data.getFlags() &
                (Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
        try {
            getContentResolver().takePersistableUriPermission(uri, takeFlags);
        } catch (SecurityException ignored) {}

        try {
            NativeSettings.saveSettings();
            Intent emulationIntent = new Intent(this, EmulationActivity.class);
            emulationIntent.setAction(Intent.ACTION_VIEW);
            emulationIntent.putExtra(EmulationActivity.EXTRA_LAUNCH_PATH, uri.toString());
            emulationIntent.setData(uri);
            emulationIntent.setClipData(ClipData.newRawUri("wiiu-game", uri));
            emulationIntent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            startActivity(emulationIntent);
        } catch (Throwable t) {
            Toast.makeText(this,
                    "Falha ao iniciar a emulação: " + t.getClass().getSimpleName(),
                    Toast.LENGTH_LONG).show();
        }
    }

    public final class WudroidBridge {
        @JavascriptInterface public void openGame() {
            runOnUiThread(MainActivity.this::openGamePicker);
        }
        @JavascriptInterface public void openSettings() {
            runOnUiThread(() -> launch(WudroidSettingsActivity.class));
        }
        @JavascriptInterface public void openGameFolders() {
            runOnUiThread(() -> launch(WudroidGamePathsActivity.class));
        }
        @JavascriptInterface public void openTouchSettings() {
            runOnUiThread(() -> launch(WudroidTouchSettingsActivity.class));
        }
        @JavascriptInterface public void openLibraryManager() {
            runOnUiThread(() -> launch(WudroidManagerActivity.class));
        }
        @JavascriptInterface public String coreStatus() {
            return "Cemu Android core loaded";
        }
        @JavascriptInterface public String version() {
            return "0.0.7";
        }
    }
}
