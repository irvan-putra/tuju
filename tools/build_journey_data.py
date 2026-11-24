#!/usr/bin/env python3
"""Generate the journey meter's leg/stop list in index.html from data/*.json.

The meter (the journey-meter card near the top of index.html) times a ride
between two stops on one leg and compares it with what the operator's data
says: straight-line stop-to-stop distance from GTFS stop coordinates, and
scheduled minutes for the outbound patterns whose GTFS trips are referenced
in data/route-stops.json. Return legs and 4D have no referenced trip, so
their schedule stays unmeasured; every leg gets coordinates (exact stop_id
for outbound, same-station name centroid otherwise - platforms sit within
~90 m). No invented figures: what the feed does not cover is reported as
not measured.

    tools/build_journey_data.py           splice the list into index.html
    tools/build_journey_data.py --check   fail if the committed block is stale

Only the var TUJU_SEGMENTS assignment between the journey-segments markers is
rewritten; everything around it is written directly in source.
"""
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
INDEX = os.path.join(ROOT, "index.html")

BEGIN = "journey-segments:begin"
END = "journey-segments:end"

NAME_ALIASES = {
    # Rider-confirmed same station, 19 Nov 2026 (7E return terminus naming).
    "Department of Agriculture Busway Shelter": "Simpang Ragunan Ar-Raudhah",
}


def norm(name):
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def centroid(points):
    return [round(sum(p["lat"] for p in points) / len(points), 6),
            round(sum(p["lon"] for p in points) / len(points), 6)]


def legs(route_segments, return_segments, extract):
    out = []
    stops_by_id = extract["stops"]
    name_points = extract["name_points"]
    trip_minutes = extract["trip_minutes"]

    def coords_by_name(name):
        pts = name_points.get(norm(NAME_ALIASES.get(name, name)))
        return centroid(pts) if pts else None

    for seg in route_segments:
        coords = []
        for s in seg["stops"]:
            rec = stops_by_id.get(s["id"])
            coords.append([rec["lat"], rec["lon"]] if rec else None)
        sched = None
        trip = seg.get("trip")
        if trip and trip in trip_minutes:
            tm = trip_minutes[trip]
            minutes = [tm.get(s["id"]) for s in seg["stops"]]
            if all(m is not None for m in minutes):
                sched = [m - minutes[0] for m in minutes]
        out.append({
            "label": "%s toward %s" % (seg["route"], seg["direction"]),
            "stops": [s["name"] for s in seg["stops"]],
            "coords": None if None in coords else coords,
            "sched": sched,
        })

    for seg in return_segments:
        coords = [coords_by_name(n) for n in seg["stops"]]
        out.append({
            "label": "%s return: %s - %s" % (seg["route"], seg["stops"][0], seg["stops"][-1]),
            "stops": list(seg["stops"]),
            "coords": None if None in coords else coords,
            "sched": None,
        })
    return out


def block(all_legs):
    lines = ["var TUJU_SEGMENTS = ["]
    for i, leg in enumerate(all_legs):
        lines.append("  %s%s" % (json.dumps(leg, ensure_ascii=False),
                                 "," if i + 1 < len(all_legs) else ""))
    lines.append("];")
    return "\n".join(lines)


def splice(text, new_block):
    pattern = re.compile(
        r"(/\*\s*" + BEGIN + r".*?\*/\s*)var TUJU_SEGMENTS = .*?;(\s*/\*\s*" + END + r"\s*\*/)",
        re.S)
    if not pattern.search(text):
        sys.exit("journey-segments markers not found in index.html")
    return pattern.sub(lambda m: m.group(1) + new_block + m.group(2), text)


def load(name):
    with open(os.path.join(ROOT, "data", name), encoding="utf-8") as f:
        return json.load(f)


def main():
    all_legs = legs(load("route-stops.json")["segments"],
                    load("return-stops.json")["segments"],
                    load("gtfs-extract.json"))
    unmeasured = [l["label"] for l in all_legs if not l["coords"]]
    if unmeasured:
        print("legs without coordinates:", unmeasured)
    with open(INDEX, encoding="utf-8") as f:
        text = f.read()
    updated = splice(text, block(all_legs))
    if "--check" in sys.argv:
        if updated != text:
            sys.exit("journey segment list is stale; run tools/build_journey_data.py")
        print("journey segment list is up to date")
        return
    with open(INDEX, "w", encoding="utf-8") as f:
        f.write(updated)
    print("wrote", os.path.relpath(INDEX, ROOT))


if __name__ == "__main__":
    main()
