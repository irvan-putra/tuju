#!/usr/bin/env python3
"""Trial: does column packing improve the CURRENT Tuju map geometry?

Non-destructive: models the three top-level layout blocks of the live map
(main network, S11 corridor block, S61 corridor block) from coordinates
measured in data/all-stops.svg at 0.2.14, pins the main network in place
(axis='x', y stays fixed so vertical reading order is untouched), and asks
the packer whether moving a corridor block shortens the drawn walking links
without creating overlaps. Meaning (stop order, connection structure) is
untouched by construction: only whole-block x positions change.

Outputs experiments/results/pack-trial.json and, when the packer moves a
block, a rendered variant SVG with that block shifted.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import pack_columns as P

OUT = ROOT / 'experiments' / 'results'
OUT.mkdir(parents=True, exist_ok=True)

# Measured from data/all-stops.svg @ 0.2.14 (flattened global coords).
BLOCKS = {
    'main': {'w': 4073, 'h': 3059, 'ports': {'cp': (584, 1860), 'redout': (2594, 1855), 'redhome': (2666, 1995)}},
    's11':  {'w': 1097, 'h': 2310, 'ports': {'top': (357, 200)}},
    's61':  {'w': 1103, 'h': 1516, 'ports': {'p1': (643, 240), 'p2': (691, 240)}},
}
PLACE = {'main': (6.0, 21.0), 's11': (233.0, 3240.0), 's61': (1653.0, 3148.0)}
LINKS = [(('main', 'cp'), ('s11', 'top')),
         (('main', 'redout'), ('s61', 'p1')),
         (('main', 'redhome'), ('s61', 'p2'))]
WIDTH = 4200

cur = P.cost(BLOCKS, LINKS, PLACE, WIDTH)
runs = []
for seed in (1, 7, 13, 42):
    bp, bc = P.pack(BLOCKS, LINKS, WIDTH, dict(PLACE), iters=40000, seed=seed,
                    axis='x', fixed=('main',))
    runs.append({'seed': seed, 'cost': round(bc, 1),
                 'place': {k: [round(v[0], 1), round(v[1], 1)] for k, v in bp.items()}})

best = min(runs, key=lambda r: r['cost'])
dx61 = best['place']['s61'][0] - PLACE['s61'][0]
dx11 = best['place']['s11'][0] - PLACE['s11'][0]

svg = (ROOT / 'data' / 'all-stops.svg').read_text()
variant = None
if abs(dx61) >= 1 or abs(dx11) >= 1:
    v = svg
    if abs(dx61) >= 1:
        # shift the whole S61 group; fix the outbound link drawn outside it
        v = v.replace('<g transform="translate(0 0)">',
                      f'<g transform="translate({dx61:g} 0)">', 1)
        v = v.replace(f'L 2296 3330 L 2296 3388',
                      f'L {2296+dx61:g} 3330 L {2296+dx61:g} 3388', 1)
    if abs(dx11) >= 1:
        v = v.replace('<g transform="translate(-3310 3050)">',
                      f'<g transform="translate({-3310+dx11:g} 3050)">', 1)
        # S11 connector tails drawn outside its group
        for old, new in ((566, 566+dx11), (614, 614+dx11)):
            v = re.sub(rf'\bL {old} (\d{{4}})', f'L {new:g} \\1', v)
    variant = OUT / 'variant-packed.svg'
    variant.write_text(v)

result = {
    'model': 'blocks measured from data/all-stops.svg @ 0.2.14; main pinned; x-only moves; walking links as L-routes',
    'current_cost': round(cur, 1),
    'best': best, 'runs': runs,
    'delta_s61_x': round(dx61, 1), 'delta_s11_x': round(dx11, 1),
    'saving_pct': round(100 * (cur - best['cost']) / cur, 1),
    'variant_svg': str(variant.name) if variant else None,
}
(OUT / 'pack-trial.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
