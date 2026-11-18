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
        assertTrue("asset must contain the combined 560-wide map svg",
                Pattern.compile("<svg viewBox=\"0 0 560 \\d+\"").matcher(html).find());
        assertFalse("asset must stay offline: no scripts, no external URLs",
                html.contains("<script") || html.contains("http://") || html.contains("https://"));
    }

    @Test
    public void activityShowsBundledMapWithPinchZoom() {
        MainActivity activity = Robolectric.buildActivity(MainActivity.class).create().get();
        ViewGroup root = (ViewGroup) activity.findViewById(android.R.id.content);
        WebView web = (WebView) root.getChildAt(0);
        assertNotNull(web);
        assertTrue(web.getSettings().getSupportZoom());
        assertTrue(web.getSettings().getBuiltInZoomControls());
        assertFalse(web.getSettings().getDisplayZoomControls());
        assertTrue(web.getSettings().getUseWideViewPort());
        assertTrue(web.getSettings().getLoadWithOverviewMode());
        assertFalse(web.getSettings().getJavaScriptEnabled());
    }
}
