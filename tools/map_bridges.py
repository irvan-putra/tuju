"""Add schematic line hops at geometric crossings, never at station joins.
Only the standard library is needed, so regeneration is reproducible in CI.
"""
import math, re
import xml.etree.ElementTree as ET

def points(d):
    tokens=re.findall(r'[MLCQZmlcqz]|-?\d+(?:\.\d+)?(?:e[-+]?\d+)?',d)
    i=0; cur=0j; out=[]
    while i<len(tokens):
        cmd=tokens[i]; i+=1
        if cmd=='Z': break
        if cmd not in ('M','L','C','Q'): return []
        n={'M':2,'L':2,'C':6,'Q':4}[cmd]
        vals=list(map(float,tokens[i:i+n]));i+=n
        z=[complex(*vals[j:j+2]) for j in range(0,n,2)]
        if cmd=='M':cur=z[0];out.append(cur);continue
        steps=1 if cmd=='L' else 48
        for k in range(1,steps+1):
            t=k/steps;u=1-t
            q=z[-1] if cmd=='L' else (u*u*cur+2*u*t*z[0]+t*t*z[1] if cmd=='Q' else u**3*cur+3*u*u*t*z[0]+3*u*t*t*z[1]+t**3*z[2])
            out.append(q)
        cur=z[-1]
    return out

def cross(a,b):return a.real*b.imag-a.imag*b.real

def add_bridges(svg):
    root=ET.fromstring(svg);paths=[];nodes=[]
    def walk(el,shift=0j):
        tr=re.search(r'translate\(([-.\d]+)[ ,]+([-.\d]+)\)',el.get('transform',''))
        if tr:shift+=complex(*map(float,tr.groups()))
        if el.tag.endswith('circle'):nodes.append(shift+complex(float(el.get('cx',0)),float(el.get('cy',0))))
        if el.tag.endswith('path') and el.get('fill')=='none' and el.get('stroke') not in (None,'Canvas'):
            pp=[p+shift for p in points(el.get('d',''))]
            if len(pp)>1:paths.append((el,pp))
        for c in el:walk(c,shift)
    walk(root)
    hops=[]
    for j,(el,bp) in enumerate(paths):
        for _el,ap in paths[:j]:
            for a,b in zip(ap,ap[1:]):
                for c,d in zip(bp,bp[1:]):
                    r=b-a;s=d-c;den=cross(r,s)
                    if abs(den)<1e-6:continue
                    t=cross(c-a,s)/den;u=cross(c-a,r)/den
                    if not (-1e-8<=t<=1+1e-8 and -1e-8<=u<=1+1e-8):continue
                    q=a+t*r
                    if min(abs(q-v) for v in (ap[0],ap[-1],bp[0],bp[-1]))<25:continue
                    if any(abs(q-v)<28 for v in nodes):continue
                    if abs(den)/(abs(r)*abs(s))<.22:continue
                    if any(abs(q-v[0])<35 for v in hops):continue
                    tangent=s/abs(s);hops.append((q,tangent,el,_el))
    overlay=['<g id="nonconnecting-crossings" aria-label="Line hops: crossing only, no transfer">']
    for q,t,el,_e2 in hops:
        a=q-t*23;b=q+t*23;n=t*1j*12
        # A curved hop and opaque halo leave a visible break in the lower line.
        path=f'M {a.real:.2f} {a.imag:.2f} Q {(q+n*2).real:.2f} {(q+n*2).imag:.2f} {b.real:.2f} {b.imag:.2f}'
        # Red 4C spines stay geometrically straight. Put the gap beneath them.
        if el.get('stroke')=='#c52d36':path=f'M {a.real:.2f} {a.imag:.2f} L {b.real:.2f} {b.imag:.2f}'
        overlay.append(f'<path d="M {a.real:.2f} {a.imag:.2f} L {b.real:.2f} {b.imag:.2f}" fill="none" stroke="Canvas" stroke-width="19"/>')
        overlay.append(f'<path d="{path}" fill="none" stroke="Canvas" stroke-width="19" stroke-linecap="round"/>')
        attrs=' '.join(f'{k}="{el.get(k)}"' for k in ('stroke','stroke-width','opacity','stroke-dasharray') if el.get(k))
        overlay.append(f'<path d="{path}" fill="none" {attrs}/>')
    overlay.append('</g>')
    import os
    if os.environ.get('HOPS'):
        for q,t,el,e2 in hops:print('hop at %d,%d'%(q.real,q.imag),'OVER',el.get('d','')[:50],'| UNDER',e2.get('d','')[:50])
    print('nonconnecting crossing hops:',len(hops))
    return svg.replace('</svg>','\n'.join(overlay)+'\n</svg>')
