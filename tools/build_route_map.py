#!/usr/bin/env python3
"""Generate one connected, all-stops SVG. Station names/order come from GTFS.
The layout is schematic, not a geographic or live-service map.
"""
import html, json, re, textwrap
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
D=json.loads((ROOT/'data/route-stops.json').read_text())
S={s['route']:s for s in D['segments']}
COL={'10':'#6536b0','9':'#27803c','4':'#1769aa','6':'#d36300','7E':'#00838f','4C':'#c52d36','5M':'#9045ac','4D':'#0f6e6e'}
A=[]
def add(s): A.append(s)
def text(x,y,s,size=20,color='currentColor',anchor='start',weight='normal'):
 add(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{weight}">{html.escape(s)}</text>')
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
def chain(route,x,y,step=58,skipfirst=False,transfers=()):
 ss=S[route]['stops']; end=y+step*(len(ss)-1)
 line(x,y,x,end,COL[route])
 for i,st in enumerate(ss):
  if not(skipfirst and i==0):node(x,y+i*step,st['name'],COL[route],st['id'] in transfers,
   label_offset=(50,-19) if route=='4' and st['name']=='Halimun' else None)
  if i<len(ss)-1 and i%3==0:tri(x,y+i*step+step/2,COL[route],False)
 return end
add('<title id="all-stops-title">Outbound routes, Arkadia homebound options and the Cikini return, with intermediate stops</title>')
add('<desc id="all-stops-desc">One connected schematic, not to scale. Read each corridor leg downward in its listed direction; the 7E return leg is drawn upward on the left after a direction switch, ending its selected leg at Department of Agriculture, which is the same station as Simpang Ragunan Ar-Raudhah (rider, 19 Nov 2026). Corridor 6 links this station with Ragunan - the destination pin - in both directions, and the ride home boards corridor 6 / 6A there toward Galunggung - the direction, not the transfer - changing at Patra Kuningan to 4D for Simpang Pramuka 1; teal rings mark the 4D return stops. Gate access and fare continuity between 7E and corridor 6 are unverified. The 7A route boards at Phe Tower Kebagusan, shares the 7E stops Plaza Oleos, Kebagusan Raya, Kementan and Kementan 2, then leaves the 7E column and ends at Masjid Ar-Raudhah, the same station where the outbound 7E leg begins (rider correction, 19 Nov 2026), about 140 m on foot from Department of Agriculture via Akses A. Arrowheads mark travel direction. Hollow circles are stops; larger rings are boarding, transfer or alighting points. The corridor 4 leg uses Galunggung via Saharjo; 5M uses the via Cikini pattern. Other patterns may skip stops. The road by the venue is drawn between the two 7E directions: the pedestrian bridge between the Mujair and Phe Tower stops crosses it, the venue sits beside Phe Tower Kebagusan, and Jln. Gabus Raya (far side) and Baung (venue side) are both farther along toward Kampung Rambutan, and the Flyover Raya Bogor direction switch stays inside the paid area with no new fare (all firsthand 18 Nov 2026). The 7F homebound shares the Kayu Putih Rawasari, Pemuda Pramuka and Utan Kayu Rawamangun station areas with the outbound 10 column, then branches left toward Flyover Raya Bogor. At the 4D Rasuna Said terminus, the venue access block carries the official IDSW access guideline (idsw.dev, checked 21 Nov 2026): LRT Rasuna Said is the other official nearest stop, about 2 minutes, sharing the same pedestrian-bridge walk; the final walk runs toward Plaza Festival for about 150 m into the Gedung PPHUI complex; and the Sunday 22 November Car Free Day window 05:30-09:00 WIB bars car and motorbike gate drop-off while the LRT and corridor 6/6A keep running and drivers park at Plaza Festival. Bakoel Koffie (Cikini) is on the 5M leg: get off at Farmasi RP Soeroso, about 100 m away. The ride home boards the 5M at Kantor Pos Cikini (about 90 m from the venue) toward Kampung Melayu and changes at Megaria to 4C for Pramuka BPKP 1; it is drawn in the Bakoel Koffie card on the page, not in this network map (official GTFS trips 5M-R02 and 4C-R10, checked 22 Nov 2026; curbside feeders, so allow a fresh tap at each boarding).</desc>')
SH=420  # whole network shifts right so the 7F homebound column can sit at the far left
add(f'<g transform="translate({SH} 0)">')
add('<g transform="translate(700 0)">')
node(700,155,'Green Pramuka area','#777',True)
for x in [-530,630,1200]:line(700,170,x,230,'#888',True)
text(-505,204,'walk ~230 m',16);text(655,204,'walk to boarding point',16);text(1230,204,'walk ~850 m',16)
add('<g transform="translate(-600 0)">')
text(40,258,'10 ↓ PGC',19,COL['10'],anchor='end',weight='600')
text(40,284,'7F ↑ Juanda',19,COL['10'],anchor='end',weight='600')
y10=chain('10',70,240,55,transfers=['G00473','G00718'])
# 7F homebound shares the top three station areas of this column (same stop names in
# the official 10 GTFS pattern and the 7F Juanda-direction listing). Its own stops
# branch off at Utan Kayu Rawamangun toward Flyover Raya Bogor; drawn in the outer section.
tri(55,267,COL['10']);tri(55,322,COL['10'])
text(95,y10+33,'Change platform inside the same paid halte',15)
text(25,y10+90,'9',22,COL['9'],anchor='end',weight='600')
y9=chain('9',70,y10,65,True,['G00403'])
line(70,y9+12,70,y9+75,'#888',True)
text(95,y9+63,'Walk ~350 m',16);text(95,y9+96,'Central Park Mall',24,'#2e9e50',weight='600')
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
text(655,y4+55,'4 to 6: no additional fare (firsthand)',15)
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
add(f'<text x="300" y="{y7-42}" font-size="13" fill="currentColor" text-anchor="end">Via footbridge</text>')
add(f'<text x="618" y="{y7-52}" font-size="13" font-style="italic" opacity=".65" fill="currentColor" text-anchor="end">far side</text>')
add(f'<text x="332" y="{y7-52}" font-size="13" font-style="italic" opacity=".65" fill="currentColor" text-anchor="start">venue side</text>')
# Pedestrian bridge across the road, between the Mujair and Phe Tower stops.
add(f'<line x1="306" y1="{y7-48}" x2="624" y2="{y7-48}" stroke="currentColor" opacity=".55" stroke-width="2"/>')
add(f'<line x1="306" y1="{y7-38}" x2="624" y2="{y7-38}" stroke="currentColor" opacity=".55" stroke-width="2"/>')
for bx in range(318,624,18): add(f'<line x1="{bx}" y1="{y7-48}" x2="{bx}" y2="{y7-38}" stroke="currentColor" opacity=".55" stroke-width="2"/>')
# One shared venue marker beside the Phe Tower stop; all walks arrive at the same place.
add(f'<rect x="457" y="{y7-34}" width="16" height="16" rx="3" fill="#2e9e50"/>')
text(465,y7+32,'De Entrance -',19,'#2e9e50',weight='600',anchor='middle')
text(465,y7+56,'Arkadia Green Park',19,'#2e9e50',weight='600',anchor='middle')
text(465,y7+78,'same side as Phe Tower + Baung',13,anchor='middle')
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
add(f'<path d="M 618 {fy+6} C 470 {fy+120}, 400 {ry-30}, 346 {ry+2}" fill="none" stroke="currentColor" opacity=".55" stroke-width="3" stroke-dasharray="5 7"/>')
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
text(1155,270,'4C',22,COL['4C'],anchor='end',weight='600')
yc=chain('4C',1200,240,62,transfers=['B07260P','B05812P'])
# Both 4C and 5M serve Masjid Jami Matraman before Tugu Proklamasi.
mas=240+next(i for i,s in enumerate(S['4C']['stops']) if s['id']=='B02350P')*62
line(1040,mat+70,1200,mas,COL['5M'])
text(1110,mas-16,'5M',18,COL['5M'],anchor='end')
line(1192,mas,1192,yc,COL['5M'])
text(1225,yc+34,'Same curbside stop: change 4C to 5M',15)
# 5M from the already drawn Tugu Proklamasi, avoiding duplicate shared stops.
ss=S['5M']['stops']; idx=next(i for i,s in enumerate(ss) if s['id']=='B05812P'); tail=ss[idx:]
yend=yc+61*(len(tail)-1)
line(1200,yc,1200,yend,COL['5M'])
for i,st in enumerate(tail[1:],1):node(1200,yc+i*61,st['name'],COL['5M'],i==len(tail)-1 or st['id']=='B00346P')
text(1155,yc+90,'5M',22,COL['5M'],anchor='end',weight='600')
text(1225,yend+43,'via Cikini pattern; other 5M patterns differ',15)
line(1200,yend+12,1200,yend+100,'#888',True)
text(1225,yend+83,'Walk ~300 m',17)
text(1225,yend+116,'Markas Indonesia',24,'#2e9e50',weight='600')
# Bakoel Koffie (Cikini): alight the outbound 5M at Farmasi RP Soeroso (ring above),
# about 100 m from the venue. The ride home (5M from Kantor Pos Cikini, change at
# Megaria to 4C for Pramuka BPKP 1; official GTFS trips 5M-R02 and 4C-R10, checked
# 22 Nov 2026) is drawn in the Bakoel Koffie card on the page, not in this network map.
bky=yc+10*61  # Farmasi RP Soeroso node
add(f'<path d="M 1206 {bky+12} C 1260 {bky+98}, 1380 {bky+106}, 1492 {bky+106}" fill="none" stroke="currentColor" opacity=".55" stroke-width="3" stroke-dasharray="5 7"/>')
add(f'<rect x="1500" y="{bky+98}" width="16" height="16" rx="3" fill="#2e9e50"/>')
text(1525,bky+96,'Bakoel Koffie',19,'#2e9e50',weight='600')
text(1525,bky+118,'get off 5M · walk ~100 m',14)
text(1525,bky+142,'home: 5M from Kantor Pos Cikini,',13)
text(1525,bky+162,'change at Megaria to 4C (card below)',13)
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
text(680,hy+2,'4D leaves here; 4 goes on to Galunggung',15,weight='600')
tail=s4d[nshared:]
y4d=by+58*(len(tail)-1)
line(bx,by,bx,y4d,COL['4D'])
for i,st in enumerate(tail):node(bx,by+i*58,st['name'],COL['4D'],i==len(tail)-1)
text(bx-25,by+30,'4D',22,COL['4D'],anchor='end',weight='600')
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
text(bx+25,y4d+256,'Final walk (official): JPO',14,weight='600')
text(bx+25,y4d+278,'toward Plaza Festival ~150 m,',14)
text(bx+25,y4d+300,'enter Gedung PPHUI complex',14)
text(bx+25,y4d+362,'CFD Sun 22 Nov 05:30-09:00:',14,weight='600')
text(bx+25,y4d+384,'no car/motorbike drop-off',14,weight='600')
text(bx+25,y4d+406,'at the gate; LRT + 6/6A',14,weight='600')
text(bx+25,y4d+428,'keep running; park at',14,weight='600')
text(bx+25,y4d+450,'Plaza Festival',14,weight='600')
text(bx+25,y4d+480,'official: idsw.dev guide,',13)
text(bx+25,y4d+500,'checked 21 Nov 2026',13)
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
for yy in (767,829):tri(615,yy,COL['4'])
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
text(585,972,'6 → 4 at Galunggung: alternative; check platform, no fare promise',13,anchor='end')
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
line(648,1098,648,806,COL['4D'])
tri(648,788,COL['4D'])
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
node(800,2040,'Ragunan (destination pin)',COL['6'],True)
text(660,2056,'6 ↔ both directions',13,COL['6'])
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
add(f'<path d="M 314 2126 C 400 2126, 480 {my}, 600 {my}" fill="none" stroke="{c7a}" stroke-width="6"/>')
add(f'<path d="M 600 {my} L 578 {my-8} L 578 {my+8} Z" fill="{c7a}" stroke="Canvas" stroke-width="3" stroke-linejoin="round"/>')
line(311,py-4,311,2118,c7a)
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
R={r['key']:r for r in json.loads((ROOT/'data/return-stops.json').read_text())['segments']}
def return_chain(key,x,bottom,top,color,skipfirst=False):
 ss=R[key]['stops']; step=(bottom-top)/(len(ss)-1)
 line(x,bottom,x,top,color)
 for i,name in enumerate(ss):
  yy=bottom-i*step
  if not(skipfirst and i==0):node(x,yy,name,color,i in (0,len(ss)-1))
  if i<len(ss)-1:tri(x,yy-step/2,color)
 return top
text(60-SH,45,'One network · out and home',30,weight='600')
text(60-SH,80,'Shared 4 / 6 and 10 / 7F spines · down outbound, up homebound · only different stops branch.',19)
text(60-SH,110,'Station areas are shared, not necessarily platforms. 7E keeps its different roadside stops.',17)
text(1580,fy+100,'A · from Phe Tower beside the venue',20,COL['7E'],weight='600')
text(1580,fy+128,'7E toward Ragunan: no bridge crossing',17)
text(1580,fy+156,'7E → Department of Agriculture',17)
text(1580,fy+184,'= Simpang Ragunan Ar-Raudhah; 6 ↔ Ragunan pin.',17)
text(1580,fy+212,'Home: 6 / 6A to Patra Kuningan, then 4D to',17)
text(1580,fy+240,'Simpang Pramuka 1. Galunggung is the 6 direction,',17)
text(1580,fy+268,'not the transfer. Allow a fresh tap/fare.',17)
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
add(f'<path d="M 164 {uky+8} L {fx} {by0}" fill="none" stroke="{COL["10"]}" stroke-width="6"/>')
line(fx,by0,fx,fy,COL['10'])
node(fx,by0+st7,'Pasar Induk',COL['10'],anchor='end')
node(fx,by0+2*st7,'Trikora',COL['10'],anchor='end')
node(fx,fy,'Flyover Raya Bogor',COL['10'],True,anchor='end')
for yy in (by0+st7/2,by0+1.5*st7,by0+2.5*st7):tri(fx,yy,COL['10'])
text(fx-23,by0-24,'7F ↑ Juanda segment',19,COL['10'],anchor='end',weight='600')
text(fx-23,fy+44,'Get on 7F here; check access.',16,anchor='end')
# The 7F end IS the first outbound 10 stop: shared station area, not a platform claim.
text(147,200,'Confirm Kayu Putih Rawasari',15,anchor='end')
text(147,224,'on this service / loop headsign.',15,anchor='end')
text(193,uky-16,'7F ↑ branches to Flyover Raya Bogor',15)
# Deliberately NOT a guaranteed paid-area connection from 7E to 7F: a separate Gojek hop.
gy=ry+80
add(f'<path d="M 1324 {y7-43} Q 1510 {y7-43} 1510 {y7+90} L 1510 {gy} L {fx} {gy} L {fx} {fy+12}" fill="none" stroke="currentColor" opacity=".6" stroke-width="3" stroke-dasharray="5 7"/>')
tri(fx,fy+60,'#6536b0',up=True)
text(1580,fy-210,'B · bridge to far-side pickup → Gojek to Flyover Raya Bogor',21,weight='600')
text(1580,fy-180,'Gojek fare/time and 7F boarding access unverified.',17)
text(1580,fy-150,'Separate from the 7E / 6 return option.',17)
text(900,gy-10,'Gojek hop to the 7F pickup (left)',16)
add('</g>')
# Source/service caveats stay within the unified map, below the network only as notes.
end=max(ry+150,2760)
for i,t in enumerate([
 'Arrowheads show travel direction. Dashed lines are walks / direction switches, not guaranteed paid-area links.',
 '7F service-hour listings disagree: jaGOdetabek combined patterns until 20:30; Moovit Juanda pattern 07:00-08:20;',
 'Traveloka 05:00-22:00. Do not assume late service. No guaranteed arrival times for either return option.',
 'Return: 19 Nov rider corrections for 7E / 6 / 4D and 7A at Masjid Ar-Raudhah; other stops: Catenary GTFS rendering, 4 cross-check: halte.id.',
 'Ragunan access / fare continuity, Gojek fare/time and 7F access remain unverified. Patterns may change.',
 'Outbound: TransJakarta operator GTFS checked 18 Nov 2026; 4D: jaGOdetabek / halte.id, not GTFS. No live arrivals.',
 'IDSW venue access: official access guideline (idsw.dev) checked 21 Nov 2026 - JPO walk, LRT Rasuna Said, CFD Sun 05:30-09:00.',
 'Bakoel Koffie (Cikini): on the 5M leg, get off at Farmasi RP Soeroso (~100 m). Return via 5M Kantor Pos Cikini to Megaria, then',
 '4C to Pramuka BPKP 1 (stops in the page card) - official GTFS trips 5M-R02 / 4C-R10, checked 22 Nov 2026. Fresh tap each boarding.',
]):text(60,end+i*31,t,18)
add('</svg>')
H=end+220
svg=f'<svg viewBox="0 0 3000 {H}" role="img" aria-labelledby="all-stops-title all-stops-desc" xmlns="http://www.w3.org/2000/svg" font-family="system-ui, sans-serif">\n'+'\n'.join(A)
p=ROOT/'index.html'; src=p.read_text()
# Both the displayed combined map and its enlarged duplicate use exactly the same SVG.
src,n=re.subn(r'<svg viewBox="0 0 (?:560 \d+|3000 \d+|1700 \d+)".*?</svg>',lambda _:svg,src,flags=re.S)
assert n==2,n
p.write_text(src)
(ROOT/'data/all-stops.svg').write_text(svg+'\n')
print('generated map',len(svg),'bytes')
