# Map-layout proposals (from the kaji map-layout research note)

Approved 2026-11-23, implemented as three dependency-free tools. They measure
and search; they do not change the hand-placed layout on their own. The map
SVG a build writes is byte-identical with or without them.

## 1. Measure first: `score_route_map.py`

Every build now prints one line:

    layout score: crossings=3 bends=40 min_gap=9.5 text_overlaps=23

- `crossings`: line crossings away from stops and endpoints, the same rule
  `map_bridges.py` uses to place hop marks, so the count and the drawn hops
  tell one story.
- `bends`: corners over all drawn lines after simplification.
- `min_gap`: closest approach of two different-coloured lines, ignoring joins
  at stops, meeting endpoints and crossing pairs (those count under
  `crossings`).
- `text_overlaps`: text boxes a line passes through or touches, using the
  estimated real widths from `check_text_clearance.py` (wrapped notes
  included).

Run it standalone: `python3 tools/score_route_map.py [--json]`. Lower is
better; any future layout engine has this number to beat.

## 2. Route walking links by search: `route_walk_links.py`

A* on a coarse grid: label boxes are blocked cells (inflated by a margin),
drawn lines cost a crossing charge to pass, every turn costs a bend charge.
Returns an orthogonal polyline, the same style the hand-drawn walks use.

    python3 tools/route_walk_links.py X1 Y1 X2 Y2 [--cell N]

prints the SVG `d` for the link. Not wired into the generator yet: adopting it
for a specific walk means swapping that walk's hand-drawn path for the routed
one and checking the score goes down. Opt in per link so ongoing manual fixes
are not clobbered.

## 3. Pack columns by search: `pack_columns.py`

Each corridor is a block with a fixed size and named ports; links join ports.
Simulated annealing over block (x, y) positions inside a fixed page width,
minimising total link length + bend cost + a large penalty for a link crossing
a third block. `python3 tools/pack_columns.py example.json` (format in the
module docstring). Final routing of an adopted layout would use proposal 2
against the real label boxes; the L-route cost here is the search objective.

Tests for all three: `python3 tools/test_layout_proposals.py`.
