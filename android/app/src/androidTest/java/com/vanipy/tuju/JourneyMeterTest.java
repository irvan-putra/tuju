package com.vanipy.tuju;

import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import org.junit.Test;
import org.junit.runner.RunWith;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;
import android.content.Intent;
import android.webkit.WebView;

/**
 * Debug-only device test for the journey meter: drives the real DOM in the
 * app's WebView. Synthetic interactions only; GPS is exercised as a toggle
 * (the fix itself is not simulated here - the distance math is unit-tested
 * in tools/test_journey_meter.py with synthetic coordinates). Location
 * permission is pre-granted by ci/run.sh so the geolocation prompt is
 * answered by the app without a system dialog.
 */
@RunWith(AndroidJUnit4.class)
public class JourneyMeterTest {
    private android.app.Instrumentation instrumentation() {
        return InstrumentationRegistry.getInstrumentation();
    }

    private String js(WebView web, String expr) throws Exception {
        java.util.concurrent.CountDownLatch done = new java.util.concurrent.CountDownLatch(1);
        final String[] out = new String[1];
        instrumentation().runOnMainSync(() -> web.evaluateJavascript(expr, result -> {
            out[0] = result == null ? "" : result.replaceAll("^\"|\"$", "").replace("\\\"", "\"");
            done.countDown();
        }));
        assertTrue("JS evaluation timed out", done.await(5, java.util.concurrent.TimeUnit.SECONDS));
        return out[0];
    }

    @Test
    public void meterTimesJourneyAndGpsToggleIsSafe() throws Exception {
        Intent intent = new Intent(instrumentation().getTargetContext(), MainActivity.class);
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        MainActivity activity = (MainActivity) instrumentation().startActivitySync(intent);
        // The WebView is the activity's only content view.
        android.view.ViewGroup root = (android.view.ViewGroup) activity.findViewById(android.R.id.content);
        WebView web = (WebView) root.getChildAt(0);

        // The meter lives on its own page now (the Meter tab).
        final WebView navWeb = web;
        instrumentation().runOnMainSync(() -> navWeb.loadUrl("file:///android_asset/meter/index.html"));
        // Wait for the bundled page and its meter script to finish loading.
        String ready = "";
        for (int i = 0; i < 40; i++) {
            ready = js(web, "document.readyState + '@' + location.href + ':' + (document.getElementById('jm-leg') ? document.getElementById('jm-leg').options.length : -1)");
            if (ready.startsWith("complete@") && !ready.endsWith(":-1") && !ready.endsWith(":0")) break;
            Thread.sleep(500);
        }
        final WebView webView = web;
        assertTrue("meter did not initialize, last state: " + ready,
                ready.startsWith("complete@") && !ready.endsWith(":-1") && !ready.endsWith(":0"));

        // Pick leg 0, from stop 0 to stop 2, and read the estimate.
        String est = js(webView,
                "var l=document.getElementById('jm-leg');l.value='0';l.dispatchEvent(new Event('change'));"
              + "var f=document.getElementById('jm-from');f.value='0';f.dispatchEvent(new Event('change'));"
              + "var t=document.getElementById('jm-to');t.value='2';t.dispatchEvent(new Event('change'));"
              + "document.getElementById('jm-estimate').textContent");
        assertTrue("estimate should mention 2 hops, got: " + est, est.contains("2 hops"));

        // Run a short journey and stop it.
        js(webView, "document.getElementById('jm-start').click();'started'");
        Thread.sleep(2100);
        String elapsed = js(webView, "document.getElementById('jm-elapsed').textContent");
        assertFalse("timer should be running", elapsed.contains("not started"));
        String result = js(webView, "document.getElementById('jm-stop').click();document.getElementById('jm-result').textContent");
        assertTrue("result should report the stop, got: " + result, result.contains("Stopped"));
        assertTrue("result should compare with the operator data, got: " + result,
                result.contains("scheduled") || result.contains("no operator estimate"));

        // GPS toggle on and off: no crash, and the status line answers.
        String on = js(webView, "var g=document.getElementById('jm-gps');g.click();document.getElementById('jm-gps-status').textContent");
        assertTrue("GPS status should answer, got: " + on, on.length() > 0);
        String off = js(webView, "var g=document.getElementById('jm-gps');g.click();document.getElementById('jm-gps-status').textContent");
        assertTrue("GPS off status, got: " + off, off.contains("GPS off"));
    }
}
