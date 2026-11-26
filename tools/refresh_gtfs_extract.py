#!/usr/bin/env python3
"""Refresh the GTFS extract the journey meter measures against.

Downloads the TransJakarta operator GTFS feed and writes
data/gtfs-extract.json: the coordinates of every stop the meter's legs use,
and per-trip scheduled minutes at those stops for the outbound patterns in
data/route-stops.json. Committed as a dated snapshot (same convention as
data/route-stops.json) so the meter never needs the network.

    tools/refresh_gtfs_extract.py   # download and rewrite data/gtfs-extract.json

Review the diff before committing: a feed update moves stops or re-times
patterns. Coordinates for name-only legs (return-stops.json, 4D) are matched
by normalized stop name; same-station platforms sit within ~90 m of each
other, so their centroid is used. "Department of Agriculture Busway Shelter"
is the rider-confirmed same station as Simpang Ragunan Ar-Raudhah (see
data/all-stops.svg) and is aliased to it.
"""
import csv
import hashlib
import io
import json
import os
import re
import sys
import urllib.request
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
FEED_URL = "https://gtfs.transjakarta.co.id/files/file_gtfs.zip"
OUT = os.path.join(ROOT, "data", "gtfs-extract.json")

NAME_ALIASES = {
    # Rider-confirmed same station, 19 Nov 2026 (7E return terminus naming).
    "Department of Agriculture Busway Shelter": "Simpang Ragunan Ar-Raudhah",
}


def norm(name):
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def load_feed():
    with urllib.request.urlopen(FEED_URL, timeout=60) as r:
        blob = r.read()
    zf = zipfile.ZipFile(io.BytesIO(blob))

    def table(name):
        with zf.open(name) as f:
            return list(csv.DictReader(io.TextIOWrapper(f, "utf-8-sig")))

    return hashlib.sha256(blob).hexdigest(), table


def main():
    with open(os.path.join(ROOT, "data", "route-stops.json"), encoding="utf-8") as f:
        outbound = json.load(f)["segments"]
    with open(os.path.join(ROOT, "data", "return-stops.json"), encoding="utf-8") as f:
        returning = json.load(f)["segments"]

    wanted_ids = {s["id"] for seg in outbound for s in seg["stops"]}
    wanted_names = {norm(NAME_ALIASES.get(n, n)) for seg in returning for n in seg["stops"]}
    wanted_names |= {norm(s["name"]) for seg in outbound for s in seg["stops"]}
    wanted_trips = {seg["trip"] for seg in outbound if seg.get("trip")}

    sha, table = load_feed()
    stops_rows = table("stops.txt")

    stops = {}
    by_name = {}
    for r in stops_rows:
        point = {"lat": float(r["stop_lat"]), "lon": float(r["stop_lon"])}
        if r["stop_id"] in wanted_ids:
            stops[r["stop_id"]] = {"name": r["stop_name"], **point}
        key = norm(r["stop_name"])
        if key in wanted_names:
            by_name.setdefault(key, []).append(point)

    # Scheduled minutes from trip start per stop, for the referenced patterns.
    trips = {}
    stop_times = {}
    for r in table("stop_times.txt"):
        if r["trip_id"] in wanted_trips:
            stop_times.setdefault(r["trip_id"], []).append(r)
    for trip_id, rows in stop_times.items():
        rows.sort(key=lambda r: int(r["stop_sequence"]))

        def minutes(r):
            h, m, _ = r["departure_time"].split(":")
            return int(h) * 60 + int(m)

        t0 = minutes(rows[0])
        trips[trip_id] = {r["stop_id"]: minutes(r) - t0 for r in rows}

    extract = {
        "source": FEED_URL,
        "checked": "2026-11-26",
        "feed_sha256": sha,
        "stops": stops,
        "name_points": {k: v for k, v in sorted(by_name.items())},
        "trip_minutes": trips,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(extract, f, indent=1, sort_keys=True)
        f.write("\n")
    missing_ids = wanted_ids - set(stops)
    missing_names = wanted_names - set(by_name)
    print("wrote", os.path.relpath(OUT, ROOT),
          "(%d stops, %d names, %d trips)" % (len(stops), len(by_name), len(trips)))
    if missing_ids or missing_names:
        print("MISSING ids:", sorted(missing_ids))
        print("MISSING names:", sorted(missing_names))
        sys.exit(1)


if __name__ == "__main__":
    main()
