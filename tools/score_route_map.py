"""Proposal 1 (measure first): one layout score for the generated map, printed
on every build so a change is measured, not eyeballed. Components:
  crossings     - line crossings away from stops and endpoints (same rule the
                  hop marker in map_bridges uses; the hops stay drawn)
  bends         - corners over all drawn lines after simplification
  min_gap       - smallest clearance between lines of different colours,
                  excluding joins at stops, endpoints and crossing pairs
  text_overlaps - text boxes a line passes through or touches (real estimated
                  widths, wrapped notes included, as in check_text_clearance)
Usage: python3 tools/score_route_map.py [--json] [svg-path]   (exit 0 always)
"""
import json, sys
from pathlib import Path
import map_geometry as G

def crossings(scene):
    """Crossing count with the same exclusions map_bridges applies for hops."""
    paths, nodes = scene.paths, scene.nodes
    found = []
    for j, (_sj, bp) in enumerate(paths):
        for _si, ap in paths[:j]:
            for a, b in zip(ap, ap[1:]):
                for c, d in zip(bp, bp[1:]):
                    r = b-a; s = d-c; den = G.cross(r, s)
                    if abs(den) < 1e-6: continue
                    q = G.seg_intersection(a, b, c, d)
                    if q is None: continue
                    if min(abs(q-v) for v in (ap[0], ap[-1], bp[0], bp[-1])) < 25: continue
                    if any(abs(q-v) < 28 for v in nodes): continue
                    if abs(den)/(abs(r)*abs(s)) < .22: continue
                    if any(abs(q-v[0]) < 35 for v in found): continue
                    found.append((q, a, b, c, d))
    return found

def bends(scene):
    return sum(G.bend_count(pp) for _s, pp in scene.paths)

def min_gap(scene, cap=200.0):
    """Closest approach of different-coloured lines, ignoring joins/crossings.
    Grid buckets keep the pairwise search cheap; only distances under cap count."""
    segs = []  # (a, b, stroke, path_index, path endpoints)
    for pi, (stroke, pp) in enumerate(scene.paths):
        for a, b in zip(pp, pp[1:]): segs.append((a, b, stroke, pi, (pp[0], pp[-1])))
    cell = cap
    grid = {}
    for si, (a, b, _s, _p, _e) in enumerate(segs):
        x0, x1 = sorted((a.real, b.real)); y0, y1 = sorted((a.imag, b.imag))
        for ix in range(int(x0//cell), int(x1//cell)+2):
            for iy in range(int(y0//cell), int(y1//cell)+2):
                grid.setdefault((ix, iy), []).append(si)
    best, seen = cap, set()
    for si, (a, b, sa, pa, ea) in enumerate(segs):
        x0, x1 = sorted((a.real, b.real)); y0, y1 = sorted((a.imag, b.imag))
        near = set()
        for ix in range(int(x0//cell)-1, int(x1//cell)+2):
            for iy in range(int(y0//cell)-1, int(y1//cell)+2):
                near.update(grid.get((ix, iy), ()))
        for sj in near:
            if sj <= si or (si, sj) in seen: continue
            seen.add((si, sj))
            c, d, sb, pb, eb = segs[sj]
            if sa == sb or pa == pb: continue
            dd = G.seg_dist(a, b, c, d)
            if dd < 1.0: continue  # a crossing, counted there instead
            if dd >= best: continue
            # Joins at a stop or meeting path endpoints are connections, not
            # crowding (same 25/28 rules the crossing count uses).
            p = a if G.point_seg_dist(a, c, d) <= G.point_seg_dist(b, c, d) else b
            q = c if G.point_seg_dist(c, a, b) <= G.point_seg_dist(d, a, b) else d
            mid = (p+q)/2
            if any(abs(mid-v) < 28 for v in scene.nodes): continue
            if min(abs(p-e) for e in ea+eb) < 25 and min(abs(q-e) for e in ea+eb) < 25: continue
            best = dd
    return best

def text_overlaps(scene, margin=6.0):
    """Text boxes touched by a line (sampling rule from check_text_clearance)."""
    hits = []
    for box in scene.texts:
        x0, y0, x1, y1, t = box[0]-margin, box[1]-margin, box[2]+margin, box[3]+margin, box[4]
        for _s, pp in scene.paths:
            for a, b in zip(pp, pp[1:]):
                if max(a.real, b.real) < x0 or min(a.real, b.real) > x1: continue
                if max(a.imag, b.imag) < y0 or min(a.imag, b.imag) > y1: continue
                if any(x0 <= (a+(b-a)*k/40).real <= x1 and y0 <= (a+(b-a)*k/40).imag <= y1
                       for k in range(41)):
                    hits.append((t, a, b)); break
            else: continue
            break
    return hits

def score(svg_text, margin=6.0, cap=200.0):
    scene = G.load(svg_text)
    return {'crossings': len(crossings(scene)),
            'bends': bends(scene),
            'min_gap': round(min_gap(scene, cap), 1),
            'text_overlaps': len(text_overlaps(scene, margin))}

if __name__ == '__main__':
    src = Path(sys.argv[-1]).read_text() if len(sys.argv) > 1 and not sys.argv[-1].startswith('-') \
        else (Path(__file__).resolve().parents[1]/'data/all-stops.svg').read_text()
    s = score(src)
    if '--json' in sys.argv: print(json.dumps(s, indent=2))
    else: print('layout score: crossings=%(crossings)d bends=%(bends)d min_gap=%(min_gap)s text_overlaps=%(text_overlaps)d' % s)
