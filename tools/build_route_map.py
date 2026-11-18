#!/usr/bin/env python3
"""Generate one connected, all-stops SVG. Station names/order come from GTFS.
The layout is schematic, not a geographic or live-service map.
"""
import html, json, re, textwrap
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
D=json.loads((ROOT/'data/route-stops.json').read_text())
S={s['route']:s for s in D['segments']}
COL={'10':'#6536b0','9':'#27803c','4':'#1769aa','6':'#d36300','7E':'#00838f','4C':'#c52d36','5M':'#9045ac'}
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
def node(x,y,name,color,transfer=False,note=None,anchor='start'):
 add(f'<circle cx="{x}" cy="{y}" r="{12 if transfer else 7}" fill="Canvas" stroke="{color}" stroke-width="4"/>')
 dx=23 if anchor=='start' else -23
 for i,part in enumerate(textwrap.wrap(name,33)):
  text(x+dx,y+6+i*24,part,20,anchor=anchor,weight='600' if transfer else 'normal')
 if note:text(x+dx,y+32,note,15,anchor=anchor)
def chain(route,x,y,step=58,skipfirst=False,transfers=()):
 ss=S[route]['stops']; end=y+step*(len(ss)-1)
 line(x,y,x,end,COL[route])
 for i,st in enumerate(ss):
  if not(skipfirst and i==0):node(x,y+i*step,st['name'],COL[route],st['id'] in transfers)
 return end
