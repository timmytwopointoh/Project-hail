package com.trioncompasitor.matrixflap;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.os.Bundle;
import android.util.Log;
import android.view.WindowManager;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

public final class MainActivity extends Activity {
    public static final String INSPECT = "com.trioncompasitor.matrixflap.INSPECT";
    private WebView game;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN,
                WindowManager.LayoutParams.FLAG_FULLSCREEN);
        game = new WebView(this);
        game.setBackgroundColor(Color.rgb(4, 6, 16));
        WebSettings settings = game.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setDefaultTextEncodingName("UTF-8");
        game.setWebViewClient(new WebViewClient());
        setContentView(game);
        game.loadUrl("file:///android_asset/index.html");
    }

    @Override protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        if (INSPECT.equals(intent.getAction())) {
            game.evaluateJavascript(
                "JSON.stringify(window.matrixFlapStatus ? window.matrixFlapStatus() : {state:'unavailable'})",
                value -> Log.i("MATRIX_FLAP_STATUS", value)
            );
        }
    }

    @Override protected void onDestroy() {
        if (game != null) {
            game.destroy();
            game = null;
        }
        super.onDestroy();
    }
}
