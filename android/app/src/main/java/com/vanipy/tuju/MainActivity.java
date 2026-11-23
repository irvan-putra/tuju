package com.vanipy.tuju;

import android.app.Activity;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.webkit.GeolocationPermissions;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;

/**
 * The app is one offline screen: the combined busway-route overview map from
 * tuju's index.html, plus the journey meter below it (ride timer, stop picker,
 * optional GPS distance), bundled as a WebView asset. Pinch to zoom, drag to
 * pan; no network.
 *
 * Script is enabled for the meter. Location is requested at runtime and only
 * when the rider switches GPS distance on in the page: the WebView's
 * geolocation prompt is what triggers the Android permission ask. Nothing is
 * tracked in the background; leaving or closing the screen stops it.
 */
public class MainActivity extends Activity {
    private static final int REQ_LOCATION = 1;

    private WebView web;
    private String pendingOrigin;
    private GeolocationPermissions.Callback pendingCallback;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        web = new WebView(this);
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true); // the journey meter is script-driven
        s.setDomStorageEnabled(true); // the walk-review screen keeps its answers on-device
        s.setSupportZoom(true);
        s.setBuiltInZoomControls(true);
        s.setDisplayZoomControls(false); // pinch only, no on-screen buttons
        s.setUseWideViewPort(true);
        s.setLoadWithOverviewMode(true); // start fit-to-screen
        web.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onGeolocationPermissionsShowPrompt(String origin,
                    GeolocationPermissions.Callback callback) {
                if (hasLocationPermission()) {
                    callback.invoke(origin, true, false);
                } else {
                    pendingOrigin = origin;
                    pendingCallback = callback;
                    requestPermissions(new String[]{
                            android.Manifest.permission.ACCESS_FINE_LOCATION,
                            android.Manifest.permission.ACCESS_COARSE_LOCATION}, REQ_LOCATION);
                }
            }
        });
        setContentView(web);
        web.loadUrl("file:///android_asset/map.html");
    }

    private boolean hasLocationPermission() {
        return checkSelfPermission(android.Manifest.permission.ACCESS_FINE_LOCATION)
                == PackageManager.PERMISSION_GRANTED
                || checkSelfPermission(android.Manifest.permission.ACCESS_COARSE_LOCATION)
                == PackageManager.PERMISSION_GRANTED;
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions,
            int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == REQ_LOCATION && pendingCallback != null) {
            boolean granted = false;
            for (int result : grantResults) {
                granted |= result == PackageManager.PERMISSION_GRANTED;
            }
            pendingCallback.invoke(pendingOrigin, granted, false);
            pendingOrigin = null;
            pendingCallback = null;
        }
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
