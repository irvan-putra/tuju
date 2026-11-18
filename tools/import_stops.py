#!/usr/bin/env python3
"""Import only the selected, directional trip segments from an operator GTFS zip.
Run with a downloaded feed path. No estimated/reversed stop sequences.
"""
import csv, hashlib, io, json, sys, zipfile
from pathlib import Path
from collections import defaultdict
segments = [
 ('4','4-R26','B08048P','G00202','Galunggung via Saharjo'),
 ('6','6-R04','G00204','G00243','Ragunan'),
 ('7E','7E-R05','B07989P','B01062P','Kampung Rambutan'),
 ('10','10-R01','G00473','G00718','PGC'),
 ('9','9-R01','G00721','G00403','Pluit'),
 ('4C','4C-R09','B07260P','B05812P','Bundaran Senayan'),
 ('5M','5M-L04','B02386P','B01786P','Tanah Abang via Cikini')]
def load(path):
 raw=Path(path).read_bytes(); z=zipfile.ZipFile(io.BytesIO(raw))
 read=lambda n:list(csv.DictReader(io.StringIO(z.read(n+'.txt').decode('utf-8-sig'))))
 stops={s['stop_id']:s for s in read('stops')}; trips={t['trip_id']:t for t in read('trips')}
 times=defaultdict(list)
 for t in read('stop_times'):times[t['trip_id']].append(t)
 result={'source':'https://gtfs.transjakarta.co.id/files/file_gtfs.zip','checked':'2026-11-18','feed_sha256':hashlib.sha256(raw).hexdigest(),'segments':[]}
 for route,trip,start,end,direction in segments:
  assert trips[trip]['route_id']==route
  ordered=sorted(times[trip],key=lambda t:int(t['stop_sequence']))
  ids=[s['stop_id'] for s in ordered]; a=ids.index(start); b=ids.index(end,a)
  seq=[{'id':t['stop_id'],'name':stops[t['stop_id']]['stop_name'],'sequence':int(t['stop_sequence'])} for t in ordered[a:b+1]]
  result['segments'].append({'route':route,'trip':trip,'direction':direction,'stops':seq})
 return result
if __name__=='__main__':
 out=Path(__file__).resolve().parents[1]/'data/route-stops.json'
 out.write_text(json.dumps(load(sys.argv[1]),ensure_ascii=False,indent=2)+'\n')
 print(out)
