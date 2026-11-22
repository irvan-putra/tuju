"""Proposal 2 (route walking links by search): obstacle-avoiding A* on a coarse
grid, the libavoid idea in a small amount of dependency-free Python.
  - label boxes (real estimated widths, wrapped notes included) are blocked
    cells, inflated by a margin: a walk never runs through text;
  - drawn route lines are crossing charges: passing from free space into a
    line's cell or back out costs half a crossing each, so one full crossing
    costs cross_cost and a walk only crosses when going around costs more;
  - every direction change is a bend charge, so straight runs win.
The anchor cells and their immediate neighbours are always passable: a walk is
allowed to touch its own endpoints even when a label sits beside the stop.
Usage: python3 tools/route_walk_links.py X1 Y1 X2 Y2 [--cell N] [--svg PATH]
Prints an SVG path `d` for the routed link; route stats go to stderr.
"""
import heapq, sys
from pathlib import Path
import map_geometry as G

def _cells_along(a, b, cell):
    """Grid cells a segment passes through, sampled finely enough not to skip."""
    n = max(1, int(abs(b-a)/(cell/2))+1)
    return [(int((a+(b-a)*k/n).real//cell), int((a+(b-a)*k/n).imag//cell)) for k in range(n+1)]

def route(start, goal, scene, cell=20, margin=10, bend_cost=40, cross_cost=250, pad=300):
    """A* from start to goal (map units, complex or (x,y)). Returns (points, cost).
    Points are the corner coordinates of an orthogonal polyline."""
    sx, sy = (start.real, start.imag) if isinstance(start, complex) else start
    gx, gy = (goal.real, goal.imag) if isinstance(goal, complex) else goal
    x0 = min(sx, gx)-pad; y0 = min(sy, gy)-pad
    x1 = max(sx, gx)+pad; y1 = max(sy, gy)+pad
    for _s, pp in scene.paths:  # links may detour around any drawn line
        for p in pp:
            x0=min(x0,p.real-pad); x1=max(x1,p.real+pad); y0=min(y0,p.imag-pad); y1=max(y1,p.imag+pad)
    def cell_of(x, y): return (int(x//cell), int(y//cell))
    sc, gc = cell_of(sx, sy), cell_of(gx, gy)
    # Hard obstacles: text boxes inflated by the margin.
    blocked = set()
    for bx0, by0, bx1, by1, _t in scene.texts:
        for ix in range(int((bx0-margin)//cell), int((bx1+margin)//cell)+1):
            for iy in range(int((by0-margin)//cell), int((by1+margin)//cell)+1):
                blocked.add((ix, iy))
    # The anchor cells and their neighbours stay passable (a label beside a
    # stop must not make its own walk unroutable).
    for anchor in (sc, gc):
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                blocked.discard((anchor[0]+dx, anchor[1]+dy))
    # Crossing charges: which cells a drawn line occupies.
    line_cells = set()
    for _s, pp in scene.paths:
        for a, b in zip(pp, pp[1:]):
            line_cells.update(_cells_along(a, b, cell))
    # A* over (cell, incoming direction); cost = distance + bends + crossings.
    INF = float('inf')
    start_state = (sc, None)
    dist = {start_state: 0.0}; back = {}
    h = lambda c: (abs(c[0]-gc[0])+abs(c[1]-gc[1]))*cell
    heap = [(h(sc), 0.0, start_state)]
    DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
    goal_state = None
    while heap:
        _f, d, state = heapq.heappop(heap)
        c, ind = state
        if d > dist.get(state, INF)+1e-9: continue
        if c == gc: goal_state = state; break
        for di, (dx, dy) in enumerate(DIRS):
            nc = (c[0]+dx, c[1]+dy)
            if nc in blocked: continue
            nx0, nx1 = nc[0]*cell, (nc[0]+1)*cell; ny0, ny1 = nc[1]*cell, (nc[1]+1)*cell
            if nx1 < x0 or nx0 > x1 or ny1 < y0 or ny0 > y1: continue
            w = cell
            if ind is not None and ind != di: w += bend_cost
            if (nc in line_cells) != (c in line_cells): w += cross_cost/2
            ns = (nc, di)
            nd = d+w
            if nd < dist.get(ns, INF)-1e-9:
                dist[ns] = nd; back[ns] = state
                heapq.heappush(heap, (nd+h(nc), nd, ns))
    if goal_state is None: raise ValueError('no route found')
    cells = [goal_state[0]]
    st = goal_state
    while st in back: st = back[st]; cells.append(st[0])
    cells.reverse()
    # Drop collinear cells, keep corners; snap ends to the exact anchors.
    corners = []
    for k in range(1, len(cells)-1):
        a, b, cc = cells[k-1], cells[k], cells[k+1]
        if (b[0]-a[0], b[1]-a[1]) != (cc[0]-b[0], cc[1]-b[1]):
            corners.append(((b[0]+0.5)*cell, (b[1]+0.5)*cell))
    # Orthogonal stubs: leave and arrive in the direction of the first/last
    # cell move, with an elbow point so no diagonal segment is drawn.
    first_move = (cells[1][0]-cells[0][0], cells[1][1]-cells[0][1]) if len(cells) > 1 else (0, 0)
    last_move = (cells[-1][0]-cells[-2][0], cells[-1][1]-cells[-2][1]) if len(cells) > 1 else (0, 0)
    pts = [(sx, sy)]
    if corners:
        f = corners[0]
        if first_move[0] == 0: pts.append((sx, f[1]))
        else: pts.append((f[0], sy))
    pts += corners
    if corners:
        l = corners[-1]
        if last_move[0] == 0: pts.append((gx, l[1]))
        else: pts.append((l[0], gy))
    pts.append((gx, gy))
    # Drop duplicates and collinear points created by the elbows.
    out = [pts[0]]
    for p in pts[1:]:
        if p == out[-1]: continue
        while len(out) >= 2:
            a, b = out[-2], out[-1]
            if (b[0]-a[0])*(p[1]-b[1]) == (b[1]-a[1])*(p[0]-b[0]) and \
               (b[0]-a[0])*(p[0]-b[0]) >= 0 and (b[1]-a[1])*(p[1]-b[1]) >= 0: out.pop()
            else: break
        out.append(p)
    return out, dist[goal_state]

def to_d(points):
    return 'M %s L %s' % ('%.0f %.0f' % points[0], ' L '.join('%.0f %.0f' % p for p in points[1:]))

if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    cell = 20
    if '--cell' in sys.argv: cell = float(sys.argv[sys.argv.index('--cell')+1])
    svg = 'data/all-stops.svg'
    if '--svg' in sys.argv: svg = sys.argv[sys.argv.index('--svg')+1]
    if len(args) != 4:
        sys.exit('usage: route_walk_links.py X1 Y1 X2 Y2 [--cell N] [--svg PATH]')
    x1, y1, x2, y2 = map(float, args)
    p = Path(svg)
    if not p.is_absolute(): p = Path(__file__).resolve().parents[1]/svg
    scene = G.load(p.read_text())
    pts, cost = route((x1, y1), (x2, y2), scene, cell=cell)
    print(to_d(pts))
    print('# corners=%d cost=%.0f' % (len(pts)-2, cost), file=sys.stderr)
