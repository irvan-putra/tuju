# tuju

Offline TransJakarta busway-route overview map, made for trips from the
Green Pramuka area. One screen: pinch to zoom, drag to pan, nothing else.

- **Web:** `index.html`, published at https://vanipy.com/tuju/
- **Android:** `android/` wraps the same map as an offline app
  (`com.vanipy.tuju`). The map is bundled; the app uses no network and
  requests no permissions. Signed with the tuju key; every release pins the
  expected signing certificate in `release.yml`.
- **Map data:** `data/` plus the generators and consistency tests in
  `tools/` (`build_map_asset.py`, `test_route_map.py`). Stop lists come from
  the TransJakarta operator GTFS; the 4D branch list is from jaGOdetabek
  and halte.id. Route patterns and temporary stops can change - this is an
  overview map, not live arrival information.

Releases are GitHub pre-releases carrying `tuju-vX.Y.Z.apk` and its
`.sha256` sidecar, and are listed on the family gallery at
https://vanipy.com/kaji/apk/.

License: AGPL-3.0 (see LICENSE).
