#!/usr/bin/env python3
"""Generate the journey meter's leg/stop list in index.html from data/*.json.

The meter (the journey-meter card near the top of index.html) lets a rider
time a ride between two stops on one leg. Its leg list is generated from the
same stop snapshots the map uses, so the picker can never drift from the map:

    tools/build_journey_data.py           splice the list into index.html
    tools/build_journey_data.py --check   fail if the committed block is stale

Only the var TUJU_SEGMENTS assignment between the journey-segments markers is
rewritten; everything around it is hand-written.
"""
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
INDEX = os.path.join(ROOT, "index.html")

BEGIN = "journey-segments:begin"
END = "journey-segments:end"


def legs():
    out = []
    with open(os.path.join(ROOT, "data", "route-stops.json"), encoding="utf-8") as f:
        for seg in json.load(f)["segments"]:
            out.append({
                "label": "%s toward %s" % (seg["route"], seg["direction"]),
                "stops": [s["name"] for s in seg["stops"]],
            })
    with open(os.path.join(ROOT, "data", "return-stops.json"), encoding="utf-8") as f:
        for seg in json.load(f)["segments"]:
            out.append({
                "label": "%s return: %s - %s" % (seg["route"], seg["stops"][0], seg["stops"][-1]),
                "stops": list(seg["stops"]),
            })
    return out


def block():
    lines = ["var TUJU_SEGMENTS = ["]
    items = legs()
    for i, leg in enumerate(items):
        lines.append("  %s%s" % (json.dumps(leg, ensure_ascii=False),
                                 "," if i + 1 < len(items) else ""))
    lines.append("];")
    return "\n".join(lines)


def splice(text, new_block):
    pattern = re.compile(
        r"(/\*\s*" + BEGIN + r".*?\*/\s*)var TUJU_SEGMENTS = .*?;(\s*/\*\s*" + END + r"\s*\*/)",
        re.S)
    if not pattern.search(text):
        sys.exit("journey-segments markers not found in index.html")
    return pattern.sub(lambda m: m.group(1) + new_block + m.group(2), text)


def main():
    with open(INDEX, encoding="utf-8") as f:
        text = f.read()
    updated = splice(text, block())
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
