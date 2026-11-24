"""Non-destructive trial of proposal 2 (A* walking-link routing) on the real map.

Picks actual existing walking links from data/all-stops.svg, re-routes each
one with route_walk_links against the rest of the current geometry, and
compares length, bends, crossings and text clearance. Nothing here writes into
the generator or index.html; variant SVGs land in experiments/results/ for
visual comparison only.
"""
import json, re, sys
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import map_geometry as G
import route_walk_links as W
import score_route_map as SC
from map_bridges import add_bridges, points

# Hand-drawn walk links to re-route, by their raw d string in the SVG.
LINKS = {
    'home-walk-850m':   'M 1552 228 L 1552 130 L 700 130 L 700 141',
    'gi-out-walk':      'M 1493 1290 L 1504 1290 L 1504 2289 L 1771 2289',
    'pramuka-walk':     'M 360 228 L 700 167',
    'bakoel-out-walk':  'M 2067 1372 L 1995 1372 L 1995 2139 L 2320 2139',
}

def strip_hops(svg):
    return re.sub(r'<g id="nonconnecting-crossings".*?</g>\n?', '', svg, flags=re.S)

def find_shifts(svg_text, raws):
    """Global translate of each raw-d path, from its enclosing groups."""
    root = ET.fromstring(svg_text)
    found = {}
    def walk(el, sh=0j):
        tr = re.search(r'translate\(([-.\d]+)[ ,]+([-.\d]+)\)', el.get('transform', ''))
        if tr: sh += complex(*map(float, tr.groups()))
        if el.tag.endswith('path') and el.get('d') in raws:
            found[el.get('d')] = (sh, el.get('stroke'), el.get('stroke-width'), el.get('opacity'))
        for c in el: walk(c, sh)
    walk(root)
    return found

def poly_metrics(pp, scene):
    length = sum(abs(b-a) for a, b in zip(pp, pp[1:]))
    bends = G.bend_count(pp)
    crossings = 0
    for _s, op in scene.paths:
        for a, b in zip(pp, pp[1:]):
            for c, d in zip(op, op[1:]):
                q = G.seg_intersection(a, b, c, d)
                if q is None: continue
                r = b-a; s = d-c
                if abs(G.cross(r, s))/(abs(r)*abs(s)+1e-9) < .22: continue
                if min(abs(q-pp[0]), abs(q-pp[-1])) < 25: continue
                if any(abs(q-v) < 28 for v in scene.nodes): continue
                crossings += 1
    text_hits = 0
    for x0, y0, x1, y1, _t in scene.texts:
        m = 6
        x0 -= m; y0 -= m; x1 += m; y1 += m
        for a, b in zip(pp, pp[1:]):
            if max(a.real, b.real) < x0 or min(a.real, b.real) > x1: continue
            if max(a.imag, b.imag) < y0 or min(a.imag, b.imag) > y1: continue
            if any(x0 <= (a+(b-a)*k/40).real <= x1 and y0 <= (a+(b-a)*k/40).imag <= y1
                   for k in range(41)):
                text_hits += 1; break
    return {'length': round(length), 'bends': bends, 'crossings': crossings, 'text_hits': text_hits}

def main():
    svg0 = (ROOT/'data/all-stops.svg').read_text()
    base = strip_hops(svg0)
    shifts = find_shifts(base, set(LINKS.values()))
    out = {'base_score': SC.score(svg0), 'links': {}}
    variants = {}
    for name, raw in LINKS.items():
        sh, stroke, sw, op = shifts[raw]
        without = base.replace(raw, 'M 0 0', 1)  # park the hand link: it is no obstacle to itself
        scene = G.load(without)
        pp_hand = [p+sh for p in points(raw)]
        start, goal = pp_hand[0], pp_hand[-1]
        hand = poly_metrics(pp_hand, scene)
        try:
            corners, cost = W.route((start.real, start.imag), (goal.real, goal.imag), scene, cell=20, margin=10)
        except ValueError as e:
            out['links'][name] = {'hand': hand, 'routed': None, 'error': str(e)}
            continue
        pp_new = [complex(x, y) for x, y in corners]
        routed = poly_metrics(pp_new, scene)
        routed['search_cost'] = round(cost)
        # Variant SVG: same element, new d in the path's local (group) coords.
        d_new = 'M %s L %s' % ('%.0f %.0f' % (pp_new[0].real-sh.real, pp_new[0].imag-sh.imag),
                               ' L '.join('%.0f %.0f' % (p.real-sh.real, p.imag-sh.imag) for p in pp_new[1:]))
        variant = base.replace(raw, d_new, 1)
        variant = add_bridges(variant)
        variants[name] = variant
        (ROOT/'experiments/results'/f'variant-{name}.svg').write_text(variant)
        out['links'][name] = {'hand': hand, 'routed': routed,
                              'variant_score': SC.score(variant),
                              'hand_path': [ [round(p.real), round(p.imag)] for p in pp_hand],
                              'routed_path': [[round(p.real), round(p.imag)] for p in pp_new]}
    (ROOT/'experiments/results/walk-trial.json').write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))

if __name__ == '__main__':
    main()
