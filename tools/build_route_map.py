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
 add(f'<path d="M {x} {y} L {xx} {yy}" fill="none" stroke="{color}" stroke-width="{3 if dashed else 6}"'+(' stroke-dasharray="5 7"' if dashed else '')+'/>')
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
add('<svg viewBox="0 0 1700 3300" role="img" aria-labelledby="all-stops-title all-stops-desc" xmlns="http://www.w3.org/2000/svg" font-family="system-ui, sans-serif">')
add('<title id="all-stops-title">All intermediate stops on the selected outbound routes</title>')
add('<desc id="all-stops-desc">One connected schematic, not to scale. Read down each line in travel order. Hollow circles are stops; larger rings are boarding, transfer or alighting points. The corridor 4 leg uses Galunggung via Saharjo; 5M uses the via Cikini pattern. Other patterns may skip stops.</desc>')
text(60,45,'Every stop, in travel order',30,weight='600')
text(60,78,'Outbound routes only · schematic, not to scale · pinch to zoom and drag to pan',20)
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
text(95,y9+63,'Walk ~350 m',16);text(95,y9+96,'Central Park Mall',24,'#27803c',weight='600')
text(585,270,'4',22,COL['4'],anchor='end',weight='600')
y4=chain('4',630,240,62,transfers=['B08048P','G00216','G00202'])
text(655,273,'temporary stop · toward Galunggung via Saharjo',14)
# Matraman branches into curbside 5M. The ring is not a paid-area transfer.
mat=240+next(i for i,s in enumerate(S['4']['stops']) if s['id']=='G00216')*62
add(f'<path d="M 630 {mat+12} L 630 {mat+30} L 1000 {mat+30} L 1040 {mat+70}" fill="none" stroke="#888" stroke-width="3" stroke-dasharray="5 7"/>')
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
# The 7E continues toward Kampung Rambutan past the Arkadia stop; venue walk branches left.
line(630,y7+12,630,y7+255,COL['7E'])
add(f'<path d="M 624 {y7+10} L 582 {y7+34}" fill="none" stroke="#888" stroke-width="3" stroke-dasharray="5 7"/>')
text(560,y7+30,'Walk ~1 min to De Entrance',15,anchor='end')
text(560,y7+64,'Arkadia Green Park',22,'#27803c',weight='600',anchor='end')
for i,name in enumerate(['Jln. H. Saidi','Jln. Nangka 1','Jln. Muara 1','Plaza Pp Condet 2','RSUD Pasar Rebo 2']):
 node(630,y7+56+i*44,name,COL['7E'])
fy=y7+264
node(630,fy,'Flyover Raya Bogor - get off',COL['7E'],True)
text(607,fy-120,'Rode past Jln. Gabus Raya?',14,anchor='end')
text(607,fy-100,'Ride on to Flyover Raya Bogor and',13,anchor='end')
text(607,fy-84,'switch direction there - the physical',13,anchor='end')
text(607,fy-68,'link and re-tap fare are unverified.',13,anchor='end')
# Direction switch: a candidate from the listings, not a confirmed physical link.
add(f'<path d="M 640 {fy+12} C 780 {fy+68}, 900 {fy+68}, 988 {fy+52}" fill="none" stroke="#888" stroke-width="3" stroke-dasharray="5 7"/>')
ry=fy+50
add(f"<circle cx='1000' cy='{ry}' r='12' fill='Canvas' stroke='{COL['7E']}' stroke-width='4'/>")
text(977,ry-10,'Flyover Raya Bogor',20,weight='600',anchor='end')
text(1023,ry+6,'board toward Ragunan - physical link unverified',13)
line(1000,ry+12,1000,ry+48+36*8-9,COL['7E'])
for i,name in enumerate(['RSUD Pasar Rebo 1','SMAN 104','Plaza Pp Condet 1','Muara Dalam','ACC Simatupang','Telkomsel Jln. Nangka','Jln. Nangka Raya','Gg. Nanas']):
 node(1000,ry+48+i*36,name,COL['7E'])
by=ry+48+36*8
node(1000,by,'Baung - get off',COL['7E'],True,anchor='end')
text(977,by+32,'or ride 1 more: Phe Tower Kebagusan (~5 min walk)',13,anchor='end')
line(1000,by+12,1000,by+36,'#888',True)
text(1023,by+32,'Walk ~4 min (285 m)',15)
text(1023,by+66,'De Entrance - Arkadia Green Park',22,'#27803c',weight='600')
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
text(1225,yend+116,'Markas Indonesia',24,'#27803c',weight='600')
text(60,3120,'Rings = boarding / transfer / get off · small circles = intermediate stops · dashed = walk or an unverified direction switch',20)
text(60,3155,'Corridor legs show the listed direction only - do not reverse them. The drawn 7E return leg is the actual Ragunan-bound pattern.',18)
text(60,3190,'The 7E Flyover Raya Bogor switch is a candidate from GTFS-derived listings - the physical link and re-tap fare are unverified.',17)
text(60,3225,'Sources: TransJakarta official GTFS · gtfs.transjakarta.co.id/files/file_gtfs.zip',17)
text(60,3260,'Check the TJ: Transjakarta app and the vehicle headsign before boarding. No live arrival information.',17)
add('</svg>')
svg='\n'.join(A)
p=ROOT/'index.html'; src=p.read_text()
# Both the displayed combined map and its enlarged duplicate use exactly the same SVG.
src,n=re.subn(r'<svg viewBox="0 0 (?:560 \d+|1700 \d+)".*?</svg>',lambda _:svg,src,flags=re.S)
assert n==2,n
p.write_text(src)
(ROOT/'data/all-stops.svg').write_text(svg+'\n')
print('generated map',len(svg),'bytes')
