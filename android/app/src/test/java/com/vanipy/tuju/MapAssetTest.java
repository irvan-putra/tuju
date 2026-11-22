package com.vanipy.tuju;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

import android.view.ViewGroup;
import android.webkit.WebView;

import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.Robolectric;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.regex.Pattern;

@RunWith(RobolectricTestRunner.class)
@Config(sdk = 34)
public class MapAssetTest {

    private static String readAsset(MainActivity activity, String name) throws Exception {
        try (InputStream in = activity.getAssets().open(name)) {
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            byte[] buf = new byte[8192];
            int n;
            while ((n = in.read(buf)) != -1) {
                out.write(buf, 0, n);
            }
            return new String(out.toByteArray(), StandardCharsets.UTF_8);
        }
    }

    @Test
    public void mapAssetIsTheCombinedOverviewMap() throws Exception {
        MainActivity activity = Robolectric.buildActivity(MainActivity.class).get();
        String html = readAsset(activity, "map.html");
        assertTrue("asset must contain the combined 4200-wide map svg",
                Pattern.compile("<svg viewBox=\"0 0 4200 \\d+\"").matcher(html).find());
    }

    @Test
    public void mapAssetCarriesTheJourneyMeter() throws Exception {
        MainActivity activity = Robolectric.buildActivity(MainActivity.class).get();
        String html = readAsset(activity, "map.html");
        assertTrue("asset must contain the journey meter card",
                html.contains("id=\"journey-meter\""));
        assertTrue("asset must contain the generated leg list",
                html.contains("var TUJU_SEGMENTS = [") && html.contains("toward"));
    }

    @Test
    public void mapAssetCarriesTheAccessGuideline() throws Exception {
        MainActivity activity = Robolectric.buildActivity(MainActivity.class).get();
        String html = readAsset(activity, "map.html");
        assertTrue("asset must contain the IDSW access guideline card",
                html.contains("id=\"access-guideline\""));
        assertTrue("asset must carry the Car Free Day warning",
                html.contains("Car Free Day"));
    }

    @Test
    public void mapAssetStaysOnDeviceOnly() throws Exception {
        MainActivity activity = Robolectric.buildActivity(MainActivity.class).get();
        String html = readAsset(activity, "map.html");
        // The journey meter runs an inline script, but everything stays on the
        // device: no external resources, no network calls of any kind.
        assertFalse("no external URLs",
                Pattern.compile("(?:src|href)\\s*=\\s*\"https?://").matcher(html).find());
        for (String call : new String[]{"fetch(", "XMLHttpRequest", "WebSocket",
                "sendBeacon", "import("}) {
            assertFalse("no network call " + call, html.contains(call));
        }
    }

    @Test
    public void activityShowsBundledMapWithPinchZoom() {
        MainActivity activity = Robolectric.buildActivity(MainActivity.class).create().get();
        ViewGroup root = (ViewGroup) activity.findViewById(android.R.id.content);
        WebView web = (WebView) root.getChildAt(0);
        assertNotNull(web);
        assertTrue(web.getSettings().getBuiltInZoomControls());
        assertFalse(web.getSettings().getDisplayZoomControls());
        assertTrue(web.getSettings().getUseWideViewPort());
        assertTrue(web.getSettings().getLoadWithOverviewMode());
        assertTrue("the journey meter needs script", web.getSettings().getJavaScriptEnabled());
    }
}
