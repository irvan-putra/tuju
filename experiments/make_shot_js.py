#!/usr/bin/env python3
"""Build a JS file that injects an SVG (optionally re-viewBoxed) into about:blank."""
import json, re, sys
svg_path, viewbox, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
svg = open(svg_path).read()
m = re.search(r'<svg[^>]*>', svg)
tag = m.group(0)
tag = re.sub(r'viewBox="[^"]*"', f'viewBox="{viewbox}"', tag)
if 'viewBox' not in tag:
    tag = tag.replace('<svg', f'<svg viewBox="{viewbox}"', 1)
tag = re.sub(r'width="[^"]*"', 'width="390"', tag)
tag = re.sub(r'height="[^"]*"', '', tag)
inner = svg[m.end():]
doc = tag + inner
js = ("document.documentElement.style.margin='0';document.body.style.margin='0';"
      "document.body.style.background='#fff';document.body.innerHTML=" + json.dumps(doc) + ";"
      "'injected '+document.querySelectorAll('svg').length")
open(out_path, 'w').write(js)
print(out_path, len(js))
