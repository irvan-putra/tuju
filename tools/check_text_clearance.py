"""List map text boxes that a line passes through or touches (approximate text widths).
Usage: python3 tools/check_text_clearance.py [margin]. Prints candidates for review; exit 0."""
import re,sys,pathlib
import xml.etree.ElementTree as ET
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from map_bridges import points
ROOT=pathlib.Path(__file__).resolve().parent.parent
M=float(sys.argv[1]) if len(sys.argv)>1 else 6
root=ET.fromstring((ROOT/'data/all-stops.svg').read_text())
texts=[];segs=[]
def walk(el,sh=0j,hidden=False):
    tr=re.search(r'translate\(([-.\d]+)[ ,]+([-.\d]+)\)',el.get('transform',''))
    if tr:sh+=complex(*map(float,tr.groups()))
    tag=el.tag.split('}')[1]
    if tag=='text':
        t=''.join(el.itertext());size=float(el.get('font-size',16));x=float(el.get('x',0));y=float(el.get('y',0))
        w=0.54*size*len(t)*(1.08 if el.get('font-weight') else 1)
        a=el.get('text-anchor','start')
        x0=x-w if a=='end' else x-w/2 if a=='middle' else x
        texts.append((sh.real+x0-M,sh.imag+y-size*0.8-M,sh.real+x0+w+M,sh.imag+y+size*0.25+M,t))
    if tag=='path' and el.get('fill')=='none' and el.get('stroke') not in (None,'Canvas'):
        pp=[p+sh for p in points(el.get('d',''))]
        for a,b in zip(pp,pp[1:]):segs.append((a,b,el.get('d','')[:40]))
    if tag=='g' and el.get('id')=='nonconnecting-crossings':return
    for c in el:walk(c,sh)
walk(root)
def hit(a,b,box):
    x0,y0,x1,y1,_=box
    if max(a.real,b.real)<x0 or min(a.real,b.real)>x1 or max(a.imag,b.imag)<y0 or min(a.imag,b.imag)>y1:return False
    for k in range(0,41):
        p=a+(b-a)*k/40
        if x0<=p.real<=x1 and y0<=p.imag<=y1:return True
    return False
n=0
for bx in texts:
    for a,b,d in segs:
        if hit(a,b,bx):
            n+=1;print('%-50s x%d y%d | %s'%(bx[4][:50],bx[0],bx[1],d));break
print('text/line touches:',n)
