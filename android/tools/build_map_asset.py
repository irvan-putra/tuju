#!/usr/bin/env python3
"""Build the app's offline map asset from the tuju website source.

Extracts the combined "all routes at a glance" SVG (the first
<svg viewBox="0 0 560 ...> block in ../index.html) and wraps it in a
minimal standalone page for the app's WebView. The app shows only this
map; the route cards stay on the website.

Usage:
    tools/build_map_asset.py           write app/src/main/assets/map.html
    tools/build_map_asset.py --check   fail if the committed asset is stale
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SRC = os.path.join(ROOT, "..", "index.html")
OUT = os.path.join(ROOT, "app", "src", "main", "assets", "map.html")

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>tuju</title>
<style>
  :root { color-scheme: light dark; }
  * { box-sizing: border-box; }
  body { font-family: system-ui, -apple-system, sans-serif; margin: 0; padding: 0; }
  svg { width: 100vw; height: auto; display: block; margin: 0; }
</style>
</head>
<body>
%s
</body>
</html>
"""


def extract_svg(html):
    m = re.search(r'<svg viewBox="0 0 560 \d+".*?</svg>', html, re.S)
    if not m:
        sys.exit("no combined 560-wide map svg found in " + SRC)
    return m.group(0)


def main():
    with open(os.path.normpath(SRC), encoding="utf-8") as f:
        svg = extract_svg(f.read())
    page = PAGE % svg
    if "--check" in sys.argv:
        try:
            with open(OUT, encoding="utf-8") as f:
                current = f.read()
        except OSError:
            current = None
        if current != page:
            sys.exit("map.html is stale; run tools/build_map_asset.py")
        print("map.html is up to date")
        return
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(page)
    print("wrote", os.path.relpath(OUT, ROOT), "(%d bytes)" % len(page))


if __name__ == "__main__":
    main()
