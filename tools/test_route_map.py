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
 def test_halimun_labels_clear_return_arrow_and_branch(self):
  root=ET.fromstring((ROOT/'data/all-stops.svg').read_text())
  labels={''.join(e.itertext()):e for e in root.iter() if e.tag.endswith('text')}
  name=labels['Halimun'];note=labels['4D leaves here; 4 goes on to Galunggung']
  self.assertEqual((name.get('x'),name.get('y')),('680','779'))
  self.assertEqual((note.get('x'),note.get('y')),('680','800'))
  self.assertEqual(note.get('fill'),'currentColor')
 def test_no_outbound_return_stop_mix(self):
  names=[s['name'] for s in S['7E']['stops']]
  self.assertNotIn('Baung',names); self.assertNotIn('Phe Tower Kebagusan',names)
 def test_journey_meter_segments_match_stop_data(self):
  import re as _re
  t=(ROOT/'index.html').read_text()
  m=_re.search(r'var TUJU_SEGMENTS = (\[.*?\]);\s*/\* journey-segments:end',t,_re.S)
  self.assertIsNotNone(m,'journey segment list missing from index.html')
  segs=json.loads(m.group(1))
  expected=[{'label':'%s toward %s'%(s['route'],s['direction']),'stops':[x['name'] for x in s['stops']]} for s in D['segments']]
  ret=json.loads((ROOT/'data/return-stops.json').read_text())
  expected+=[{'label':'%s return: %s - %s'%(s['route'],s['stops'][0],s['stops'][-1]),'stops':s['stops']} for s in ret['segments']]
  self.assertEqual([{k:s[k] for k in ('label','stops')} for s in segs],expected)
 def test_journey_meter_estimates_are_grounded_or_absent(self):
  import re as _re
  t=(ROOT/'index.html').read_text()
  segs=json.loads(_re.search(r'var TUJU_SEGMENTS = (\[.*?\]);\s*/\* journey-segments:end',t,_re.S).group(1))
  for s in segs:
   n=len(s['stops'])
   if s['coords'] is not None:
    self.assertEqual(len(s['coords']),n)
    for lat,lon in s['coords']: self.assertTrue(-6.5<lat<-6.0 and 106.6<lon<107.0,(s['label'],lat,lon))
   if s['sched'] is not None:
    self.assertEqual(len(s['sched']),n); self.assertEqual(s['sched'][0],0)
    self.assertEqual(s['sched'],sorted(s['sched']))
  # Outbound legs with a referenced GTFS trip carry a schedule; returns and 4D do not.
  bylabel={s['label']:s for s in segs}
  self.assertIsNotNone(bylabel['4 toward Galunggung via Saharjo']['sched'])
  self.assertIsNone(bylabel['4D toward Patra Kuningan (westbound pattern)']['sched'])
  self.assertTrue(all(s['sched'] is None for s in segs if ' return: ' in s['label']))
 def test_journey_meter_reaches_android_asset(self):
  asset=(ROOT/'android/app/src/main/assets/map.html').read_text()
  self.assertIn('id="journey-meter"',asset)
  self.assertIn('var TUJU_SEGMENTS = [',asset)
 def test_homebound_patterns_are_independent_and_complete(self):
  ret=json.loads((ROOT/'data/return-stops.json').read_text())
  r={x['key']:x['stops'] for x in ret['segments']}
  self.assertEqual(r['7E-return'][0],'Phe Tower Kebagusan')
  self.assertEqual(r['7E-return'][-1],'Department of Agriculture Busway Shelter')
  self.assertIn('Flyover Kuningan',r['6-return'])
  self.assertIn('Halte Manggarai Temporer 1',r['4-return'])
  self.assertNotIn('Matraman',r['4-return'])
  self.assertEqual(r['7F-return'],['Flyover Raya Bogor','Trikora','Pasar Induk','Utan Kayu Rawamangun','Pemuda Pramuka','Kayu Putih Rawasari'])
  svg=(ROOT/'data/all-stops.svg').read_text()
  for stops in r.values():
   for name in stops:self.assertIn(name.replace('Department of Agriculture Busway Shelter','Department of Agriculture'),svg)
  for term in ['One network · out and home','Gojek to Flyover Raya Bogor','fresh tap/fare','7F service-hour listings disagree']:
   self.assertIn(term,svg)
 def test_homebound_is_inside_top_network(self):
  svg=(ROOT/'data/all-stops.svg').read_text()
  self.assertNotIn('Going home from Arkadia',svg)
  self.assertIn('One network · out and home',svg)
  self.assertIn('translate(700 0)',svg)
  self.assertIn('4200',svg.split('>')[0])
  height=int(re.search(r'viewBox="0 0 4200 (\d+)"',svg).group(1))
  self.assertLess(height,7900)
  self.assertEqual(svg.count('4D leaves here'),1)
 def test_shared_spine_is_not_a_duplicate_return_column(self):
  root=ET.fromstring((ROOT/'data/all-stops.svg').read_text())
  texts=[''.join(x.itertext()) for x in root.iter() if x.tag.endswith('text')]
  for name in ['Pramuka Sari','Utan Kayu','Pasar Genjing','Pasar Rumput','Halimun','Galunggung','Kuningan','Patra Kuningan','Underpass Kuningan','Mampang Prapatan','Duren Tiga','Warung Buncit','Warung Jati','Buncit Indah','Pejaten','Jati Padang','Jati Barat','Kayu Putih Rawasari','Pemuda Pramuka','Utan Kayu Rawamangun','Pasar Induk','Trikora']:
   self.assertEqual(texts.count(name),1,name)
  self.assertEqual(texts.count('Flyover Kuningan'),1)
  self.assertEqual(texts.count('Halte Manggarai Temporer 1'),1)
  self.assertEqual(texts.count('Phe Tower Kebagusan'),1)
  self.assertIn('Shared 4 / 6 and 10 / 7F spines', ' '.join(texts))
  self.assertIn('not necessarily platforms', ' '.join(texts))
 def test_bsd_and_grand_indonesia_extensions(self):
  self.assertEqual(S['S11']['trip'],'S11-L05')
  self.assertEqual(S['S11']['stops'][0]['id'],'B07533P')
  self.assertEqual(S['S11']['stops'][-1]['id'],'B04683P')
  self.assertEqual(S['4C']['stops'][-1]['name'],'Bundaran Senayan 1')
  ret=json.loads((ROOT/'data/return-stops.json').read_text())
  r={x['key']:x for x in ret['segments']}
  self.assertEqual(r['S11-return']['trip'],'S11-R05')
  self.assertEqual(r['S11-return']['stops'][-1],'Taman Anggrek')
  self.assertEqual(r['4C-GI-return']['stops'][0],'Tosari 2')
  self.assertEqual(r['4C-GI-return']['stops'][-1],'Megaria')
  svg=(ROOT/'data/all-stops.svg').read_text()
  for name in ('The Breeze BSD','Grand Indonesia','2.2 km / 29 min'):
   self.assertIn(name,svg)
  self.assertEqual(svg.count('Serpong BSD</text>'),1)
  self.assertEqual(svg.count('SMPN 8</text>'),1)
 def test_portrait_red_spines_and_alam_sutera(self):
  root=ET.fromstring((ROOT/'data/all-stops.svg').read_text())
  width,height=map(int,root.attrib['viewBox'].split()[2:])
  self.assertLess(width,5000); self.assertGreater(height,width*1.7)
  self.assertEqual(S['S61']['stops'][0]['id'],'G00696')
  self.assertEqual(S['S61']['stops'][-1]['name'],'Forest Park')
  self.assertEqual(S['S61']['trip'],'S61-R02')
  for e in root.iter():
   if e.tag.endswith('path') and e.get('stroke')=='#c52d36':
    nums=list(map(float,re.findall(r'-?\d+(?:\.\d+)?',e.attrib['d'])))
    self.assertTrue(all(x==nums[0] for x in nums[::2]),e.attrib['d'])
  text=' '.join(''.join(e.itertext()) for e in root.iter() if e.tag.endswith('text'))
  for t in ('BINUS main building','Mall / BINUS extension','1 km / 13 min','790 m / 10 min'):
   self.assertIn(t,text)
 def test_offline_asset(self):
  # The journey meter adds an inline script; the asset must still run fully
  # on-device: no external resources and no network calls of any kind.
  page=(ROOT/'android/app/src/main/assets/map.html').read_text()
  self.assertNotRegex(page,r'(?:src|href)="https?://')
  for call in ('fetch(','XMLHttpRequest','WebSocket','sendBeacon','import('):
   self.assertNotIn(call,page)
  self.assertIn('maximum-scale=12',page)
 def test_ragunan_connection_and_return(self):
  svg=(ROOT/'data/all-stops.svg').read_text()
  self.assertIn('7E leg ends here',svg)
  self.assertIn('= Department of Agriculture · same station · 7E leg ends here',svg)
  self.assertIn('6 ↔ both directions',svg)
  self.assertIn('board 6 / 6A ↑ toward Galunggung',svg)
  self.assertIn('Ragunan (destination pin)',svg)
  self.assertIn('7E boards curbside · fresh fare (firsthand)',svg)
  self.assertIn('chosen return: change 6 → 4D here (19 Nov)',svg)
  self.assertIn('teal rings: 4D return stops (Maps, 19 Nov)',svg)
  self.assertEqual(svg.count('Simpang Ragunan Ar-Raudhah</text>'),1)
  self.assertNotIn('walk via Simpang Ragunan',svg)
  self.assertNotIn('6N',svg)
  self.assertNotIn('Kementerian Pertanian',svg)
  self.assertNotIn('PLN Corporate University',svg)
  self.assertNotIn('walk ~40 m',svg)
  self.assertIn('walk ~140 m / 3 min',svg)
  self.assertEqual(svg.count('walk ~140 m / 3 min'),1)
  self.assertIn('7A / D21 boards at Phe Tower: same stops as 7E',svg)
  self.assertIn('Plaza Oleos, Kebagusan Raya, Kementan, Kementan 2',svg)
  self.assertIn('the same station',svg)
  self.assertEqual(svg.count('Masjid Ar-Raudhah</text>'),1)
  self.assertNotIn('M -100 2290',svg)
  self.assertNotIn('M 312 2012 L 618 1956',svg)
 def test_readable_notes_and_crossing_hops(self):
  svg=(ROOT/'data/all-stops.svg').read_text()
  root=ET.fromstring(svg)
  hop=root.find("{http://www.w3.org/2000/svg}g[@id='nonconnecting-crossings']")
  self.assertIsNotNone(hop)
  self.assertGreaterEqual(len(hop),18)
  labels={''.join(e.itertext()):e for e in root.iter() if e.tag.endswith('text')}
  for name in ('Grand Indonesia','A · from Phe Tower beside the venue','Central Park ↔ The Breeze BSD'):
   self.assertGreaterEqual(int(labels[name].get('font-size')),36)
  web=(ROOT/'index.html').read_text();app=(ROOT/'android/app/src/main/assets/map.html').read_text()
  notes=(ROOT/'data/map-reading-notes.html').read_text().strip()
  self.assertIn(notes,web)
  for page in (web,app):
   self.assertIn('id="map-reading-notes"',page)
   self.assertIn('font:16px/1.6',page)
   self.assertIn('A line hop or gap at a crossing means the lines do not connect',page)
   self.assertIn('Read walking and return notes without zoom',page)

if __name__=='__main__':unittest.main()
