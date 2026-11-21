# tuju app

The combined busway-route overview map from https://vanipy.com/tuju/ as an
offline Android app screen: pinch to zoom, drag to pan, with the journey
meter below the map. No network - the map and meter are bundled in the app.
The only permission is location, requested at runtime and only if the rider
switches the meter's GPS distance on; it tracks only while the screen is
open and nothing leaves the device.

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
    python3 tools/badge_icon.py 0.2.0

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


## 0.1.6 combined network

The two Arkadia homebound options are integrated into the top network, with independently sourced directional stop sequences and upward homebound arrows. The shared outbound 4/4D trunk and other destinations remain. Ragunan boarding/fare continuity, conflicting 7F hours, and Gojek access/fare/time caveats remain visible. Same package and pinned signing certificate; no phone installation or data reset.
