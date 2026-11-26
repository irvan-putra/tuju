#!/usr/bin/env python3
"""Generate one connected, all-stops SVG. Station names/order come from GTFS.
The layout is schematic, not a geographic or live-service map.
"""
import html, json, re, textwrap
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
D=json.loads((ROOT/'data/route-stops.json').read_text())
S={s['route']:s for s in D['segments']}
R={r['key']:r for r in json.loads((ROOT/'data/return-stops.json').read_text())['segments']}
COL={'10':'#6536b0','9':'#27803c','4':'#1769aa','6':'#d36300','7E':'#00838f','4C':'#c52d36','5M':'#9045ac','4D':'#0f6e6e','S11':'#917000','S61':'#007d87'}

import math
GX=json.loads((ROOT/'data/gtfs-extract.json').read_text())
def _norm(n):return re.sub(r'[^a-z0-9]','',n.lower())
def _mdist(a,b):return math.hypot((a[0]-b[0])*111320,(a[1]-b[1])*111320*math.cos(math.radians(6.2)))
def merged_rows(out_stops,ret_names,limit=130):
 """Align the outbound stops with the return stops (listed in travel order, so reversed here)
 by real GTFS coordinates. A pair within `limit` m is one spine row; anything else keeps its own row."""
 O=[[ (GX['stops'][o['id']]['lat'],GX['stops'][o['id']]['lon']) ] for o in out_stops]
 Rv=list(reversed(ret_names))
 Rp=[[(q['lat'],q['lon']) for q in GX['name_points'][_norm(n)]] for n in Rv]
 def stem(n):
  import re as _r
  return _r.sub(r'\s+(arah\s+\w+|\d+)$','',_norm(n) if False else n.lower().strip())
 def cost(i,j):
  if stem(out_stops[i]['name'])!=stem(Rv[j]):return None
  d=min(_mdist(a,b) for a in O[i] for b in Rp[j]);return d if d<=limit else None
 n,m=len(O),len(Rv);INF=1e9
 dp=[[INF]*(m+1) for _ in range(n+1)];bk=[[None]*(m+1) for _ in range(n+1)];dp[0][0]=0
 for i in range(n+1):
  for j in range(m+1):
   if dp[i][j]>=INF:continue
   if i<n and dp[i][j]+1<dp[i+1][j]:dp[i+1][j]=dp[i][j]+1;bk[i+1][j]=(i,j,'o')
   if j<m and dp[i][j]+1<dp[i][j+1]:dp[i][j+1]=dp[i][j]+1;bk[i][j+1]=(i,j,'r')
   if i<n and j<m:
    c=cost(i,j)
    if c is not None and dp[i][j]+c/limit<dp[i+1][j+1]:dp[i+1][j+1]=dp[i][j]+c/limit;bk[i+1][j+1]=(i,j,'b',c)
 rows=[];i,j=n,m
 while i or j:
  pi,pj,k,*c=bk[i][j]
  rows.append((out_stops[pi]['name'] if k in 'ob' else None,Rv[pj] if k in 'rb' else None,int(c[0]) if c else None));i,j=pi,pj
 return rows[::-1]
def spine(rows,x,y0,dy,color,ends=()):
 """One spine, outbound labels on the right and return labels on the left. Arrows: down = outbound, up = return."""
 n=len(rows);line(x,y0,x,y0+dy*(n-1),color)
 for i,(o,r,d) in enumerate(rows):
  yy=y0+i*dy;big=i in ends
  add(f'<circle cx="{x}" cy="{yy}" r="{12 if big else 7}" fill="Canvas" stroke="{color}" stroke-width="4"/>')
  if o:text(x+23,yy+6,o,20,anchor='start',weight='600' if big else 'normal')
  if r and r!=o:text(x-23,yy+6,r,20,anchor='end',weight='600' if big else 'normal')
  if i<n-1:
   if i%3==0:tri(x,yy+dy/2,color,False)
   elif i%3==1:tri(x,yy+dy/2,color,True)
def dual(out_stops,ret_names,x,y0,dy,color,gap=24,out_right=True):
 """Two close parallel direction lines in one narrow column (the user's preferred reference).
 Outbound line on the right, down arrows, labels right; return line on the left, up arrows, labels left.
 Each direction keeps its own stop order and markers; no stop is claimed to be the same boarding point as another."""
 O=[o['name'] if isinstance(o,dict) else o for o in out_stops];Rv=list(reversed(ret_names))
 n=max(len(O),len(Rv));H=dy*(n-1)
 def col(names,cx,anchor,up):
  m=len(names);line(cx,y0,cx,y0+H,color);st=H/max(m-1,1)
  for i,nm in enumerate(names):
   yy=y0+i*st;big=i in (0,m-1)
   add(f'<circle cx="{cx}" cy="{yy:.0f}" r="{11 if big else 6}" fill="Canvas" stroke="{color}" stroke-width="4"/>')
   text(cx+(20 if anchor=='start' else -20),round(yy+6),nm,20,anchor=anchor,weight='600' if big else 'normal')
   if i<m-1 and i%3==1:tri(cx,yy+st/2,color,up)
 s=1 if out_right else -1
 col(Rv,x-s*gap,'end' if out_right else 'start',True);col(O,x+s*gap,'start' if out_right else 'end',False)
 return n