add('<title id="all-stops-title">All intermediate stops on the selected outbound routes</title>')
add('<desc id="all-stops-desc">One connected schematic, not to scale. Read each corridor leg downward in its listed direction; the 7E return leg is drawn upward on the left after an unverified direction switch, with arrowheads marking travel direction. Hollow circles are stops; larger rings are boarding, transfer or alighting points. The corridor 4 leg uses Galunggung via Saharjo; 5M uses the via Cikini pattern. The corridor 4 leg uses Galunggung via Saharjo; 5M uses the via Cikini pattern. Other patterns may skip stops. The road by the venue is drawn between the two 7E directions: the pedestrian bridge between the Mujair and Phe Tower stops crosses it, the venue sits beside Phe Tower Kebagusan just past Jln. Gabus Raya, and Baung is farther along - both on the venue side (firsthand 18 Nov 2026); the Flyover Raya Bogor direction switch itself remains unverified.</desc>')
text(60,45,'Every stop, in travel order',30,weight='600')
text(60,78,'Corridor legs in listed direction · 7E return leg drawn back up the left · schematic, not to scale',20)
text(60,108,'Operator GTFS checked 18 Nov 2026. Route patterns and temporary stops can change.',17)
node(700,155,'Green Pramuka area','#777',True)
for x in [70,630,1200]:line(700,170,x,230,'#888',True)
text(95,204,'walk ~230 m',16);text(655,204,'walk to boarding point',16);text(1230,204,'walk ~850 m',16)
text(40,270,'10',22,COL['10'],anchor='end',weight='600')
y10=chain('10',70,240,55,transfers=['G00473','G00718'])
text(95,y10+33,'Change platform inside the same paid halte',15)
text(25,y10+90,'9',22,COL['9'],anchor='end',weight='600')
y9=chain('9',70,y10,65,True,['G00403'])
line(70,y9+12,70,y9+75,'#888',True)
text(95,y9+63,'Walk ~350 m',16);text(95,y9+96,'Central Park Mall',24,'#2e9e50',weight='600')
text(585,270,'4',22,COL['4'],anchor='end',weight='600')
y4=chain('4',630,240,62,transfers=['B08048P','G00216','G00202'])
text(655,273,'temporary stop · toward Galunggung via Saharjo',14)
# Matraman branches into curbside 5M. The ring is not a paid-area transfer.
mat=240+next(i for i,s in enumerate(S['4']['stops']) if s['id']=='G00216')*62
add(f'<path d="M 630 {mat+12} L 630 {mat+30} L 1000 {mat+30} L 1040 {mat+70}" fill="none" stroke="currentColor" opacity=".55" stroke-width="3" stroke-dasharray="5 7"/>')
node(1040,mat+70,'Matraman 3',COL['5M'],True,anchor='end')
text(1040,mat+110,'Tap out; ~1 min walk',15,anchor='end')
# Walk from corridor 4 to 6 at Galunggung is not assumed paid-area continuous.
line(630,y4+12,630,y4+110,'#888',True)
text(655,y4+55,'4 to 6: paid-area continuity unconfirmed',15)
text(585,y4+145,'6',22,COL['6'],anchor='end',weight='600')
y6=chain('6',630,y4+120,61,transfers=['G00204','G00243'])
line(630,y6+12,630,y6+110,'#888',True)
text(655,y6+50,'Walk ~2 min to the curbside 7E stop',15)
text(585,y6+145,'7E',22,COL['7E'],anchor='end',weight='600')
y7=chain('7E',630,y6+120,60,transfers=['B07989P','B01062P'])
# The 7E continues toward Kampung Rambutan past the Arkadia stop.
line(630,y7+12,630,y7+268,COL['7E'])
# The road between the two 7E sides by the venue (firsthand 18 Nov 2026):
# Ragunan-bound on the venue side (left column), Kampung Rambutan-bound far side.
# The venue sits beside the Phe Tower Kebagusan stop, just past Jln. Gabus Raya
# toward Kampung Rambutan; the footbridge is between the Mujair and Phe stops.
py=y7+44
bq=y7+88
add(f'<rect x="306" y="{y7-16}" width="318" height="120" fill="currentColor" opacity="0.12"/>')
add(f'<line x1="465" y1="{y7-16}" x2="465" y2="{y7+104}" stroke="currentColor" opacity="0.35" stroke-width="3" stroke-dasharray="8 8"/>')
add(f'<text x="300" y="{y7+10}" font-size="13" fill="currentColor" text-anchor="end">Walk ~1 min</text>')
add(f'<text x="618" y="{y7-2}" font-size="13" font-style="italic" opacity=".65" fill="currentColor" text-anchor="end">far side</text>')
add(f'<text x="312" y="{y7-2}" font-size="13" font-style="italic" opacity=".65" fill="currentColor" text-anchor="start">venue side</text>')
# Pedestrian bridge across the road, between the Mujair and Phe Tower stops.
add(f'<line x1="306" y1="{y7+4}" x2="624" y2="{y7+4}" stroke="currentColor" opacity=".55" stroke-width="2"/>')
add(f'<line x1="306" y1="{y7+16}" x2="624" y2="{y7+16}" stroke="currentColor" opacity=".55" stroke-width="2"/>')
for bx in range(318,624,18): add(f'<line x1="{bx}" y1="{y7+4}" x2="{bx}" y2="{y7+16}" stroke="currentColor" opacity=".55" stroke-width="2"/>')
# One shared venue marker beside the Phe Tower stop; all walks arrive at the same place.
add(f'<rect x="457" y="{y7+38}" width="16" height="16" rx="3" fill="#2e9e50"/>')
text(465,y7+84,'De Entrance -',19,'#2e9e50',weight='600',anchor='middle')
text(465,y7+108,'Arkadia Green Park',19,'#2e9e50',weight='600',anchor='middle')
text(465,y7+130,'same side as Phe Tower + Baung',13,anchor='middle')
add(f'<path d="M 306 {y7+16} C 340 {y7+28}, 400 {y7+38}, 449 {y7+44}" fill="none" stroke="currentColor" opacity=".55" stroke-width="3" stroke-dasharray="5 7"/>')
add(f'<path d="M 312 {py+2} C 360 {py-2}, 410 {py-2}, 449 {py+2}" fill="none" stroke="currentColor" opacity=".55" stroke-width="3" stroke-dasharray="5 7"/>')
add(f'<path d="M 312 {bq+2} C 350 {bq-24}, 410 {y7+56}, 449 {y7+52}" fill="none" stroke="currentColor" opacity=".55" stroke-width="3" stroke-dasharray="5 7"/>')
for i,name in enumerate(['Jln. H. Saidi','Jln. Nangka 1','Jln. Muara 1','Plaza Pp Condet 2','RSUD Pasar Rebo 2']):
 node(630,y7+56+i*44,name,COL['7E'])
