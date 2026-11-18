#!/usr/bin/env python3
"""Stop snapshot invariants and rendered-map coverage, independent of Android."""
import importlib.util, json, re, unittest
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
D=json.loads((ROOT/'data/route-stops.json').read_text()); S={s['route']:s for s in D['segments']}
class StopMapTest(unittest.TestCase):
 def test_directional_sequences(self):
  for seg in S.values():
   seq=[s['sequence'] for s in seg['stops']]
   self.assertEqual(seq,list(range(seq[0],seq[-1]+1)))
   self.assertEqual(len({s['id'] for s in seg['stops']}),len(seq))
 def test_relevant_patterns_not_reverse_or_short_turn(self):
  self.assertEqual(S['4']['trip'],'4-R26')
  self.assertEqual(S['5M']['trip'],'5M-L04')
  self.assertEqual(S['9']['direction'],'Pluit')
  self.assertEqual(S['7E']['direction'],'Kampung Rambutan')
 def test_order_landmarks(self):
  expected={'4':['Pramuka Sari','Utan Kayu','Pasar Genjing','Matraman','Tegalan','Kesatrian'],
    '10':['Pemuda Pramuka','Utan Kayu Rawamangun','Pisangan','Flyover Jatinegara','Pedati Prumpung','Kebon Nanas','Halim','Simpang Cawang'],
    '7E':['Masjid Ar-Raudhah','Ampera 1','Jatipadang Raya','Jln. Jatipadang Poncol','Jln. Mujair Raya','Jln. Gabus Raya']}
  for route,names in expected.items():
   actual=[s['name'] for s in S[route]['stops']]
   idx=[actual.index(n) for n in names];self.assertEqual(idx,sorted(idx))
 def test_all_station_names_are_visible_svg_text(self):
  root=ET.fromstring((ROOT/'data/all-stops.svg').read_text());texts=[''.join(x.itertext()) for x in root.iter() if x.tag.endswith('text')]
  joined=' '.join(texts)
  for seg in S.values():
   for st in seg['stops']:self.assertIn(st['name'],joined)
 def test_map_and_android_share_exact_svg(self):
  svg=(ROOT/'data/all-stops.svg').read_text().strip()
  self.assertEqual((ROOT/'index.html').read_text().count(svg),2)
  self.assertIn(svg,(ROOT/'android/app/src/main/assets/map.html').read_text())
 def test_no_outbound_return_stop_mix(self):
  names=[s['name'] for s in S['7E']['stops']]
  self.assertNotIn('Baung',names); self.assertNotIn('Phe Tower Kebagusan',names)
 def test_homebound_patterns_are_independent_and_complete(self):
  ret=json.loads((ROOT/'data/return-stops.json').read_text())
  r={x['key']:x['stops'] for x in ret['segments']}
  self.assertEqual(r['7E-return'][0],'Phe Tower Kebagusan')
  self.assertEqual(r['7E-return'][-1],'Ragunan')
  self.assertIn('Flyover Kuningan',r['6-return'])
  self.assertIn('Halte Manggarai Temporer 1',r['4-return'])
  self.assertNotIn('Matraman',r['4-return'])
  self.assertEqual(r['7F-return'],['Flyover Raya Bogor','Trikora','Pasar Induk','Utan Kayu Rawamangun','Pemuda Pramuka','Kayu Putih Rawasari'])
  svg=(ROOT/'data/all-stops.svg').read_text()
  for stops in r.values():
   for name in stops:self.assertIn(name,svg)
  for term in ['One network · out and home','Gojek to Flyover Raya Bogor','fresh tap/fare','not a guarantee','7F service-hour listings disagree']:
   self.assertIn(term,svg)
 def test_homebound_is_inside_top_network(self):
  svg=(ROOT/'data/all-stops.svg').read_text()
  self.assertNotIn('Going home from Arkadia',svg)
  self.assertIn('One network · out and home',svg)
  self.assertIn('translate(700 0)',svg)
  self.assertIn('3000',svg.split('>')[0])
  height=int(re.search(r'viewBox="0 0 3000 (\d+)"',svg).group(1))
  self.assertLess(height,3400)
  self.assertEqual(svg.count('4D leaves here'),1)
 def test_shared_spine_is_not_a_duplicate_return_column(self):
  root=ET.fromstring((ROOT/'data/all-stops.svg').read_text())
  texts=[''.join(x.itertext()) for x in root.iter() if x.tag.endswith('text')]
  for name in ['Pramuka Sari','Utan Kayu','Pasar Genjing','Pasar Rumput','Halimun','Galunggung','Kuningan','Patra Kuningan','Underpass Kuningan','Mampang Prapatan','Duren Tiga','Warung Buncit','Warung Jati','Buncit Indah','Pejaten','Jati Padang','Jati Barat']:
   self.assertEqual(texts.count(name),1,name)
  self.assertEqual(texts.count('Flyover Kuningan'),1)
  self.assertEqual(texts.count('Halte Manggarai Temporer 1'),1)
  self.assertEqual(texts.count('Phe Tower Kebagusan'),1)
  self.assertIn('Shared 4 / 6 spine', ' '.join(texts))
  self.assertIn('not necessarily platforms', ' '.join(texts))
 def test_offline_asset(self):
  page=(ROOT/'android/app/src/main/assets/map.html').read_text()
  self.assertNotIn('<script',page)
  self.assertNotRegex(page,r'(?:src|href)="https?://')
  self.assertIn('maximum-scale=8',page)
if __name__=='__main__':unittest.main()