A=[]
def add(s): A.append(s)
def text(x,y,s,size=20,color='currentColor',anchor='start',weight='normal'):
 add(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{weight}">{html.escape(s)}</text>')
def mv_open(mid,label):add(f'<g class="mv" data-move="{mid}" data-label="{html.escape(label)}">')
def mv_close():add('</g>')
def line(x,y,xx,yy,color,dashed=False):
 if dashed and color=='#888':
  add(f'<path d="M {x} {y} L {xx} {yy}" fill="none" stroke="currentColor" opacity=".55" stroke-width="3" stroke-dasharray="5 7"/>');return
 add(f'<path d="M {x} {y} L {xx} {yy}" fill="none" stroke="{color}" stroke-width="{3 if dashed else 6}"'+(' stroke-dasharray="5 7"' if dashed else '')+'/>')
def tri(x,y,color,up=True):
 # Bold arrowhead marking travel direction; the Canvas halo keeps it distinct from the leg line.
 pts=f'{x} {y-13} L {x-11} {y+11} L {x+11} {y+11}' if up else f'{x} {y+13} L {x-11} {y-11} L {x+11} {y-11}'
 add(f'<path d="M {pts} Z" fill="{color}" stroke="Canvas" stroke-width="3" stroke-linejoin="round"/>')
def node(x,y,name,color,transfer=False,note=None,anchor='start',label_offset=None):
 add(f'<circle cx="{x}" cy="{y}" r="{12 if transfer else 7}" fill="Canvas" stroke="{color}" stroke-width="4"/>')
 dx=23 if anchor=='start' else -23
 for i,part in enumerate(textwrap.wrap(name,33)):
  text(x+(label_offset[0] if label_offset else dx),y+(label_offset[1] if label_offset else 6)+i*24,part,20,anchor=anchor,weight='600' if transfer else 'normal')
 if note:text(x+dx,y+32,note,15,anchor=anchor)
def chain(route,x,y,step=58,skipfirst=False,transfers=(),both=False):
 ss=S[route]['stops']; ss=ss[:8] if route=='4C' else ss; end=y+step*(len(ss)-1)
 line(x,y,x,end,COL[route])
 for i,st in enumerate(ss):
  if not(skipfirst and i==0):node(x,y+i*step,st['name'],COL[route],st['id'] in transfers,
   label_offset=(76,-19) if route=='4' and st['name']=='Halimun' else (76,6) if route=='4' and st['name']=='Galunggung' else ((76,0) if route=='6' and st['name'] in ('Setiabudi Integritas','Kuningan Madya') else None))
  if i<len(ss)-1 and i%3==0 and not (route=='4' and i==9):tri(x,y+i*step+step/2,COL[route],False)
  if both and i<len(ss)-1 and i%3==1:tri(x,y+i*step+step/2,COL[route],True)
 return end
add('<title id="all-stops-title">Outbound routes, Arkadia homebound options and the Cikini return, with intermediate stops</title>')
add('<desc id="all-stops-desc">One connected schematic, not to scale. Read each corridor leg downward in its listed direction; the 7E return leg is drawn upward on the left after a direction switch, ending its selected leg at Department of Agriculture, which is the same station as Simpang Ragunan Ar-Raudhah (rider, 19 Nov 2026). Corridor 6 links this station with Ragunan - the destination pin - in both directions, and the ride home boards corridor 6 / 6A there toward Galunggung - the direction, not the transfer - changing at Patra Kuningan to 4D for Simpang Pramuka 1; teal rings mark the 4D return stops. Gate access and fare continuity between 7E and corridor 6 are unverified. The 7A route boards at Phe Tower Kebagusan, shares the 7E stops Plaza Oleos, Kebagusan Raya, Kementan and Kementan 2, then leaves the 7E column and ends at Masjid Ar-Raudhah, the same station where the outbound 7E leg begins (rider correction, 19 Nov 2026), about 140 m on foot from Department of Agriculture via Akses A. Arrowheads mark travel direction. Hollow circles are stops; larger rings are boarding, transfer or alighting points. The corridor 4 leg uses Galunggung via Saharjo; 5M uses the via Cikini pattern. Other patterns may skip stops. The road by the venue is drawn between the two 7E directions: the pedestrian bridge between the Mujair and Phe Tower stops crosses it, the venue sits beside Phe Tower Kebagusan, and Jln. Gabus Raya (far side) and Baung (venue side) are both farther along toward Kampung Rambutan, and the Flyover Raya Bogor direction switch stays inside the paid area with no new fare (all firsthand 18 Nov 2026). The 7F homebound shares the Kayu Putih Rawasari, Pemuda Pramuka and Utan Kayu Rawamangun station areas with the outbound 10 column, then branches left toward Flyover Raya Bogor. At the 4D Rasuna Said terminus, the venue access block carries the official IDSW access guideline (idsw.dev, checked 21 Nov 2026): LRT Rasuna Said is the other official nearest stop, about 2 minutes, sharing the same pedestrian-bridge walk; the final walk runs toward Plaza Festival for about 150 m into the Gedung PPHUI complex; and the Sunday 22 November Car Free Day window 05:30-09:00 WIB bars car and motorbike gate drop-off while the LRT and corridor 6/6A keep running and drivers park at Plaza Festival. Bakoel Koffie (Cikini) is on the 5M leg: get off at Farmasi RP Soeroso, about 100 m away. The ride home boards the 5M at Kantor Pos Cikini (about 90 m from the venue) toward Kampung Melayu and changes at Megaria to 4C for Pramuka BPKP 1; it runs back up the right-hand column with its intermediate stops and rejoins the start area over the top (official GTFS trips 5M-R02 and 4C-R10, checked 22 Nov 2026; curbside feeders, so allow a fresh tap at each boarding).</desc>')
DY=1500  # band above the network for the Mall Kelapa Gading feeders (26 Nov, merged into the main map)
add(f'<g transform="translate(0 {DY})">')
SH=420  # whole network shifts right so the 7F homebound column can sit at the far left
add(f'<g transform="translate({SH} 0)">')
add('<g transform="translate(700 0)">')
node(700,155,'Green Pramuka area','#777',True)
for x in [-530,630,1200]:line(700,170,x,230,'#888',True)
text(-280,208,'walk ~230 m',16);text(655,204,'walk to boarding point',16);text(1230,204,'walk ~850 m',16)
add('<g transform="translate(-600 0)">')
text(95,-62,'10 ↓ PGC',19,COL['10'],weight='600');text(225,-62,'9 ↓ Pluit',19,COL['9'],weight='600')
text(40,-62,'10 ↑ Tanjung Priok',19,COL['10'],anchor='end',weight='600')
text(-170,-62,'9 ↑ Pinang Ranti',19,COL['9'],anchor='end',weight='600')
y10=chain('10',70,240,55,transfers=['G00473','G00718'],both=False)
# 7F homebound shares the top three station areas of this column (same stop names in
# the official 10 GTFS pattern and the 7F Juanda-direction listing). Its own stops
# branch off at Utan Kayu Rawamangun toward Flyover Raya Bogor; drawn in the outer section.
text(95,y10+36,'10 and 9 use different GTFS platform IDs here;',14)
text(95,y10+52,'paid-area interchange not verified',14)
y9=chain('9',70,y10,65,True,['G00403'],both=False)
# Return legs: own stops and order from GTFS trips 9-R02 / 10-R02, drawn as a second line 36 units left.
RCP={r['key']:r for r in json.loads((ROOT/'data/return-central-park.json').read_text())['segments']}
xr=34
def rnode(y,name,col,big=False):
 add(f'<circle cx="{xr}" cy="{y}" r="{12 if big else 7}" fill="Canvas" stroke="{col}" stroke-width="4"/>')
 for k,part in enumerate(textwrap.wrap(name,40 if 'Cawang Sentral ·' in name else 20)):text(xr-23,y+6+k*22,part,19,anchor='end',weight='600' if big else 'normal')
r9=RCP['9-return']['stops'];r10=RCP['10-return']['stops']
ycs9=y10+16;ycs10=y10-16
line(xr,ycs9,xr,y9,COL['9']);line(xr,240,xr,ycs10,COL['10'])
add(f'<path d="M {xr} {ycs10} L {xr} {ycs9}" fill="none" stroke="#888" stroke-width="3" stroke-dasharray="5 7"/>')
for j,st in enumerate(r9):
 yy=y9-65*j if j<len(r9)-1 else ycs9
 rnode(yy,st['name'] if j<len(r9)-1 else 'Cawang Sentral · 9',COL['9'],j==len(r9)-1 or j==0)
 if j%3==2 and j<len(r9)-1:tri(xr,yy-32,COL['9'])
for m,st in enumerate(r10):
 yy=y10-55*m if m else ycs10
 rnode(yy,st['name'] if m else 'Cawang Sentral · 10',COL['10'],m==0 or m==len(r10)-1)
 if m%3==2:tri(xr,yy+27,COL['10'])
text(xr-23,y10+40,'interchange unverified',14,anchor='end')
# Centennial is a walk off existing corridor 9, not a new transit stop.
cy=1450; cx=580
mv_open('centennial-tower','Centennial Tower pin and notes')
add(f'<rect x="{cx-9}" y="{cy}" width="18" height="18" rx="3" fill="#2e9e50"/>')
text(cx,cy+52,'Centennial Tower',24,'#2e9e50',weight='600',anchor='middle')
text(cx,cy+82,'out: Denpasar Arah Barat',16,anchor='middle')
text(cx,cy+108,'walk ~420 m / 6 min',16,anchor='middle')
text(cx,cy+142,'home: Denpasar Arah Timur',16,anchor='middle')
text(cx,cy+168,'walk ~340 m / 5 min',16,anchor='middle')
text(cx,cy+200,'crossings / gates unverified',15,anchor='middle')
mv_close()
dout=y10+65*next(i for i,st in enumerate(S['9']['stops']) if st['name']=='Denpasar Arah Barat')
dhome=y9-65*next(i for i,st in enumerate(r9) if st['name']=='Denpasar Arah Timur')
add(f'<path d="M 82 {dout+22} L 400 {dout+22} L 400 {cy-30} L {cx} {cy-30} L {cx} {cy}" fill="none" stroke="currentColor" opacity=".55" stroke-width="3" stroke-dasharray="5 7"/>')
add(f'<path d="M {xr-10} {dhome+12} L {xr-10} {dhome+31} L 415 {dhome+31} L 415 {cy-16} L {cx-9} {cy-16} L {cx-9} {cy}" fill="none" stroke="currentColor" opacity=".55" stroke-width="3" stroke-dasharray="5 7"/>')
mv_open('central-park','Central Park Mall pin')
line(70,y9+12,70,y9+75,'#888',True)
text(95,y9+63,'Walk ~350 m',16);text(95,y9+96,'Central Park Mall',24,'#2e9e50',weight='600')
mv_close()
# Return from Central Park (rider asked 23 Nov 2026): the same station areas, drawn once with
# arrows both ways. GTFS 9-R02 and 10-R02 use the opposite-direction stop names (data/return-central-park.json).
for k,t in enumerate(['Return (left line): board 9 ↑ Pinang Ranti at Tanjung Duren Arah Timur.',
 'The road crossing from the mall to that stop is unverified; ~100 m from the',
 'Arah Barat stop, walk from the mall not measured.',
 'Return stops are the GTFS opposite-direction stops (Arah Timur / Selatan),',
 'drawn with their own order, not paired with the outbound stops.',
 '9 (ends) and 10 (starts) use two Cawang Sentral stops; the interchange between',
 'them is unverified. 10 ↑ Tanjung Priok ends at Kayu Putih Rawasari.',
 'GTFS trips 9-R02 and 10-R02, checked 23 Nov 2026. Fares not checked.']):
 text(95,y9+134+k*22,t,15)
add('</g>')
text(585,270,'4 + 4D',22,COL['4'],anchor='end',weight='600')
y4=chain('4',630,240,62,transfers=['B08048P','G00216','G00202'])
text(655,273,'temporary stop · 4 toward Galunggung via Saharjo',14)
text(655,288,'4D toward Patra Kuningan',14)
# Matraman branches into curbside 5M. The ring is not a paid-area transfer.
mat=240+next(i for i,s in enumerate(S['4']['stops']) if s['id']=='G00216')*62
add(f'<path d="M 630 {mat+12} L 630 {mat+30} L 1000 {mat+30} L 1040 {mat+70}" fill="none" stroke="currentColor" opacity=".55" stroke-width="3" stroke-dasharray="5 7"/>')
node(1040,mat+70,'Matraman 3',COL['5M'],True,anchor='end')
text(1040,mat+110,'Tap out; ~1 min walk',15,anchor='end')
# Firsthand 18 Nov 2026: no additional fare for the 4 to 6 change at Galunggung.
line(630,y4+12,630,y4+110,'#888',True)
text(712,y4+50,'4 to 6: no additional',15);text(712,y4+72,'fare (firsthand)',15)
text(585,y4+145,'6',22,COL['6'],anchor='end',weight='600')
y6=chain('6',630,y4+120,61,skipfirst=True,transfers=['G00204','G00243'])
line(630,y6+12,630,y6+110,'#888',True)
# Station to Masjid Ar-Raudhah walk; its labels sit left of the link (below).
# Alias carried by the left-side note below; keep clear of the 6 tail.
text(585,y6+174,'7E',22,COL['7E'],anchor='end',weight='600')
y7=chain('7E',630,y6+120,60,transfers=['B07989P','B01062P'])
# The 7E continues toward Kampung Rambutan past the Arkadia stop.
line(630,y7+12,630,y7+268,COL['7E'])
# The road between the two 7E sides by the venue (firsthand 18 Nov 2026):
# Ragunan-bound on the venue side (left column), Kampung Rambutan-bound far side.
# Along the road toward Kampung Rambutan: Jln. Mujair Raya, then the footbridge,
# then Phe Tower Kebagusan with the venue beside it, then Jln. Gabus Raya on the
# far side, then Baung on the venue side.
py=y7-26
bq=y7+52
add(f'<rect x="306" y="{y7-52}" width="318" height="116" fill="currentColor" opacity="0.12"/>')
add(f'<line x1="465" y1="{y7-52}" x2="465" y2="{y7+64}" stroke="currentColor" opacity="0.35" stroke-width="3" stroke-dasharray="8 8"/>')
add(f'<text x="292" y="{y7-58}" font-size="13" fill="currentColor" text-anchor="end">Via footbridge</text>')
add(f'<text x="618" y="{y7-62}" font-size="13" font-style="italic" opacity=".65" fill="currentColor" text-anchor="end">far side</text>')
add(f'<text x="356" y="{y7-62}" font-size="13" font-style="italic" opacity=".65" fill="currentColor" text-anchor="start">venue side</text>')
# Pedestrian bridge across the road, between the Mujair and Phe Tower stops.
add(f'<line x1="306" y1="{y7-48}" x2="624" y2="{y7-48}" stroke="currentColor" opacity=".55" stroke-width="2"/>')
add(f'<line x1="306" y1="{y7-38}" x2="624" y2="{y7-38}" stroke="currentColor" opacity=".55" stroke-width="2"/>')
for bx in range(318,624,18): add(f'<line x1="{bx}" y1="{y7-48}" x2="{bx}" y2="{y7-38}" stroke="currentColor" opacity=".55" stroke-width="2"/>')
# One shared venue marker beside the Phe Tower stop; all walks arrive at the same place.
mv_open('arkadia','De Entrance - Arkadia Green Park marker')
add(f'<rect x="457" y="{y7-34}" width="16" height="16" rx="3" fill="#2e9e50"/>')
text(465,y7+32,'De Entrance -',19,'#2e9e50',weight='600',anchor='middle')
text(465,y7+56,'Arkadia Green Park',19,'#2e9e50',weight='600',anchor='middle')
text(465,y7+78,'same side as Phe Tower + Baung',13,anchor='middle')
mv_close()
add(f'<path d="M 306 {y7-38} C 340 {y7-32}, 410 {y7-28}, 449 {y7-26}" fill="none" stroke="currentColor" opacity=".55" stroke-width="3" stroke-dasharray="5 7"/>')
add(f'<path d="M 312 {py+2} C 360 {py-2}, 410 {py-2}, 449 {py+2}" fill="none" stroke="currentColor" opacity=".55" stroke-width="3" stroke-dasharray="5 7"/>')
add(f'<path d="M 312 {bq+2} C 350 {bq-20}, 410 {y7-8}, 449 {y7-18}" fill="none" stroke="currentColor" opacity=".55" stroke-width="3" stroke-dasharray="5 7"/>')
for i,name in enumerate(['Jln. H. Saidi','Jln. Nangka 1','Jln. Muara 1','Plaza Pp Condet 2','RSUD Pasar Rebo 2']):
 node(630,y7+56+i*44,name,COL['7E'])
fy=y7+280
node(630,fy,'Flyover Raya Bogor - get off',COL['7E'],True)
text(607,fy-120,'Rode past Jln. Gabus Raya?',14,anchor='end')
text(607,fy-100,'Ride on to Flyover Raya Bogor and',13,anchor='end')
text(607,fy-84,'switch direction there - inside the',13,anchor='end')
text(607,fy-68,'paid area, no exit or new fare.',13,anchor='end')
for ay in (y7-150,y7+28,y7+122,y7+210,y7+254):tri(630,ay,COL['7E'],up=False)
# Direction switch: firsthand 18 Nov 2026 the link stays inside the paid area.
ry=y7+452
add(f'<path d="M 606 {fy+10} C 455 {fy+125}, 395 {ry-30}, 346 {ry+2}" fill="none" stroke="currentColor" opacity=".55" stroke-width="3" stroke-dasharray="5 7"/>')
add(f'<path d="M 312 {ry+2} L 344 {ry-11} L 344 {ry+15} Z" fill="currentColor" opacity=".6" stroke="Canvas" stroke-width="3" stroke-linejoin="round"/>')
add(f"<circle cx='300' cy='{ry}' r='12' fill='Canvas' stroke='{COL['7E']}' stroke-width='4'/>")
text(277,ry+6,'Flyover Raya Bogor',20,weight='600',anchor='end')
text(277,ry+30,'board toward Ragunan',13,anchor='end')
text(277,ry+46,'inside the paid area (firsthand)',13,anchor='end')
# Return leg runs back UP the left column, toward the venue.
line(300,py+12,300,ry-12,COL['7E'])
for i,name in enumerate(['Gg. Nanas','Jln. Nangka Raya','Telkomsel Jln. Nangka','ACC Simatupang','Muara Dalam','Plaza Pp Condet 1','SMAN 104','RSUD Pasar Rebo 1']):
 node(300,bq+44+i*44,name,COL['7E'],anchor='end')
for ay in (y7+24,y7+74,y7+162,y7+250,y7+338,y7+426):tri(300,ay,COL['7E'])
node(300,py,'Phe Tower Kebagusan',COL['7E'],True,anchor='end')
text(277,py+26,'get off - right by the venue',13,anchor='end')
node(300,bq,'Baung - get off',COL['7E'],True,anchor='end')
text(277,bq+30,'Walk ~4 min (285 m)',13,anchor='end')
# 4C is the straight red spine. 5M leaves it as a purple branch.
# Local coordinates in the existing translated group; global red x = 2600 / 2672.
red=COL['4C']; purple=COL['5M']; xo=1480; xh=1552; xp=1516; po=2320; ph=po+72  # 5M directions paired like S11/S16 (user feedback)
all4=S['4C']['stops']; step4=70
mas=240+next(i for i,st in enumerate(all4) if st['id']=='B02350P')*step4
line(xo,240,xo,240+(len(all4)-1)*step4,red)
for i,st in enumerate(all4):
 yy=240+i*step4
 node(xo,yy,st['name'],red,st['id'] in ('B07260P','B05812P','B05391P','B05775P','B00221P'),anchor='end')
 if i and abs(yy-step4/2-(mas-35))>1:tri(xo,yy-step4/2,red,False)  # the Matraman 3 link hops the outbound line in this gap
add(f'<path d="M 1040 {mat+70} L 1040 {mas-35} L {xo+22} {mas-35} L {xp} {mas}" fill="none" stroke="{purple}" stroke-width="6"/>')
text(xo-24,180,'4C ↓ Bundaran Senayan',20,red,weight='600',anchor='end')
# Matraman 3 joins the shared 4C/5M section at Masjid Jami Matraman.
shared_end=240+next(i for i,st in enumerate(all4) if st['id']=='B05391P')*step4
line(xp,mas,xp,shared_end,purple)
for i,st in enumerate(all4):
 yy=240+i*step4
 if mas<=yy<=shared_end:
  add(f"<circle cx='{xo}' cy='{yy}' r='{17 if st['id'] in ('B05812P','B05391P') else 13}' fill='none' stroke='{purple}' stroke-width='3.5'/>")
  if yy>mas:tri(xp,yy-step4/2,purple,False)
text(xh+30,mas-30,'4C + 5M shared stops (middle line)',15,purple)
# Purple outbound branches at SMPN 8, rather than bending the red trunk.
out5=S['5M']['stops']; idx5=next(i for i,st in enumerate(out5) if st['id']=='B05391P');tail5=out5[idx5+1:]
pstart=shared_end+115
for i,st in enumerate(tail5):
 yy=pstart+i*61
 if i:line(po,yy-61,po,yy,purple)
 node(po,yy,st['name'],purple,st['id']=='B00346P' or i==len(tail5)-1,anchor='end')
 if i:tri(po,yy-30,purple,False)
text(po-24,pstart-35,'5M ↓ Tanah Abang · via Cikini',18,purple,weight='600',anchor='end')
pbottom=pstart+(len(tail5)-1)*61
mv_open('markas-indonesia','Markas Indonesia label')
text(po+24,pbottom+46,'Walk ~300 m',16)
text(po+24,pbottom+76,'Markas Indonesia',23,'#2e9e50',weight='600')
mv_close()
# Independent red homebound is straight from Bundaran Senayan 2 to Pramuka BPKP 1.
home4=list(reversed(R['4C-Senayan-return']['stops'][:-1]+R['4C-GI-return']['stops'][:-1]+R['4C-return']['stops']))
line(xh,240,xh,240+(len(home4)-1)*step4,red)
for i,name in enumerate(home4):
 yy=240+i*step4
 node(xh,yy,name,red,name in ('Pramuka BPKP 1','Megaria','Tosari 2','Bundaran Senayan 2'))
 if i and abs(yy-step4/2-(shared_end+35))>1 and yy not in (240+home4.index('Tosari 2')*step4,240+home4.index('Tosari 2')*step4+step4):tri(xh,yy-step4/2,red)  # GI walk links leave through the gaps above and below Tosari 2  # the 5M branch hops the homebound line in this gap
text(xh+24,180,'4C ↑ JIEP · home',20,red,weight='600')
add(f'<path d="M {xh} 228 L {xh} 130 L 700 130 L 700 141" fill="none" stroke="currentColor" opacity=".55" stroke-width="3" stroke-dasharray="5 7"/>')
text(1250,118,'walk ~850 m home',15)
# Purple return joins the red homebound at Megaria; different stops stay separate.
add(f'<path d="M {xp} {shared_end} L {xp} {shared_end+35} L {po} {shared_end+35} L {po} {pstart}" fill="none" stroke="Canvas" stroke-width="13"/>')
add(f'<path d="M {xp} {shared_end} L {xp} {shared_end+35} L {po} {shared_end+35} L {po} {pstart}" fill="none" stroke="{purple}" stroke-width="6"/>')
yme=240+home4.index('Megaria')*step4
return5=list(reversed(R['5M-return']['stops']))
# Straight Pegangsaan Timur to Megaria join; clears the Megaria and St. Cikini Selatan
# labels (user feedback 23 Nov: the old sweep struck the St. Cikini Selatan label and
# read as if 5M served it). Ring marks the change to 4C.
add(f'<path d="M {ph} {yme+110} L {xh} {yme+14}" fill="none" stroke="Canvas" stroke-width="13"/>')
add(f'<path d="M {ph} {yme+110} L {xh} {yme+14}" fill="none" stroke="{purple}" stroke-width="6"/>')
add(f"<circle cx='{xh}' cy='{yme}' r='17' fill='none' stroke='{purple}' stroke-width='3.5'/>")
# Explanation at the spot he circled (23 Nov): the join line passing near St. Cikini
# Selatan read as a 5M stop. Same register as the S61 curbside note.
text(1780,yme-24,'Get off the 5M at Megaria: transfer to the red 4C for home.',16)
text(1780,yme-1,'St. Cikini Selatan is 4C only; the purple line passes, no stop.',16)
text(1780,yme+22,'Curbside transfer; allow a fresh tap/fare.',16)
for i,name in enumerate(return5[1:]):
 yy=yme+110+i*105
 if i:line(ph,yy-105,ph,yy,purple)
 node(ph,yy,name,purple,i==len(return5)-2)
 if i:tri(ph,yy-52,purple)
text(ph+24,yme+75,'5M ↑ Kampung Melayu; change at Megaria',16,purple)
# Same Bakoel destination, linked to its two distinct roadside stops.
bkout=pstart+next(i for i,st in enumerate(tail5) if st['id']=='B00346P')*61
bkhome=yme+110+(len(return5)-2)*105
bpx=ph+90; bpy=bkout+17  # pin sits right of the paired 5M columns, below the return leg's end
mv_open('bakoel','Bakoel Koffie pin and notes')
add(f'<rect x="{bpx}" y="{bpy}" width="18" height="18" rx="3" fill="#2e9e50"/>')
text(bpx,bpy+52,'Bakoel Koffie',23,'#2e9e50',weight='600')
text(bpx,bpy+80,'5M out: Farmasi RP Soeroso',14);text(bpx,bpy+98,'walk ~100 m',14)
text(bpx,bpy+121,'5M home: Kantor Pos Cikini',14);text(bpx,bpy+139,'walk ~90 m',14)
mv_close()
add(f'<path d="M {po+8} {bkout+8} L {po+22} {bkout+26} L {bpx} {bkout+26}" fill="none" stroke="#888" stroke-width="3" stroke-dasharray="5 7"/>')
add(f'<path d="M {ph+8} {bkhome+8} L {ph+22} {bkhome+26} L {bpx+9} {bkhome+26} L {bpx+9} {bpy}" fill="none" stroke="#888" stroke-width="3" stroke-dasharray="5 7"/>')
# GI remains a walk from Tosari 3 out / Tosari 2 home, not a new bus stop.
yto=240+next(i for i,st in enumerate(all4) if st['id']=='B05775P')*step4
yth=240+home4.index('Tosari 2')*step4
# GI note sits in the empty space right of the Tosari labels, beside the 5M outbound column.
gcx=1906; giy=yth+15
mv_open('grand-indonesia','Grand Indonesia pin and notes')
add(f'<rect x="{gcx-9}" y="{giy}" width="18" height="18" rx="3" fill="#2e9e50"/>')
add(f'<text aria-label="Grand Indonesia" x="{gcx}" y="{giy+46}" font-size="36" fill="#2e9e50" text-anchor="middle" font-weight="600"><tspan x="{gcx}">Grand </tspan><tspan x="{gcx}" dy="40">Indonesia</tspan></text>')
text(gcx,giy+122,'out: Tosari 3',20,anchor='middle');text(gcx,giy+148,'~640 m / 8 min',20,anchor='middle')
text(gcx,giy+182,'home: walk to Tosari 2',20,anchor='middle');text(gcx,giy+208,'check crossing',20,anchor='middle')
mv_close()
# Out: from Tosari 3, up between the two 4C lines, across the return line above Tosari 2, then down into the pin.
add(f'<path d="M {xo+13} {yto} L {xo+30} {yto} L {xo+30} {yth-35} L {gcx} {yth-35} L {gcx} {giy}" fill="none" stroke="currentColor" opacity=".55" stroke-width="3" stroke-dasharray="5 7"/>')
# Home: from Tosari 2 out through the label gap below it.
add(f'<path d="M {xh+8} {yth+8} L {xh+22} {yth+24} L {gcx-9} {yth+24}" fill="none" stroke="currentColor" opacity=".55" stroke-width="3" stroke-dasharray="5 7"/>')
# J.CO Reserve (AI Hotel Thamrin) sits by Tosari, stacked under the GI block (user request 23 Nov).
jcx=1906; jy=1500
mv_open('jco-reserve','J.CO Reserve pin and notes')
add(f'<rect x="{jcx-9}" y="{jy}" width="18" height="18" rx="3" fill="#2e9e50"/>')
text(jcx,jy+70,'J.CO Reserve',23,'#2e9e50',weight='600',anchor='middle')
text(jcx,jy+92,'AI Hotel Thamrin',14,anchor='middle')
text(jcx,jy+122,'out: Tosari 3 · ~700 m',16,anchor='middle')
text(jcx,jy+144,'home: walk to Tosari 2 · ~200 m',16,anchor='middle')
mv_close()
# Out: from Tosari 3 (fork beside the GI stub), up between the 4C pair to the shared
# walk trunk row. Both links end at the same pin, so the shared trunk is unambiguous.
add(f'<path d="M {xo+13} {yto} L {xo+44} {yto} L {xo+44} {yth+50} L {xh+13} {yth+50}" fill="none" stroke="currentColor" opacity=".55" stroke-width="3" stroke-dasharray="5 7"/>')
# Home: from the Tosari 2 ring bottom, right across the gap below Tosari 2 (clear of the
# St. Sudirman 2 label box and ring), down at x=1730 (clear of the GI title box), pin top.
add(f'<path d="M {xh} {yth+12} L {xh+13} {yth+50} L 1742 {yth+50} L 1742 {jy-30} L {jcx} {jy-30} L {jcx} {jy}" fill="none" stroke="currentColor" opacity=".55" stroke-width="3" stroke-dasharray="5 7"/>')
# Autograph shares the Tosari walk trunk, with its own venue pin.
ax=1940; ay=1750
mv_open('autograph-tower','Autograph Tower pin and notes')
add(f'<rect x="{ax-9}" y="{ay}" width="18" height="18" rx="3" fill="#2e9e50"/>')
text(ax,ay+56,'Autograph Tower',22,'#2e9e50',weight='600',anchor='middle')
text(ax,ay+84,'Thamrin Nine · Academy @ UC',14,anchor='middle')
text(ax,ay+114,'out: Tosari 3 · ~870 m / 11 min',14,anchor='middle')
text(ax,ay+142,'home: Tosari 2 · ~300 m / 4 min',14,anchor='middle')
text(ax,ay+174,'entrance / crossings unverified',14,anchor='middle')
mv_close()
add(f'<path d="M 1742 {jy-30} L 1742 {ay-30} L {ax} {ay-30} L {ax} {ay}" fill="none" stroke="currentColor" opacity=".55" stroke-width="3" stroke-dasharray="5 7"/>')
# 4D shares the first ten stops with corridor 4 (same stop IDs in data/route-stops.json), so it branches off the drawn 4 column at Halimun.
# Stop order for 4D is NOT from the GTFS snapshot (see data/route-stops.json).
s4=[x['id'] for x in S['4']['stops']]; s4d=S['4D']['stops']
nshared=0
while nshared<len(s4d) and nshared<len(s4) and s4d[nshared]['id']==s4[nshared]:nshared+=1
assert nshared==10,nshared
hy=240+(nshared-1)*62
bx=930; by=hy+62
add(f'<path d="M 630 {hy+14} L {bx} {by}" fill="none" stroke="{COL["4D"]}" stroke-width="6"/>')
# Keep Halimun and its note to the right of the return arrow, above the branch.
text(704,hy+14,'4D leaves here; 4 goes on to Galunggung',15,weight='600')
tail=s4d[nshared:]
y4d=by+58*(len(tail)-1)
line(bx,by,bx,y4d,COL['4D'])
for i,st in enumerate(tail):node(bx,by+i*58,st['name'],COL['4D'],i==len(tail)-1)
text(bx-25,by+30,'4D',22,COL['4D'],anchor='end',weight='600')
mv_open('plaza-festival','Plaza Festival / Usmar Ismail Hall notes')
line(bx,y4d+12,bx,y4d+100,'#888',True)
text(bx+25,y4d+62,'Exit Akses E, walk ~2 min',17)
text(bx+25,y4d+95,'Plaza Festival /',22,'#2e9e50',weight='600')
text(bx+25,y4d+121,'Usmar Ismail Hall',22,'#2e9e50',weight='600')
text(bx+25,y4d+145,'stop order: jaGOdetabek /',14)
text(bx+25,y4d+163,'halte.id, not GTFS',14)
# Official IDSW venue access (idsw.dev/access-guideline, checked 21 Nov 2026).
# The LRT station is the other official nearest stop and shares the same JPO
# walk; the filled square + dashed link is a walk connection, NOT a TJ transfer.
# Car Free Day bars car/motorbike gate drop-off Sunday morning; LRT + 6/6A run.
lrtc='#b03a2e'
line(bx,y4d+112,bx,y4d+184,'#888',True)
add(f'<rect x="{bx-11}" y="{y4d+186}" width="22" height="22" rx="5" fill="{lrtc}"/>')
text(bx+25,y4d+204,'LRT Rasuna Said',16,lrtc,weight='600')
text(bx+25,y4d+226,'~2 min · same JPO walk (official)',13,lrtc)
for k,t in enumerate(['Final walk (official):','JPO toward Plaza Festival','~150 m, enter Gedung','PPHUI complex']):
 text(bx+25,y4d+256+k*20,t,14,weight='600' if k==0 else 'normal')
for k,t in enumerate(['CFD Sun 22 Nov','05:30-09:00: no car /','motorbike drop-off at','the gate; LRT + 6/6A','keep running; park at','Plaza Festival']):
 text(bx+25,y4d+362+k*22,t,14,weight='600')
text(bx+25,y4d+518,'official: idsw.dev guide,',13)
text(bx+25,y4d+538,'checked 21 Nov 2026',13)
mv_close()
# Shared outbound/return station spine. Return-only stop sequences are local branches,
# not an independently duplicated vertical. Common names denote the station area,
# not a claim that opposite-direction platforms or fare gates are identical.
# 4 return: the top curbside stop and middle approach differ.
line(360,240,630,302,COL['4'])
node(360,240,'Simpang Pramuka 1',COL['4'],True,anchor='end')
tri(490,270,COL['4'])
text(337,270,'4 ↑ Pulo Gadung · return-side exit',15,anchor='end')
line(360,228,700,167,'#888',True)
text(337,300,'Exact walk to Green Pramuka unchecked',14,anchor='end')
# Shared 4 station areas: Pramuka Sari, Utan Kayu, Pasar Genjing.
for yy in (333,395):tri(615,yy,COL['4'])
# Outbound 4/4D uses Matraman, Tegalan, Kesatrian and Temporer 2;
# homebound 4 branches through Flyover Pramuka and Temporer 1.
add(f'<path d="M 630 736 L 360 674 L 360 488 L 630 426" fill="none" stroke="{COL["4"]}" stroke-width="6"/>')
node(360,520,'Flyover Pramuka',COL['4'],anchor='end')
node(360,650,'Halte Manggarai Temporer 1',COL['4'],anchor='end')
tri(360,580,COL['4'])
for yy in (767,):tri(615,yy,COL['4'])
text(337,710,'4 ↑ return-only approach',15,COL['4'],anchor='end')
# 6 shares every drawn station area with its return except Flyover Kuningan.
# Galunggung is a single station node for the 4 and 6 transfer.
for yy in (1071,1132,1193,1254,1315,1376,1437,1498,1559,1620,1681,1742,1803,1864,1925):
 tri(615,yy,COL['6'])
add(f'<path d="M 630 1041 L 360 1011 L 360 900 L 618 860" fill="none" stroke="{COL["6"]}" stroke-width="6"/>')
node(360,948,'Flyover Kuningan',COL['6'],anchor='end')
tri(360,978,COL['6'])
text(337,1035,'6 ↑ Galunggung',18,COL['6'],anchor='end',weight='600')
text(337,1062,'Return-only Flyover Kuningan branch',14,anchor='end')
text(342,966,'6 → 4 at Galunggung: alternative;',13,anchor='end');text(342,984,'check platform, no fare promise',13,anchor='end')
# Chosen return transfer (rider's Maps listing, 19 Nov 2026): leave corridor 6 at
# Patra Kuningan and continue on 4D to Simpang Pramuka 1. Galunggung is only the
# 6 direction, not the transfer point. The 4D return rides the drawn corridor 6
# spine from Patra Kuningan up to Kuningan Madya (rings), then rejoins the 4
# corridor at Halimun; from Halimun it matches the drawn 4 return path exactly
# (Pasar Rumput, Manggarai Temporer 1, Flyover Pramuka, Pasar Genjing, Utan Kayu,
# Pramuka Sari, Simpang Pramuka 1), so rings mark the shared stops, no redraw.
for yy in (1346,1285,1224,1163,1102,798,736,426,364,302):
 add(f"<circle cx='630' cy='{yy}' r='13' fill='none' stroke='{COL['4D']}' stroke-width='3'/>")
for yy in (650,520,240):
 add(f"<circle cx='360' cy='{yy}' r='13' fill='none' stroke='{COL['4D']}' stroke-width='3'/>")
# Connect at the Kuningan Madya ring (user feedback 23 Nov: the bare vertical stopped
# 36 units right of the ring and read as unconnected).
add(f'<path d="M 630 1102 L 666 1102 L 666 818" fill="none" stroke="{COL["4D"]}" stroke-width="6"/>')
tri(666,850,COL['4D'])
text(585,1090,'4D ↑ return to Halimun · no stops between',14,COL['4D'],anchor='end')
text(655,1378,'chosen return: change 6 → 4D here (19 Nov)',14,COL['4D'])
text(337,560,'teal rings: 4D return stops (Maps, 19 Nov)',13,COL['4D'],anchor='end')
# Selected return itinerary corrected 19 Nov 2026 (rider): the 6N continuation was
# a red herring and is removed. The Ragunan destination pin is reached on foot via
# the Simpang Ragunan Ar-Raudhah station area, and the ride home boards corridor 6
# there toward Galunggung. Department of Agriculture is the Maps name for the
# Simpang Ragunan boarding area; the drawn walks keep gate and fare continuity
# unverified. A Ragunan headsign is still not evidence of a direct ride to the pin.
line(300,2082,300,py-12,COL['7E'])
for yy,name in zip([2126,2182,2238,2294],['Kementan 2','Kementan','Kebagusan Raya','Plaza Oleos']):
 node(300,yy,name,COL['7E'],anchor='end')
for yy in (2098,2154,2210,2266,2322):tri(300,yy,COL['7E'])
# Rider, 19 Nov 2026: Department of Agriculture and Simpang Ragunan Ar-Raudhah
# are ONE station - the drawn corridor 6 terminus node on the shared spine. The
# 7E return leg curves in from Kementan 2 and ends on that same node; no separate
# Department node is drawn. Corridor 6 links the station with Ragunan - the
# destination pin - in both directions, drawn as a short 6 tail, arrows both ways.
add(f'<path d="M 300 2126 C 300 2020, 360 1966, 606 1962" fill="none" stroke="{COL["7E"]}" stroke-width="6"/>')
add(f'<path d="M 606 1962 L 584 1954 L 584 1970 Z" fill="{COL["7E"]}" stroke="Canvas" stroke-width="3" stroke-linejoin="round"/>')
add(f'<path d="M 642 1968 L 788 2032" fill="none" stroke="{COL["6"]}" stroke-width="6"/>')
add(f'<path d="M 728 2006 L 705 2003 L 713 1985 Z" fill="{COL["6"]}" stroke="Canvas" stroke-width="2" stroke-linejoin="round"/>')
add(f'<path d="M 668 1982 L 670 1999 L 678 1981 Z" fill="{COL["6"]}" stroke="Canvas" stroke-width="2" stroke-linejoin="round"/>')
mv_open('ragunan','Ragunan destination pin')
node(800,2040,'Ragunan (destination pin)',COL['6'],True)
text(660,2056,'6 ↔ both directions',13,COL['6'])
mv_close()
# One node, both names; boarding and walk notes sit left of the halte walk link.
text(585,1914,'board 6 / 6A ↑ toward Galunggung',14,COL['6'],anchor='end')
text(585,1938,'= Department of Agriculture · same station · 7E leg ends here',14,anchor='end')
text(585,2030,'walk ~140 m / 3 min · Akses A',14,anchor='end')
text(585,2054,'7E boards curbside · fresh fare (firsthand)',13,anchor='end')
text(18,2350,'7E ↑ Ragunan headsign',17,COL['7E'],anchor='end',weight='600')
# 7A / D21 is an alternative curbside arrival, not a paid-area shortcut.
c7a='#527b9c'
# 7A runs from Phe Tower over the same first stops as 7E, then leaves the 7E column
# after Kementan 2 and ends at Masjid Ar-Raudhah. Rider correction 19 Nov 2026:
# that is the same station where the outbound 7E leg begins, so 7A ends on the
# drawn Masjid Ar-Raudhah node instead of a duplicate. D21 appears in the label
# only because the same Maps result named it; not verified identical.
my=y6+120  # Masjid Ar-Raudhah, first stop of the drawn 7E column
add(f'<path d="M 346 2126 C 420 2126, 490 {my}, 600 {my}" fill="none" stroke="{c7a}" stroke-width="6"/>')
add(f'<path d="M 600 {my} L 578 {my-8} L 578 {my+8} Z" fill="{c7a}" stroke="Canvas" stroke-width="3" stroke-linejoin="round"/>')
line(346,py-4,346,2118,c7a)
for yy in (2126,2182,2238,2294):add(f"<circle cx='300' cy='{yy}' r='13' fill='none' stroke='{c7a}' stroke-width='3'/>")
add(f"<circle cx='300' cy='{py}' r='17' fill='none' stroke='{c7a}' stroke-width='3'/>")
add(f"<circle cx='630' cy='{my}' r='17' fill='none' stroke='{c7a}' stroke-width='3'/>")
text(655,my+36,'7A / D21 get off here · same station',13,c7a)
text(-250,2150,'7A / D21 boards at Phe Tower: same stops as 7E',14,c7a)
text(-250,2170,'Plaza Oleos, Kebagusan Raya, Kementan, Kementan 2,',13,c7a)
text(-250,2190,'then ends at Masjid Ar-Raudhah - the same station',13,c7a)
text(-250,2210,'as the 7E start (blue rings; selected trip only)',13,c7a)
# Station to Masjid walk is the vertical link at the 6 terminus; labeled there.
# Long text belongs outside the stop columns.
add('</g>')
def return_chain(key,x,bottom,top,color,skipfirst=False):
 ss=R[key]['stops']; step=(bottom-top)/(len(ss)-1)
 line(x,bottom,x,top,color)
 for i,name in enumerate(ss):
  yy=bottom-i*step
  if not(skipfirst and i==0):node(x,yy,name,color,i in (0,len(ss)-1))
  if i<len(ss)-1:tri(x,yy-step/2,color)
 return top
text(60-SH,45-DY,'One network · out and home',30,weight='600')
text(60-SH,80-DY,'Shared 4 / 6, 9 / 10 and 10 / 7F spines · down outbound, up homebound · only different stops branch.',19)
text(60-SH,140-DY,'Line hops / gaps: no connection. Rings: stops and actual joins.',19)
text(60-SH,110-DY,'Station areas are shared, not necessarily platforms. 7E keeps its different roadside stops.',17)
# ---- Mall Kelapa Gading -> home, merged into the main map (Irvan, 26 Nov: "merge the maps") ----
# The feeders sit in the band above the network and join the existing corridor 10 and corridor 4
# columns at their real stops, so those stops are drawn once. Stop lists: data/route-stops.json (GTFS 26 Nov 2026).
X10,X4,X59,YT=170,1330,2000,-1166
c12,cB,cA='#5a8f5a','#c2185b','#7a5230'; c10=COL['10']; c4c=COL['4']
def _ring(x,y,c,big):add(f'<circle cx="{x}" cy="{y:.0f}" r="{12 if big else 7}" fill="Canvas" stroke="{c}" stroke-width="4"/>')
def _col(x,ys,names,c,anchor='start',bigs=(),arrows=True,wrapn=33):
 for k,(y,nm) in enumerate(zip(ys,names)):
  _ring(x,y,c,k in bigs)
  for m,part in enumerate(textwrap.wrap(nm,wrapn)):text(x+(23 if anchor=='start' else -23),round(y+6+m*22),part,20,anchor=anchor,weight='600' if k in bigs else 'normal')
  if arrows and k<len(ys)-1 and k%3==1:tri(x,(y+ys[k+1])/2,c,False)
# 1. Corridor 10 toward PGC, extended upward from Kayu Putih Rawasari (the 5 stops before it, GTFS 10 pattern)
ext10=[s['name'] for s in S['10SK']['stops'][:5]]
ys10=[240-55*(5-i) for i in range(5)]
line(X10,ys10[0],X10,240,c10)
_col(X10,ys10,ext10,c10,bigs=(0,))
for k in range(4):
 if k%3==0:tri(X10,(ys10[k]+ys10[k+1])/2+0,c10,False)
# 2. Corridor 4 toward Galunggung, extended upward from Simpang Pramuka 2 (labels on the left, clear of the home walks)
ext4=[s['name'] for s in S['4PG']['stops'][:8]]
ys4=[150-62*(7-k) for k in range(8)]
line(X4,ys4[0],X4,240,c4c)
_col(X4,ys4,ext4,c4c,anchor='end',bigs=(0,4))
for k in range(8):
 if k%3==1:tri(X4,(ys4[k]+(ys4[k+1] if k<7 else 240))/2,c4c,False)
# 3. The three feeders from the Mall Kelapa Gading stop
mv_open('mkg-home','Mall Kelapa Gading to home feeders')
text(900,45-DY,'Mall Kelapa Gading → home',30,'#2e9e50',weight='600')
text(900,76-DY,'Mall Kelapa Gading is a TransJakarta stop (12P and JAK feeders), not a BRT corridor stop. Each option has one change.',17)
text(900,100-DY,'The three options join corridor 10 and corridor 4 below, the same lines and stops as the rest of this map.',17)
text(900,124-DY,'Green rings: where each option gets off. Kayu Putih Rawasari has the ~230 m home walk; Simpang Pramuka 2 is ~100 m from Pramuka BPKP 2, then the home walk.',17)
text(900,148-DY,'GTFS 26 Nov 2026, scheduled times only. Fare, gate, crossing and walks unverified. Also ~400 m away: LRT Boulevard Utara.',17)
add(f'<circle cx="{X4}" cy="{YT}" r="13" fill="Canvas" stroke="#2e9e50" stroke-width="5"/>')
text(X4,YT-28,'Mall Kelapa Gading stop (start of every option)',20,'#2e9e50',anchor='middle',weight='600')
F0=YT+110
def feeder(x,key,color,head,sub,stats,yend,final_big=True):
 st=S[key]['stops'][1:];ys=[F0+(yend-F0)*i/(len(st)-1) for i in range(len(st))]
 if x==X4:line(x,YT,x,yend,color)
 else:add(f'<path d="M {X4} {YT} L {x} {YT} L {x} {yend}" fill="none" stroke="{color}" stroke-width="6"/>')
 _col(x,ys,[t['name'] for t in st],color,bigs=(len(st)-1,),wrapn=44)
 text(x+23,YT+34,head,22,color,weight='600');text(x+23,YT+56,sub,15);text(x+23,YT+76,stats,14)
 return ys
y12=feeder(X10,'12P',c12,'Main: 12P → Sunter Kelapa Gading','then 10 toward PGC to Kayu Putih Rawasari (green ring)','12P: 9 stops, ~21 min sched.; then 10: ~26 min',-175)
y61=feeder(X4,'JAK61',cB,'Option 2: JAK.61 → Pulo Gadung 5','then 4 from Pulo Gadung (starts empty) to Simpang Pramuka 2 (green ring)','JAK.61: 14 stops, ~33 min sched.; then 4: ~23 min',-396)
y59=feeder(X59,'JAK59',cA,'Option 3: JAK.59 → Simpang Arion','then 4 from Pemuda Rawamangun to Simpang Pramuka 2 (green ring)','JAK.59: 19 stops, ~46 min sched.; then 4: ~11 min',-130)
# transfer walks (dashed, unverified) and their notes
line(X10,-175+14,X10,ys10[0]-14,'#888',True)
for k,t in enumerate(['walk ~25 m between the two Sunter Kelapa Gading','platforms (Utara to Selatan). Transfer is inside the','paid area, no second fare (Irvan, 26 Nov 2026).']):text(X10+23,-146+k*17,t,14)
line(X4,-396+14,X4,ys4[0]-14,'#888',True)
for k,t in enumerate(['walk ~95 m inside the Pulo Gadung','terminal area; Pulo Gadung 5 is a JAK','stop, Pulo Gadung is the 4 halte.','Fare gate / access unverified.']):text(X4+23,-356+k*17,t,14)
add(f'<path d="M {X59} {-130+14} L {X59} -36 L {X4+16} -36" fill="none" stroke="currentColor" opacity=".55" stroke-width="3" stroke-dasharray="5 7"/>')
for k,t in enumerate(['walk ~75 m to Pemuda Rawamangun','(corridor 4). Crossing and gate','access unverified.']):text(X4+40,-14+k*17,t,14)
mv_close()
# ride counts and the alighting stops on the shared columns
text(X10+360,-62,'12P then 10: ride 5 stops from Sunter Kelapa Gading',15,c10,weight='600')
add(f'<circle cx="{X10}" cy="240" r="17" fill="none" stroke="#2e9e50" stroke-width="3"/>')
text(450,244,'◀ Main option gets off here',16,'#2e9e50',weight='600')
text(450,261,'then the ~230 m walk home (unverified)',15)
add(f'<circle cx="{X4}" cy="240" r="17" fill="none" stroke="#2e9e50" stroke-width="3"/>')
# Option A note sits beside the 6 / Ragunan stations it explains (rider, 23 Nov 2026),
# in the empty area left of the corridor 6 spine; right edge kept clear of the spine.
AX,AY=1280,1560
text(AX,AY,'A · from Phe Tower',26,'currentColor',anchor='end',weight='600')
text(AX,AY+30,'beside the venue',26,'currentColor',anchor='end',weight='600')
for k,t in enumerate(['7E toward Ragunan: no bridge crossing','7E → Department of Agriculture','= Simpang Ragunan Ar-Raudhah;','6 ↔ Ragunan pin.','Home: 6 / 6A to Patra Kuningan,','then 4D to Simpang Pramuka 1.','Galunggung is the 6 direction,','not the transfer.','Allow a fresh tap/fare.']):
 text(AX,AY+68+k*27,t,21,anchor='end')
# Far-side homebound choice: the 7F shares the top three station areas of the outbound
# 10 column (Kayu Putih Rawasari, Pemuda Pramuka, Utan Kayu Rawamangun - same names in
# the official 10 GTFS pattern and the 7F Juanda-direction listing: Catenary 18 Nov 2026,
# e-kompas cross-check). Only its own stops branch left toward Flyover Raya Bogor, and
# the Gojek link runs below the network.
fx=300-SH
assert [s['name'] for s in S['10']['stops'][:3]]==['Kayu Putih Rawasari','Pemuda Pramuka','Utan Kayu Rawamangun']
assert R['7F-return']['stops']==['Flyover Raya Bogor','Trikora','Pasar Induk','Utan Kayu Rawamangun','Pemuda Pramuka','Kayu Putih Rawasari']
uky=240+2*55  # Utan Kayu Rawamangun, the branch point on the shared 10 column
by0=500
st7=(fy-by0)/3
add(f'<path d="M 164 {uky+8} L 164 {uky+27.5} L {fx} {uky+27.5} L {fx} {by0}" fill="none" stroke="{COL["10"]}" stroke-width="6"/>')
line(fx,by0,fx,fy,COL['10'])
node(fx,by0+st7,'Pasar Induk',COL['10'],anchor='end')
node(fx,by0+2*st7,'Trikora',COL['10'],anchor='end')
node(fx,fy,'Flyover Raya Bogor',COL['10'],True,anchor='end')
for yy in (by0+st7/2,by0+1.5*st7,by0+2.5*st7):tri(fx,yy,COL['10'])
text(fx-23,by0-24,'7F ↑ Juanda segment',19,COL['10'],anchor='end',weight='600')
text(fx-23,fy+44,'Get on 7F here; check access.',16,anchor='end')
# The 7F end IS the first outbound 10 stop: shared station area, not a platform claim.
text(80,196,'Confirm Kayu Putih Rawasari',15,anchor='end')
text(80,218,'on this service / loop headsign.',15,anchor='end')
text(193,uky-16,'7F ↑ branches to Flyover Raya Bogor',15)
# Deliberately NOT a guaranteed paid-area connection from 7E to 7F: a separate Gojek hop.
gy=ry+80
add(f'<path d="M 1324 {y7-43} Q 1720 {y7-43} 1720 {y7+90} L 1720 {gy} L {fx} {gy} L {fx} {fy+12}" fill="none" stroke="currentColor" opacity=".6" stroke-width="3" stroke-dasharray="5 7"/>')
tri(fx,fy+60,'#6536b0',up=True)
text(280,gy+70,'B · bridge to far-side pickup → Gojek to Flyover Raya Bogor',34,weight='600')
text(280,gy+120,'Gojek fare/time and 7F boarding access unverified.',32)
text(280,gy+164,'Separate from the 7E / 6 return option.',32)
text(900,gy-10,'Gojek hop to the 7F pickup (left)',16)
add('</g>')
# Preserve the Central Park node; S11 stacks below, rather than widening the map.
add('<rect x="582" y="1863" width="16" height="16" rx="3" fill="#2e9e50"/>')
# Organization pass (23 Nov 2026): the S11 block fills the empty left area under the
# Central Park node, and the S61 block sits under the Arkadia notes where S11 used to be,
# so nothing hangs far below the network. Only positions change, not routes or stops.
S11TX,S11TY=-3310,3050
_t=S11TY+400-60;_s=S11TY+400-10
add(f'<path d="M 590 1881 L 590 {_t} M 590 {_t} L 614 {_t} L 614 {_s} M 590 {_t} L 566 {_t} L 566 {_s}" fill="none" stroke="currentColor" opacity=".55" stroke-width="3" stroke-dasharray="5 7"/>')
add(f'<g transform="translate({S11TX} {S11TY})">')
mv_open('s11-block','S11 Central Park to The Breeze BSD block')
# S11 branches from the existing Central Park destination. Walk runs below the
# original network; line crossings without a ring are not transfer points.
s11c=COL['S11']; ox=3900; sy=400; dy=74
text(3960,190,'Central Park ↔ The Breeze BSD',40,weight='600')
text(3960,270,'From Central Park: JPO walk ~450 m / 6 min',30)
out=S['S11']['stops']; ret=R['S11-return']['stops']
rows11=[0]*max(len(out),len(ret))
by=sy+(len(rows11)-1)*dy
# Real-world check (GTFS coordinates): 19 of 22 outbound stops sit 16-102 m from a return stop and share one row;
# the rest keep their own row. Return labels on the left, outbound labels on the right.
dual(out,ret,ox,sy,dy,s11c)
text(ox+40,sy-30,'S11 ↓ BSD (right)',21,s11c,weight='600')
text(ox-40,sy-30,'S11 ↑ Jelambar (left)',21,s11c,anchor='end',weight='600')
text(ox+40,sy-72,'Walk to boarding: Jln. Gelong Baru Utara (right line).',18)
text(ox+40,sy-96,'Home: off at Taman Anggrek (left line); walk back.',18)
mv_open('breeze-bsd','The Breeze BSD pin and notes')
add(f'<rect x="{ox-9}" y="{by+140}" width="18" height="18" rx="3" fill="#2e9e50"/>')
text(ox,by+196,'The Breeze BSD',24,'#2e9e50',anchor='middle',weight='600')
line(ox,by+14,ox,by+131,'#888',True)
text(ox,by+232,'S11 ends at Serpong BSD, not at the mall.',17,anchor='middle')
text(ox,by+262,'Walk ~2.2 km / 29 min via BSD Grand Boulevard.',17,anchor='middle')
text(ox,by+290,'Pedestrian path / crossings not checked on site.',16,anchor='middle')
text(ox,by+340,'Operator feed: S11-L05 outbound, S11-R05 return.',16,anchor='middle')
text(ox,by+368,'No live arrivals or guaranteed last bus; check TJ app.',16,anchor='middle')
text(ox,by+398,'Two lines = two directions. Stops are not claimed to be the same boarding point.',16,anchor='middle')
mv_close()
S11END=S11TY+by+460
mv_close()
add('</g>')
add('<path d="M 2600 1876 L 2600 2138" fill="none" stroke="currentColor" opacity=".55" stroke-width="3" stroke-dasharray="5 7"/>')
S61DX=311  # whole block sits under the Bundaran Senayan pair (global x 2600 / 2672)
S61DY=-1250  # user feedback 23 Nov: block moves up 1250 map units beside the network
add(f'<g transform="translate({S61DX} {S61DY})">')
mv_open('s61-block','Alam Sutera S61 block')
# Alam Sutera branch below the established network, connected to the red termini.
# Dashed links are the walks between 4C curbside and S61 BRT at Bundaran Senayan.
c61=COL['S61']; ax=2325; sy61=3400; dy61=76  # pair widened (user feedback): columns under the red termini at global 2600 / 2672
ss61=S['S61']['stops']; rr61=R['S61-return']['stops']
text(2254,3170,'Alam Sutera · S61 from Bundaran Senayan',28,anchor='end',weight='600')
text(2254,3200,'Not an in-platform change. Check the pedestrian overpass,',16,anchor='end')
text(2254,3222,'gates and platform on the day.',16,anchor='end')
text(2254,3250,'4C curbside ↔ S61 BRT:',17,anchor='end')
text(2254,3278,'separate walk via pedestrian access;',17,anchor='end')
text(2254,3306,'allow a fresh tap/fare.',17,anchor='end')
rows61=[0]*max(len(ss61),len(rr61))
by61=sy61+(len(rows61)-1)*dy61
dual(ss61,rr61,ax,sy61,dy61,c61,gap=36,out_right=False)
text(ax-64,sy61-50,'S61 ↓ Alam Sutera (left)',20,c61,anchor='end',weight='600')
text(ax+64,sy61-50,'S61 ↑ Blok M (right)',20,c61,weight='600')
# Return link from the red homebound end: horizontal under the header, then straight up.
add('<path d="M 2361 3388 L 2361 3266" fill="none" stroke="currentColor" opacity=".55" stroke-width="3" stroke-dasharray="5 7"/>')
mx,mlx=2150,2490
fpy=by61-dy61;mly=by61
line(ax-24,by61+14,mx+8,by61+190,'#888',True);line(ax+24,by61+14,mlx-8,by61+190,'#888',True)
yb=by61+190
mv_open('binus-main','BINUS main building pin and notes')
add(f'<rect x="{mx-9}" y="{yb}" width="18" height="18" rx="3" fill="#2e9e50"/>')
text(mx,yb+55,'BINUS main building',24,'#2e9e50',anchor='middle',weight='600')
text(mx,yb+100,'Jl. Jalur Sutera Barat Kav. 21',16,anchor='middle')
text(mx,yb+130,'Forest Park → main: ~0.8 km / 11 min',16,anchor='middle')
text(mx,yb+160,'Main → Mall stop: ~1.3 km / 16 min',16,anchor='middle')
mv_close()
mv_open('binus-mall','Mall / BINUS extension pin and notes')
add(f'<rect x="{mlx-9}" y="{yb}" width="18" height="18" rx="3" fill="#2e9e50"/>')
text(mlx,yb+55,'Mall / BINUS extension',24,'#2e9e50',anchor='middle',weight='600')
text(mlx,yb+100,'Mall also houses BINUS extension classrooms',16,anchor='middle')
text(mlx,yb+130,'East Side · Kav. 16 · first floor (BINUS)',16,anchor='middle')
text(mlx,yb+160,'Forest Park → ext.: ~0.4 km / 5 min',16,anchor='middle')
text(mlx,yb+190,'Extension → Mall stop: ~0.5 km / 6 min',16,anchor='middle')
text(mlx,yb+220,'Free SuteraLoop shuttle loops from the mall; campus stop unverified.',16,anchor='middle')
mv_close()
text(2320,yb+260,'Same BINUS Alam Sutera operation, different buildings; campus and mall face each other across divided',17,anchor='middle')
text(2320,yb+290,'Jl. Jalur Sutera Barat - no formal crossing at the closest point on satellite (checked 23 Nov 2026);',17,anchor='middle')
text(2320,yb+320,'formal campus ↔ mall walk ~1.6 km / 21 min via the Jalur Sutera Boulevard junction (Google walking).',17,anchor='middle')
text(2320,yb+350,'On-ground sidewalks, crossings and gate access still unverified. No promised wait or last bus.',17,anchor='middle')
text(2320,yb+380,'GTFS 4C-R09 / R10 and S61-R02 / R01 checked 23 Nov 2026. Short turns also exist.',17,anchor='middle')
mv_close()
add('</g>')
# Source/service caveats stay within the unified map, below the network only as notes.
end=max(ry+150,S11END,5400)
_BASE_LINES=([
 'Arrowheads show travel direction. Dashed lines are walks / direction switches, not guaranteed paid-area links.',
 '7F service-hour listings disagree: jaGOdetabek combined patterns until 20:30; Moovit Juanda pattern 07:00-08:20;',
 'Traveloka 05:00-22:00. Do not assume late service. No guaranteed arrival times for either return option.',
 'Return: 19 Nov rider corrections for 7E / 6 / 4D and 7A at Masjid Ar-Raudhah; other stops: Catenary GTFS rendering, 4 cross-check: halte.id.',
 'Ragunan access / fare continuity, Gojek fare/time and 7F access remain unverified. Patterns may change.',
 'Outbound: TransJakarta operator GTFS checked 18 Nov 2026; 4D: jaGOdetabek / halte.id, not GTFS. No live arrivals.',
 'IDSW venue access: official access guideline (idsw.dev) checked 21 Nov 2026 - JPO walk, LRT Rasuna Said, CFD Sun 05:30-09:00.',
 'Bakoel Koffie (Cikini): on the 5M leg, get off at Farmasi RP Soeroso (~100 m). Home via the right column: 5M Kantor Pos Cikini to Megaria,',
 'then 4C to Pramuka BPKP 1 - official GTFS trips 5M-R02 / 4C-R10, checked 22 Nov 2026. Fresh tap each boarding.',
])
yy=end
for i,t in enumerate(_BASE_LINES):text(60,yy+i*31,t,18)
yy+=len(_BASE_LINES)*31+20
# Map notes block removed by Irvan, 26 Nov 2026 ("eh, just remove them"). Old text kept in data/map-reading-notes.html and git history (v0.2.31).
end=yy
add('</g>')
add('</svg>')
H=end+340+DY
svg=f'<svg viewBox="0 0 4600 {H}" role="img" aria-labelledby="all-stops-title all-stops-desc" xmlns="http://www.w3.org/2000/svg" font-family="system-ui, sans-serif">\n'+'\n'.join(A)
from map_bridges import add_bridges
svg=add_bridges(svg)
p=ROOT/'index.html'; src=p.read_text()
# Both the displayed combined map and its enlarged duplicate use exactly the same SVG.
src,n=re.subn(r'<svg viewBox="0 0 (?:560 \d+|4600 \d+|4200 \d+|5600 \d+|5000 \d+|3000 \d+|1700 \d+)".*?</svg>',lambda _:svg,src,flags=re.S)
assert n==1,n
p.write_text(src)
(ROOT/'data/all-stops.svg').write_text(svg+'\n')
print('generated map',len(svg),'bytes')
# Map-layout proposal 1: every build prints the layout score, so a nudge is
# measured, not eyeballed. Scoring reads the SVG only; files never change.
try:
 from score_route_map import score as _lscore
 print('layout score:',' '.join('%s=%s'%(k,v) for k,v in _lscore(svg).items()))
except Exception as _e:
 print('layout score unavailable:',_e)
