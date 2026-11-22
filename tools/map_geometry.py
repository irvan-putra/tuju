"""Shared geometry extraction from the generated all-stops SVG.
Backs the three map-layout proposals (score, walk routing, column packing).
Standard library only. Points are complex numbers (x + yj), as in map_bridges.
"""
import re
import xml.etree.ElementTree as ET
from map_bridges import points, cross

HOPS = 'nonconnecting-crossings'  # hop marks are crossings already counted, skip them

class Scene:
    """texts: (x0,y0,x1,y1,content) boxes; paths: (stroke,[points]); nodes: stop centres."""
    def __init__(self, texts, paths, nodes):
        self.texts, self.paths, self.nodes = texts, paths, nodes

def load(svg_text):
    root = ET.fromstring(svg_text)
    texts, paths, nodes = [], [], []
    def walk(el, sh=0j):
        tr = re.search(r'translate\(([-.\d]+)[ ,]+([-.\d]+)\)', el.get('transform', ''))
        if tr: sh += complex(*map(float, tr.groups()))
        tag = el.tag.split('}')[-1]
        if tag == 'g' and el.get('id') == HOPS: return
        if tag == 'text':
            t = ''.join(el.itertext()); size = float(el.get('font-size', 16))
            x = float(el.get('x', 0)); y = float(el.get('y', 0))
            w = 0.54*size*len(t)*(1.08 if el.get('font-weight') else 1)
            a = el.get('text-anchor', 'start')
            x0 = x-w if a == 'end' else x-w/2 if a == 'middle' else x
            texts.append((sh.real+x0, sh.imag+y-size*0.8, sh.real+x0+w, sh.imag+y+size*0.25, t))
        if tag == 'circle':
            nodes.append(sh+complex(float(el.get('cx', 0)), float(el.get('cy', 0))))
        if tag == 'path' and el.get('fill') == 'none' and el.get('stroke') not in (None, 'Canvas'):
            pp = [p+sh for p in points(el.get('d', ''))]
            if len(pp) > 1: paths.append((el.get('stroke'), pp))
        for c in el: walk(c, sh)
    walk(root)
    return Scene(texts, paths, nodes)

def seg_intersection(a, b, c, d):
    """Intersection point of ab and cd, or None. Near-parallel lines never count."""
    r = b-a; s = d-c; den = cross(r, s)
    if abs(den) < 1e-6: return None
    t = cross(c-a, s)/den; u = cross(c-a, r)/den
    if not (-1e-8 <= t <= 1+1e-8 and -1e-8 <= u <= 1+1e-8): return None
    return a+t*r

def point_seg_dist(p, a, b):
    """Distance from p to segment ab."""
    r = b-a; L2 = abs(r)**2
    if L2 < 1e-12: return abs(p-a)
    t = max(0.0, min(1.0, ((p-a).real*r.real+(p-a).imag*r.imag)/L2))
    return abs(p-(a+t*r))

def seg_dist(a, b, c, d):
    """Distance between segments ab and cd (0 when they cross)."""
    if seg_intersection(a, b, c, d) is not None: return 0.0
    return min(point_seg_dist(a, c, d), point_seg_dist(b, c, d),
               point_seg_dist(c, a, b), point_seg_dist(d, a, b))

def rdp(pp, eps):
    """Ramer-Douglas-Peucker simplification of a polyline."""
    if len(pp) < 3: return pp
    a, b = pp[0], pp[-1]
    i, dmax = 0, -1.0
    for k in range(1, len(pp)-1):
        d = point_seg_dist(pp[k], a, b)
        if d > dmax: i, dmax = k, d
    if dmax <= eps: return [a, b]
    return rdp(pp[:i+1], eps)[:-1]+rdp(pp[i:], eps)

def bend_count(pp, eps=3.0, min_deg=8.0):
    """Corners after simplification: vertices turning more than min_deg."""
    sp = rdp(pp, eps)
    n = 0
    for k in range(1, len(sp)-1):
        v1 = sp[k]-sp[k-1]; v2 = sp[k+1]-sp[k]
        if abs(v1) < 1e-9 or abs(v2) < 1e-9: continue
        cos = (v1.real*v2.real+v1.imag*v2.imag)/(abs(v1)*abs(v2))
        cos = max(-1.0, min(1.0, cos))
        import math
        if math.degrees(math.acos(cos)) > min_deg: n += 1
    return n
