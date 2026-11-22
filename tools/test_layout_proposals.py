"""Tests for the three map-layout proposals: the build score (1), the A*
walking-link router (2) and the corridor packer (3). Standard library only."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import map_geometry as G
import route_walk_links as W
import pack_columns as P
import score_route_map as SC

ROOT = Path(__file__).resolve().parents[1]
SCENE_SVG = '''<svg xmlns="http://www.w3.org/2000/svg">
<path d="M 100 0 L 100 400" fill="none" stroke="#f00"/>
<text x="150" y="200" font-size="20">a label in the way</text>
</svg>'''

def orthogonal(points):
    return all(p[0] == q[0] or p[1] == q[1] for p, q in zip(points, points[1:]))

class ScoreTest(unittest.TestCase):
    def test_components_present_and_typed(self):
        s = SC.score((ROOT/'data/all-stops.svg').read_text())
        self.assertEqual(set(s), {'crossings', 'bends', 'min_gap', 'text_overlaps'})
        self.assertIsInstance(s['crossings'], int)
        self.assertIsInstance(s['bends'], int)
        self.assertGreater(s['min_gap'], 0)
        self.assertGreaterEqual(s['text_overlaps'], 0)
    def test_crossings_match_drawn_hops(self):
        # The hop marker group and the crossing count must tell one story.
        svg = (ROOT/'data/all-stops.svg').read_text()
        scene = G.load(svg)
        self.assertNotIn('nonconnecting-crossings', [p[0] for p in scene.paths])
        self.assertEqual(len(SC.crossings(scene)), SC.score(svg)['crossings'])
    def test_synthetic_counts(self):
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
<path d="M 0 0 L 0 100 L 50 100" fill="none" stroke="#f00"/>
<path d="M 25 50 L 25 150" fill="none" stroke="#00f"/>
<text x="500" y="500" font-size="20">far away</text>
</svg>'''
        s = SC.score(svg)
        self.assertEqual(s['crossings'], 1)   # the two lines cross at (25, 100)... no: red L and blue vertical
        self.assertEqual(s['bends'], 1)       # red has one corner, blue is straight
        self.assertEqual(s['text_overlaps'], 0)
    def test_text_overlap_detected(self):
        svg = '''<svg xmlns="http://www.w3.org/2000/svg">
<path d="M 0 200 L 400 200" fill="none" stroke="#f00"/>
<text x="150" y="200" font-size="20">a label in the way</text>
</svg>'''
        self.assertEqual(SC.score(svg)['text_overlaps'], 1)

class WalkRouterTest(unittest.TestCase):
    def setUp(self):
        self.scene = G.load(SCENE_SVG)
    def test_clear_run_is_straight(self):
        pts, cost = W.route((0, 100), (0, 300), self.scene, cell=10, margin=5)
        self.assertEqual(pts, [(0, 100), (0, 300)])
        self.assertEqual(cost, 200.0)
    def test_label_is_avoided(self):
        pts, _c = W.route((0, 200), (300, 200), self.scene, cell=10, margin=5)
        self.assertTrue(orthogonal(pts))
        # Only the exempt anchor cell may sit inside the inflated label box.
        for a, b in zip(pts, pts[1:]):
            for k in range(41):
                x = a[0]+(b[0]-a[0])*k/40; y = a[1]+(b[1]-a[1])*k/40
                if 145 <= x <= 349 and 179 <= y <= 210:
                    self.assertLess(abs(x-300)+abs(y-200), 30)
    def test_crossing_costs_more_than_straight(self):
        _p, clear = W.route((0, 100), (0, 300), self.scene, cell=10, margin=5)
        pts, cross = W.route((0, 100), (200, 100), self.scene, cell=10, margin=5)
        self.assertTrue(orthogonal(pts))
        self.assertGreater(cross, 200)  # same length as clear run, plus a crossing
    def test_rounding_a_line_end_beats_crossing_when_cheaper(self):
        pts, cost = W.route((0, 350), (300, 350), self.scene, cell=10, margin=5)
        self.assertTrue(all(y > 400 for x, y in pts[1:-1]))  # went around the bottom end
    def test_enclosed_anchor_raises(self):
        walled = '''<svg xmlns="http://www.w3.org/2000/svg">
<path d="M 0 0 L 100 0 L 100 100 L 0 100 Z" fill="none" stroke="#f00"/>
<text x="-30" y="30" font-size="60">xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx</text>
<text x="-30" y="90" font-size="60">xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx</text>
</svg>'''
        scene = G.load(walled)
        with self.assertRaises(ValueError):
            W.route((50, 50), (300, 300), scene, cell=10, margin=5, pad=50)

class PackerTest(unittest.TestCase):
    def setUp(self):
        self.blocks = {
            'home': {'w': 300, 'h': 200, 'ports': {'out': (300, 100), 'walk': (150, 200)}},
            'bus': {'w': 200, 'h': 600, 'ports': {'top': (100, 0), 'mid': (100, 300)}},
            'mall': {'w': 250, 'h': 150, 'ports': {'door': (125, 0)}}}
        self.links = [(('home', 'out'), ('bus', 'top')), (('bus', 'mid'), ('mall', 'door'))]
    def test_packed_beats_overlapping_start(self):
        start = {'home': (0, 0), 'bus': (0, 250), 'mall': (0, 500)}
        c0 = P.cost(self.blocks, self.links, start, 900)
        bp, bc = P.pack(self.blocks, self.links, 900, start, iters=8000, seed=7)
        self.assertLess(bc, c0)
        ids = list(self.blocks)
        for i, a in enumerate(ids):
            xa, ya = bp[a]
            self.assertGreaterEqual(xa, 0)
            self.assertLessEqual(xa+self.blocks[a]['w'], 900)
            for b in ids[i+1:]:
                xb, yb = bp[b]
                overlap = xa < xb+self.blocks[b]['w'] and xb < xa+self.blocks[a]['w'] \
                    and ya < yb+self.blocks[b]['h'] and yb < ya+self.blocks[a]['h']
                self.assertFalse(overlap, (a, b))
    def test_straight_link_has_no_bend_cost(self):
        blocks = {'a': {'w': 100, 'h': 100, 'ports': {'p': (100, 50)}},
                  'b': {'w': 100, 'h': 100, 'ports': {'q': (0, 50)}}}
        place = {'a': (0, 0), 'b': (200, 0)}
        self.assertEqual(P.cost(blocks, [(('a', 'p'), ('b', 'q'))], place, 900), 100.0)
    def test_link_through_third_block_is_penalised(self):
        blocks = {'a': {'w': 100, 'h': 100, 'ports': {'p': (100, 50)}},
                  'wall': {'w': 100, 'h': 300, 'ports': {}},
                  'b': {'w': 100, 'h': 100, 'ports': {'q': (0, 50)}}}
        place = {'a': (0, 0), 'wall': (150, 0), 'b': (300, 0)}
        self.assertGreaterEqual(P.cost(blocks, [(('a', 'p'), ('b', 'q'))], place, 900), 1000)


    def test_pack_fixed_blocks_do_not_move(self):
        # a block listed in fixed must keep its placement even when moving it
        # would shorten the link
        blocks = {'m': {'w': 100, 'h': 100, 'ports': {'a': (50, 100)}},
                  's': {'w': 100, 'h': 100, 'ports': {'b': (50, 0)}}}
        links = [(('m', 'a'), ('s', 'b'))]
        place = {'m': (0.0, 0.0), 's': (400.0, 300.0)}
        bp, _ = P.pack(blocks, links, 1000, place, iters=2000, seed=3, fixed=("m",))
        self.assertEqual(bp['m'], (0.0, 0.0))
        # the free block still moved toward the fixed one
        self.assertLess(abs(bp['s'][0] - 0) + abs(bp['s'][1] - 200), 400)

if __name__ == '__main__':
    unittest.main()
