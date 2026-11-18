# tuju app

The combined busway-route overview map from https://vanipy.com/tuju/ as an
offline Android app screen: pinch to zoom, drag to pan, nothing else. No
permissions, no network - the map SVG is bundled in the app.

- Package: `com.vanipy.tuju`, launcher name `tuju`
- Version: `android/app/build.gradle.kts` (`appVersionName`, major.minor.revision)

## Map asset

`app/src/main/assets/map.html` is generated from the combined "all routes at
a glance" SVG in the repo-root `index.html`:

    python3 tools/build_map_asset.py          # regenerate after index.html changes
    python3 tools/build_map_asset.py --check  # CI freshness check

The release workflow fails if the committed asset is stale.

## Icons

    pip install pillow==12.3.0
    python3 tools/badge_icon.py 0.1.0

## Build and release

Debug build and unit tests:

    ./gradlew --no-daemon testDebugUnitTest assembleDebug

Signed release: dispatch the "tuju signed release" workflow. It needs the
`TUJU_KEYSTORE_B64`, `TUJU_STORE_PASSWORD`, `TUJU_KEY_ALIAS` and
`TUJU_KEY_PASSWORD` repository secrets and publishes a GitHub pre-release
with the APK and its SHA-256.

The "tuju emulator smoke test" workflow runs on pushes to `android/**` and
installs the debug APK on an emulator, verifies the map WebView renders and
uploads screenshots.
