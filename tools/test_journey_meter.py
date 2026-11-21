#!/usr/bin/env python3
"""Unit tests for the journey meter's pure logic, run under node.

Extracts the inline <script> of the journey-meter card from index.html and
checks the helpers with synthetic coordinates and times only - no real
location data ever appears here. Needs node on PATH (GitHub's runners have
it); skips with a warning where node is missing.
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HARNESS = r"""
const m = require(process.argv[2]);
let failures = 0;
function ok(cond, msg) { if (!cond) { failures++; console.error("FAIL: " + msg); } }
function near(a, b, tol, msg) { ok(Math.abs(a - b) <= tol, msg + " (got " + a + ", want ~" + b + ")"); }

ok(Array.isArray(m.segments) && m.segments.length >= 10, "segments present");
ok(m.segments.every(s => s.label && Array.isArray(s.stops) && s.stops.length >= 2),
   "every leg has a label and at least two stops");

near(m.haversineMeters(0, 0, 1, 0), 111195, 200, "one degree latitude");
near(m.haversineMeters(-6.175, 106.865, -6.176, 106.865), 110.8, 2, "111 m south at Jakarta latitude");

// GPS steps: first fix seeds, bad fixes and jumps are dropped.
const a = { lat: -6.175, lon: 106.865, accuracyM: 12, timeMs: 100000 };
const b = { lat: -6.1759, lon: 106.865, accuracyM: 12, timeMs: 130000 };   // ~100 m in 30 s
const bad = { lat: -6.2, lon: 106.9, accuracyM: 12, timeMs: 131000 };      // teleport jump
const jitter = { lat: -6.175901, lon: 106.865001, accuracyM: 12, timeMs: 160000 };
const coarse = { lat: -6.176, lon: 106.865, accuracyM: 80, timeMs: 190000 };
ok(m.gpsStepMeters(null, a) === 0, "first fix only seeds");
near(m.gpsStepMeters(a, b), 100, 5, "normal step counts");
ok(m.gpsStepMeters(b, bad) === 0, "teleport jump rejected");
ok(m.gpsStepMeters(b, jitter) === 0, "sub-5 m jitter rejected");
ok(m.gpsStepMeters(b, coarse) === 0, "coarse fix rejected");
ok(m.gpsStepMeters(b, { lat: -6.176, lon: 106.865, accuracyM: 12, timeMs: 100000 }) === 0,
   "non-positive time step rejected");

// Synthetic two-hop leg: ~111 m + ~100 m straight-line, 6 scheduled minutes.
const seg = { label: "synthetic", stops: ["A", "B", "C"],
  coords: [[-6.175, 106.865], [-6.176, 106.865], [-6.1769, 106.865]],
  sched: [0, 4, 6] };
const e2 = m.estimateForSegment(seg, 0, 2);
ok(e2.hops === 2, "two hops");
near(e2.km, 0.211, 0.01, "straight-line km is the sum of stop-to-stop steps");
ok(e2.minutes === 6, "scheduled minutes come from the feed, both directions");
ok(m.estimateForSegment(seg, 2, 0).minutes === 6, "reverse selection same estimate");
ok(m.formatEstimate(e2).includes("2 hops") && m.formatEstimate(e2).includes("straight-line"),
   "estimate text names hops and grounded distance");
const bare = { label: "bare", stops: ["A", "B"], coords: null, sched: null };
const eb = m.estimateForSegment(bare, 0, 1);
ok(eb.km === null && eb.minutes === null, "uncovered leg stays unmeasured");
ok(m.formatEstimate(eb).includes("not measured"), "uncovered leg says not measured");
ok(m.formatEstimate(m.estimateForSegment(seg, 1, 1)).includes("different stops"), "zero-hop guidance");
// Real embedded segments: every leg reports grounded or honestly unmeasured.
ok(m.segments.every(s => (s.coords && s.coords.length === s.stops.length) || s.coords === null),
   "coords cover all stops or are null");
ok(m.segments.every(s => s.sched === null || (s.sched.length === s.stops.length && s.sched[0] === 0)),
   "schedules are cumulative from the leg start or null");

ok(m.formatClock(0) === "0:00", "clock zero");
ok(m.formatClock(65000) === "1:05", "clock minutes");
ok(m.formatClock(3725000) === "1:02:05", "clock hours");
ok(m.formatKm(1234) === "1.23 km", "km formatting");

if (failures) { console.error(failures + " journey-meter assertion(s) failed"); process.exit(1); }
console.log("journey-meter logic ok: " + m.segments.length + " legs, helpers verified");
"""


def main():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    m = re.search(r"<!-- journey-meter:begin[^>]*-->.*?<script>(.*?)</script>", html, re.S)
    if not m:
        sys.exit("journey meter script not found in index.html")
    node = shutil.which("node")
    if not node:
        print("WARNING: node not found; journey meter logic tests skipped")
        return
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / "meter.js"
        harness = Path(tmp) / "harness.js"
        script.write_text(m.group(1), encoding="utf-8")
        harness.write_text(HARNESS, encoding="utf-8")
        subprocess.run([node, "--check", str(script)], check=True)
        subprocess.run([node, str(harness), str(script)], check=True)


if __name__ == "__main__":
    main()
