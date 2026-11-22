#!/usr/bin/env bash
cd "$(dirname "$0")/.." 
set -euo pipefail
adb install -r app/build/outputs/apk/debug/tuju-v*-debug.apk
python3 ci/smoke.py

adb shell pm grant com.vanipy.tuju android.permission.ACCESS_FINE_LOCATION
adb shell pm grant com.vanipy.tuju android.permission.ACCESS_COARSE_LOCATION
adb install -r app/build/outputs/apk/androidTest/debug/*-androidTest.apk
adb shell am instrument -w -r -e class com.vanipy.tuju.MapGestureTest,com.vanipy.tuju.JourneyMeterTest com.vanipy.tuju.test/androidx.test.runner.AndroidJUnitRunner | tee ci/shots/gesture-result.txt
grep -q 'OK (2 tests)' ci/shots/gesture-result.txt
adb pull /sdcard/Android/data/com.vanipy.tuju/files/map-zoom.png ci/shots/map-zoom.png
adb pull /sdcard/Android/data/com.vanipy.tuju/files/map-pan.png ci/shots/map-pan.png

for name in return-a return-b return-a-middle return-a-bottom grand-indonesia breeze-bsd alam-sutera mall-extension; do
  adb pull /sdcard/Android/data/com.vanipy.tuju/files/$name.png ci/shots/$name.png
done
