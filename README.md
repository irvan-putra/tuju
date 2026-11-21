# tuju

Offline TransJakarta busway-route overview map, made for trips from the
Green Pramuka area. One screen: pinch to zoom, drag to pan, plus a journey
meter (ride timer with stop-to-stop estimate, optional GPS distance).

- **Web:** `index.html`, published at https://vanipy.com/tuju/
- **Android:** `android/` wraps the same map and meter as an offline app
  (`com.vanipy.tuju`). Everything is bundled; the app has no network
  permission. Location is asked only if you switch the meter's GPS distance
  on, and is used only while the screen is open. Signed with the tuju key;
  every release pins the expected signing certificate in `release.yml`.
- **Map data:** `data/` plus the generators and consistency tests in
  `tools/` (`build_map_asset.py`, `build_journey_data.py`, `test_route_map.py`,
  `test_journey_meter.py`). Stop lists come from
  the TransJakarta operator GTFS; the 4D branch list is from jaGOdetabek
  and halte.id. Route patterns and temporary stops can change - this is an
  overview map, not live arrival information.

Releases are GitHub pre-releases carrying `tuju-vX.Y.Z.apk` and its
`.sha256` sidecar, and are listed on the family gallery at
https://vanipy.com/kaji/apk/.

License: AGPL-3.0 (see LICENSE).
