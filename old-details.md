# Old details (pre-2026-11-24 refresh)

Archived on 2026-11-24 before the repo-details refresh. Current details are in
README.md and the repo metadata.

## About description (before)

(none)

## Website field (before)

(none)

## README.md (before)

```markdown
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

```

## Refresh outcome

The README was already convention-compliant (English, leads with the project,
honest limits, live link, AGPL, no personal data), so the refresh made no
README changes. The .sha256 sidecar wording stays because the latest release
still publishes it.

## Second pass (2026-11-24, later)

At the owner's request the start area was taken off the public repo details:
the About description and the README intro no longer name it. The map's
coverage is unchanged; the site copy is separate site content.

## Third pass (2026-11-24, later)

At the owner's request the start area was also taken off the live site: page
title, subtitle, map start label, route schematics and notes now say "the
start area" / "Start area", and four source links whose URLs or text named it
were dropped. Destinations and official stop names (Simpang Pramuka, Pramuka
BPKP, Pramuka Sari) are unchanged. The generator, the bundled Android map
asset and the experiment SVGs were updated together so they stay in sync.
