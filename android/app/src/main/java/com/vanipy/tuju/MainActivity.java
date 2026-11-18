package com.vanipy.tuju;

import android.app.Activity;
import android.os.Bundle;
import android.webkit.WebSettings;
import android.webkit.WebView;

/**
 * The whole app is one offline map: the combined busway-route overview from
 * tuju's index.html, bundled as a WebView asset. Pinch to zoom, drag to pan;
 * no cards, no controls, no network.
 */
public class MainActivity extends Activity {
    private WebView web;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        web = new WebView(this);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(false); // the map is static SVG; no script needed
        s.setSupportZoom(true);
        s.setBuiltInZoomControls(true);
        s.setDisplayZoomControls(false); // pinch only, no on-screen buttons
        s.setUseWideViewPort(true);
        s.setLoadWithOverviewMode(true); // start fit-to-screen
        setContentView(web);
        web.loadUrl("file:///android_asset/map.html");
    }

    @Override
    public void onBackPressed() {
        if (web != null && web.canGoBack()) {
            web.goBack();
        } else {
            super.onBackPressed();
        }
    }
}
