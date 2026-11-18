#!/usr/bin/env bash
cd "$(dirname "$0")/.." 
set -euo pipefail
adb install -r app/build/outputs/apk/debug/tuju-v*-debug.apk
python3 ci/smoke.py

adb install -r app/build/outputs/apk/androidTest/debug/*-androidTest.apk
adb shell am instrument -w -r -e class com.vanipy.tuju.MapGestureTest com.vanipy.tuju.test/android.test.InstrumentationTestRunner | tee ci/shots/gesture-result.txt
grep -q 'OK (1 test)' ci/shots/gesture-result.txt
adb pull /sdcard/Download/tuju-map-zoom.png ci/shots/map-zoom.png
adb pull /sdcard/Download/tuju-map-pan.png ci/shots/map-pan.png
