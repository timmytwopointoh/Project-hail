package com.trioncompasitor.riftward;

import android.app.Activity;
import android.content.res.Configuration;
import android.graphics.Color;
import android.os.Bundle;
import android.util.Log;
import android.view.WindowManager;
import android.webkit.ConsoleMessage;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

public final class MainActivity extends Activity {
    private WebView game;

    @Override public void onCreate(Bundle bundle) {
        super.onCreate(bundle);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN, WindowManager.LayoutParams.FLAG_FULLSCREEN);
        game = new WebView(this);
        game.setBackgroundColor(Color.rgb(5, 8, 20));
        WebSettings settings = game.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setDefaultTextEncodingName("UTF-8");
        game.setWebViewClient(new WebViewClient());
        game.setWebChromeClient(new WebChromeClient() {
            @Override public boolean onConsoleMessage(ConsoleMessage m) {
                if (m.message().startsWith("RIFTWARD_STATE:")) {
                    Log.i("RIFTWARD_STATE", m.message());
                } else if (m.messageLevel() == ConsoleMessage.MessageLevel.ERROR) {
                    Log.e("RIFTWARD_WEB_ERROR", m.message());
                }
                return false;
            }
        });
        setContentView(game);
        game.loadUrl("file:///android_asset/index.html");
    }

    @Override @SuppressWarnings("deprecation") public void onBackPressed() {
        if (game == null) { super.onBackPressed(); return; }
        game.evaluateJavascript("window.Riftward && window.Riftward.back ? window.Riftward.back() : false", response -> {
            if (!"true".equals(response)) runOnUiThread(() -> MainActivity.super.onBackPressed());
        });
    }

    @Override public void onConfigurationChanged(Configuration configuration) {
        super.onConfigurationChanged(configuration);
        if (game != null) game.evaluateJavascript("window.dispatchEvent(new Event('resize'))", null);
    }

    @Override protected void onPause() {
        super.onPause();
        if (game != null) game.evaluateJavascript("window.Riftward && window.Riftward.suspend && window.Riftward.suspend()", null);
    }

    @Override protected void onDestroy() {
        if (game != null) { game.destroy(); game = null; }
        super.onDestroy();
    }
}
