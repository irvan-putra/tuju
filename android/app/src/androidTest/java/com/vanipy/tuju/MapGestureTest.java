package com.vanipy.tuju;

import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import org.junit.Test;
import org.junit.runner.RunWith;
import static org.junit.Assert.assertTrue;
import android.os.SystemClock;
import android.view.InputDevice;
import android.view.MotionEvent;
import android.webkit.WebView;

/** Debug-only device test: real two-pointer pinch events, then a drag. */
@SuppressWarnings("deprecation")
@RunWith(AndroidJUnit4.class)
public class MapGestureTest {
    private android.app.Instrumentation getInstrumentation() { return InstrumentationRegistry.getInstrumentation(); }

    private float scale(WebView web) {
        final float[] value = new float[1];
        getInstrumentation().runOnMainSync(() -> value[0] = web.getScale());
        return value[0];
    }
    private void touch(long start, int action, float x1, float y1, float x2, float y2, int count) {
        MotionEvent.PointerProperties[] props = new MotionEvent.PointerProperties[count];
        MotionEvent.PointerCoords[] coords = new MotionEvent.PointerCoords[count];
        for (int i = 0; i < count; i++) {
            props[i] = new MotionEvent.PointerProperties();
            props[i].id = i;
            props[i].toolType = MotionEvent.TOOL_TYPE_FINGER;
            coords[i] = new MotionEvent.PointerCoords();
            coords[i].x = i == 0 ? x1 : x2;
            coords[i].y = i == 0 ? y1 : y2;
            coords[i].pressure = 1;
            coords[i].size = 1;
        }
        MotionEvent event = MotionEvent.obtain(start, SystemClock.uptimeMillis(), action,
                count, props, coords, 0, 0, 1, 1, 0, 0, InputDevice.SOURCE_TOUCHSCREEN, 0);
        getInstrumentation().sendPointerSync(event);
        event.recycle();
    }

    @Test
    public void testPinchAndPan() throws Exception {
        android.content.Intent launch = new android.content.Intent(getInstrumentation().getTargetContext(), MainActivity.class);
        launch.addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK);
        MainActivity activity = (MainActivity) getInstrumentation().startActivitySync(launch);
        getInstrumentation().waitForIdleSync();
        Thread.sleep(1500);
        WebView web = (WebView) ((android.view.ViewGroup) activity.findViewById(android.R.id.content)).getChildAt(0);
        float before = scale(web);
        int[] position = new int[2];
        web.getLocationOnScreen(position);
        float cx = position[0] + web.getWidth() * .38f;
        float cy = position[1] + web.getHeight() * .35f;
        long t = SystemClock.uptimeMillis();
        touch(t, MotionEvent.ACTION_DOWN, cx-25, cy, 0, 0, 1);
        touch(t, MotionEvent.ACTION_POINTER_DOWN | (1 << MotionEvent.ACTION_POINTER_INDEX_SHIFT), cx-25, cy, cx+25, cy, 2);
        for (int i=1; i<=24; i++) {
            float span=25+i*6;
            touch(t, MotionEvent.ACTION_MOVE, cx-span, cy-i*4, cx+span, cy+i*4, 2);
            SystemClock.sleep(24);
        }
        touch(t, MotionEvent.ACTION_POINTER_UP | (1 << MotionEvent.ACTION_POINTER_INDEX_SHIFT), cx-169, cy-96, cx+169, cy+96, 2);
        touch(t, MotionEvent.ACTION_UP, cx-169, cy-96, 0, 0, 1);
        Thread.sleep(800);
        assertTrue("Pinch must enlarge actual WebView scale", scale(web) > before * 1.5f);
        getInstrumentation().getUiAutomation().takeScreenshot().compress(android.graphics.Bitmap.CompressFormat.PNG,100,new java.io.FileOutputStream(new java.io.File(activity.getExternalFilesDir(null), "map-zoom.png")));
        // Drag the zoomed map and record resulting pixels.
        int oldX=web.getScrollX(), oldY=web.getScrollY();
        t=SystemClock.uptimeMillis();
        touch(t,MotionEvent.ACTION_DOWN,cx,cy,0,0,1);
        for(int i=1;i<=20;i++) {
            touch(t,MotionEvent.ACTION_MOVE,cx-i*5,cy-i*12,0,0,1);
            SystemClock.sleep(24);
        }
        touch(t,MotionEvent.ACTION_UP,cx-100,cy-240,0,0,1);
        Thread.sleep(700);
        assertTrue("Drag must move the enlarged map",web.getScrollX()!=oldX || web.getScrollY()!=oldY);
        getInstrumentation().getUiAutomation().takeScreenshot().compress(android.graphics.Bitmap.CompressFormat.PNG,100,new java.io.FileOutputStream(new java.io.File(activity.getExternalFilesDir(null), "map-pan.png")));

        // Inspect the changed homebound content in the real Android WebView.
        String bundled = new String(getInstrumentation().getTargetContext().getAssets().open("map.html").readAllBytes(), java.nio.charset.StandardCharsets.UTF_8);
        assertTrue(bundled.contains("Going home from Arkadia"));
        assertTrue(bundled.contains("Gojek to Flyover Raya Bogor"));
        assertTrue(bundled.contains("Flyover Kuningan"));
        getInstrumentation().runOnMainSync(() -> web.zoomBy((before * 2.1f) / web.getScale()));
        Thread.sleep(800);
        assertTrue("Return capture must remain zoomed", scale(web) > before * 1.5f);
        final float svgPixels = web.getWidth() * scale(web) / (1700f * before);
        getInstrumentation().runOnMainSync(() -> web.scrollTo((int)(0*svgPixels),(int)(3368*svgPixels)));
        Thread.sleep(600);
        getInstrumentation().getUiAutomation().takeScreenshot().compress(android.graphics.Bitmap.CompressFormat.PNG,100,new java.io.FileOutputStream(new java.io.File(activity.getExternalFilesDir(null), "return-a.png")));
        getInstrumentation().runOnMainSync(() -> web.scrollTo((int)(830*svgPixels),(int)(3368*svgPixels)));
        Thread.sleep(600);
        getInstrumentation().getUiAutomation().takeScreenshot().compress(android.graphics.Bitmap.CompressFormat.PNG,100,new java.io.FileOutputStream(new java.io.File(activity.getExternalFilesDir(null), "return-b.png")));
        getInstrumentation().runOnMainSync(() -> web.scrollTo((int)(0*svgPixels),(int)(4228*svgPixels)));
        Thread.sleep(600);
        getInstrumentation().getUiAutomation().takeScreenshot().compress(android.graphics.Bitmap.CompressFormat.PNG,100,new java.io.FileOutputStream(new java.io.File(activity.getExternalFilesDir(null), "return-a-middle.png")));
        getInstrumentation().runOnMainSync(() -> web.scrollTo((int)(0*svgPixels),(int)(5128*svgPixels)));
        Thread.sleep(600);
        getInstrumentation().getUiAutomation().takeScreenshot().compress(android.graphics.Bitmap.CompressFormat.PNG,100,new java.io.FileOutputStream(new java.io.File(activity.getExternalFilesDir(null), "return-a-bottom.png")));
    }
}
