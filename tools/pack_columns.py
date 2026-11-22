"""Proposal 3 (pack columns by search): treat each corridor (outbound and
return together where coordinates allow) as a movable block, fix the page
width, leave height free, and minimise total link length plus routing
penalties. Pure Python local search, enough at Tuju's size.

A block has a fixed size and named ports (block-relative points where walking
links attach). A link joins two ports. Links are routed as one-bend L paths;
a link that crosses a third block pays a large penalty, so the search also
learns to keep links clear of blocks. Final routing of an adopted layout uses
route_walk_links (proposal 2) against the real label boxes; the L-route cost
here is the cheap objective the search optimises.

Usage: python3 tools/pack_columns.py EXAMPLE.json
  EXAMPLE.json: {"width": W, "blocks": [{"id","w","h","ports":{"name":[x,y]}}],
                 "links": [["blockA","portA","blockB","portB"]],
                 "place": {"block": [x, y]},  optional starting positions
                 "seed": 1, "iters": 20000}
Prints the packed placement and cost as JSON.
"""
import json, math, random, sys

def port_xy(blocks, place, ref):
    b = blocks[ref[0]]; px, py = b['ports'][ref[1]]
    x, y = place[ref[0]]
    return (x+px, y+py)

def l_route(p, q):
    """Cheapest one-bend L path between p and q: (length, bends, corners)."""
    if p[0] == q[0] or p[1] == q[1]:
        return abs(p[0]-q[0])+abs(p[1]-q[1]), 0, []
    e1 = (p[0], q[1]); e2 = (q[0], p[1])
    L = abs(p[0]-q[0])+abs(p[1]-q[1])
    return L, 1, [e1, e2]

def seg_hits_block(a, b, bl, place, skip):
    """Does segment ab pass through any block box other than skip?"""
    for bid, blk in bl.items():
        if bid in skip: continue
        x, y = place[bid]
        x0, y0, x1, y1 = x, y, x+blk['w'], y+blk['h']
        if max(a[0], b[0]) < x0 or min(a[0], b[0]) > x1: continue
        if max(a[1], b[1]) < y0 or min(a[1], b[1]) > y1: continue
        # Strict interior touch counts; grazing an edge is fine.
        if min(a[0], b[0]) < x1 and max(a[0], b[0]) > x0 and \
           min(a[1], b[1]) < y1 and max(a[1], b[1]) > y0: return True
    return False

def cost(blocks, links, place, width, bend_cost=40, cross_penalty=1000, overlap_penalty=100000):
    total = 0.0
    ids = list(blocks)
    # Blocks must stay inside the page width and never overlap.
    for i, a in enumerate(ids):
        xa, ya = place[a]; ba = blocks[a]
        if xa < 0 or xa+ba['w'] > width or ya < 0: total += overlap_penalty
        if ba.get('obstacle'): continue
        for b in ids[i+1:]:
            xb, yb = place[b]; bb = blocks[b]
            if bb.get('obstacle'): continue
            if xa < xb+bb['w'] and xb < xa+ba['w'] and ya < yb+bb['h'] and yb < ya+ba['h']:
                total += overlap_penalty
    for la, lb in links:
        pa = port_xy(blocks, place, la); pb = port_xy(blocks, place, lb)
        L, bends, elbows = l_route(pa, pb)
        total += L + bends*bend_cost
        skip = {la[0], lb[0]}
        pts = [pa]+elbows[:1]+[pb] if elbows else [pa, pb]
        for a, b in zip(pts, pts[1:]):
            if seg_hits_block(a, b, blocks, place, skip): total += cross_penalty
    return total

def pack(blocks, links, width, place=None, iters=20000, seed=1, axis='xy', fixed=()):
    """Simulated annealing over block (x, y) positions. Blocks: {id: {w,h,ports}};
    links: [((block,port),(block,port))]; place: optional {id: (x,y)} start.
    axis='x' keeps every block's y fixed (reading order is meaning), and
    axis='y' keeps x fixed."""
    rng = random.Random(seed)
    ids = [bid for bid in blocks if bid not in set(fixed)]
    if place is None:
        place = {}
        x = 0
        for bid in ids:  # naive left-to-right row as the starting point
            place[bid] = (float(x), 0.0); x += blocks[bid]['w']+50
    else:
        place = {k: (float(v[0]), float(v[1])) for k, v in place.items()}
    cur = cost(blocks, links, place, width)
    best, best_place = cur, dict(place)
    t0, t1 = 200.0, 1.0
    for it in range(iters):
        T = t0*(t1/t0)**(it/max(iters-1, 1))
        bid = rng.choice(ids)
        old = place[bid]
        nx = max(0.0, min(width-blocks[bid]['w'], old[0]+rng.gauss(0, 80))) if 'x' in axis else old[0]
        ny = max(0.0, old[1]+rng.gauss(0, 80)) if 'y' in axis else old[1]
        place[bid] = (nx, ny)
        new = cost(blocks, links, place, width)
        if new <= cur or rng.random() < math.exp(-(new-cur)/T):
            cur = new
            if new < best: best, best_place = new, dict(place)
        else:
            place[bid] = old
    return best_place, best

if __name__ == '__main__':
    spec = json.loads(open(sys.argv[1]).read())
    blocks = {b['id']: {'w': b['w'], 'h': b['h'], 'ports': b.get('ports', {})} for b in spec['blocks']}
    links = [((l[0], l[1]), (l[2], l[3])) for l in spec['links']]
    place = {k: tuple(v) for k, v in spec.get('place', {}).items()} or None
    bp, bc = pack(blocks, links, spec['width'], place, spec.get('iters', 20000), spec.get('seed', 1))
    print(json.dumps({'cost': bc, 'place': {k: [round(x, 1), round(y, 1)] for k, (x, y) in bp.items()}}, indent=2))