fy=y7+280
node(630,fy,'Flyover Raya Bogor - get off',COL['7E'],True)
text(607,fy-120,'Rode past Jln. Gabus Raya?',14,anchor='end')
text(607,fy-100,'Ride on to Flyover Raya Bogor and',13,anchor='end')
text(607,fy-84,'switch direction there - the physical',13,anchor='end')
text(607,fy-68,'link and re-tap fare are unverified.',13,anchor='end')
for ay in (y7-150,y7+28,y7+122,y7+210,y7+254):tri(630,ay,COL['7E'],up=False)
# Direction switch: a candidate from the listings, not a confirmed physical link.
ry=y7+496
add(f'<path d="M 618 {fy+6} C 470 {fy+120}, 400 {ry-30}, 346 {ry+2}" fill="none" stroke="currentColor" opacity=".55" stroke-width="3" stroke-dasharray="5 7"/>')
add(f'<path d="M 312 {ry+2} L 344 {ry-11} L 344 {ry+15} Z" fill="currentColor" opacity=".6" stroke="Canvas" stroke-width="3" stroke-linejoin="round"/>')
add(f"<circle cx='300' cy='{ry}' r='12' fill='Canvas' stroke='{COL['7E']}' stroke-width='4'/>")
text(277,ry+6,'Flyover Raya Bogor',20,weight='600',anchor='end')
text(277,ry+30,'board toward Ragunan',13,anchor='end')
text(277,ry+46,'physical link unverified',13,anchor='end')
# Return leg runs back UP the left column, toward the venue.
line(300,py+12,300,ry-12,COL['7E'])
for i,name in enumerate(['Gg. Nanas','Jln. Nangka Raya','Telkomsel Jln. Nangka','ACC Simatupang','Muara Dalam','Plaza Pp Condet 1','SMAN 104','RSUD Pasar Rebo 1']):
 node(300,bq+44+i*44,name,COL['7E'],anchor='end')
for ay in (y7+66,y7+110,y7+198,y7+286,y7+374,y7+462):tri(300,ay,COL['7E'])
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
for i,st in enumerate(tail[1:],1):node(1200,yc+i*61,st['name'],COL['5M'],i==len(tail)-1)
text(1155,yc+90,'5M',22,COL['5M'],anchor='end',weight='600')
text(1225,yend+43,'via Cikini pattern; other 5M patterns differ',15)
line(1200,yend+12,1200,yend+100,'#888',True)
text(1225,yend+83,'Walk ~300 m',17)
text(1225,yend+116,'Markas Indonesia',24,'#2e9e50',weight='600')
foot0=max(ry+50,fy+76,yend+116,y9+96)+50
text(60,foot0,'Rings = boarding / transfer / get off · small circles = intermediate stops · arrowheads = travel direction · dashed = walk or an unverified direction switch',20)
text(60,foot0+35,'Corridor legs show the listed direction only - do not reverse them. The drawn 7E return leg is the actual Ragunan-bound pattern.',18)
text(60,foot0+70,'The 7E Flyover Raya Bogor switch is a candidate from GTFS-derived listings - the physical link and re-tap fare are unverified.',17)
text(60,foot0+105,'Firsthand 18 Nov 2026: the venue sits beside the Phe Tower Kebagusan stop, just past Jln. Gabus Raya toward Kampung Rambutan; the pedestrian bridge is between the Mujair and Phe Tower stops; Baung is farther along on the venue side.',17)
text(60,foot0+140,'Sources: TransJakarta official GTFS · gtfs.transjakarta.co.id/files/file_gtfs.zip',17)
text(60,foot0+175,'Check the TJ: Transjakarta app and the vehicle headsign before boarding. No live arrival information.',17)
add('</svg>')
H=foot0+215
svg=f'<svg viewBox="0 0 1700 {H}" role="img" aria-labelledby="all-stops-title all-stops-desc" xmlns="http://www.w3.org/2000/svg" font-family="system-ui, sans-serif">\n'+'\n'.join(A)
p=ROOT/'index.html'; src=p.read_text()
# Both the displayed combined map and its enlarged duplicate use exactly the same SVG.
src,n=re.subn(r'<svg viewBox="0 0 (?:560 \d+|1700 \d+)".*?</svg>',lambda _:svg,src,flags=re.S)
assert n==2,n
p.write_text(src)
(ROOT/'data/all-stops.svg').write_text(svg+'\n')
print('generated map',len(svg),'bytes')
