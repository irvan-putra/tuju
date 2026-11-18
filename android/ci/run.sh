#!/usr/bin/env bash
set -euo pipefail
adb install -r app/build/outputs/apk/debug/tuju-v*-debug.apk
python3 ci/smoke.py
