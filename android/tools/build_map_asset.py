#!/usr/bin/env python3
"""Build the app's offline map asset from the tuju website source.

Extracts the combined "all routes at a glance" card from ../index.html:
the first <svg viewBox="0 0 (?:1700|3000|5000|4200|4600) ...> map plus the card's intro and closing
notes (they carry the route-uncertainty caveats, which must stay with the
map). The closing note is adapted for the app: the route cards live on the
website, not "below", and the map is already enlarged here.

Also bundles the journey meter page (../../meter/index.html) as assets/meter/index.html
(card, scoped style and script between the journey-meter markers): the ride timer, stop picker and optional GPS
distance. The meter runs on-device only; the app keeps no network permission.

Also extracts the IDSW access-guideline card (between the access-guideline
markers): the official venue access notes, below the meter. External links
are rewritten as plain text, because the app has no network and the asset
test forbids external URLs.

Also bundles the walk-review checklist (../../review/index.html) as
assets/review/index.html, the app's second screen: the map's review link is
rewritten to the bundled file. The review page must stay fully offline.

Usage:
    tools/build_map_asset.py           write app/src/main/assets/map.html and assets/review/index.html
    tools/build_map_asset.py --check   fail if either committed asset is stale
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SRC = os.path.join(ROOT, "..", "index.html")
OUT = os.path.join(ROOT, "app", "src", "main", "assets", "map.html")
REVIEW_SRC = os.path.join(ROOT, "..", "review", "index.html")
REVIEW_OUT = os.path.join(ROOT, "app", "src", "main", "assets", "review", "index.html")
METER_SRC = os.path.join(ROOT, "..", "meter", "index.html")
METER_OUT = os.path.join(ROOT, "app", "src", "main", "assets", "meter", "index.html")

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=12">
<title>tuju</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{ font-family: system-ui, -apple-system, sans-serif; margin: 0; line-height: 1.55; }}
  svg {{ width: 100%; height: auto; display: block; }}
  .note {{ font-size: .85rem; opacity: .8; padding: .4rem .75rem .2rem; margin: 0; }}
  .note:last-child {{ padding-bottom: .9rem; }}
  .card {{ border: 1px solid #8884; border-radius: .75rem; padding: .55rem .9rem; margin: .8rem .6rem 1rem; }}
  .card h3 {{ margin: .25rem 0 .4rem; font-size: 1rem; }}
  .card p {{ margin: .45rem 0; font-size: .9rem; }}
  .card .tag {{ font-size: .68rem; border: 1px solid #8886; border-radius: 999px; padding: .02rem .5rem; vertical-align: .1em; }}
</style>
</head>
<body>
{tabs}
{intro}
{svg}
{closing}
{reading_notes}
{editor}
{guideline}
</body>
</html>
"""


def extract_card(html):
    m = re.search(
        r'<svg viewBox="0 0 (?:1700|3000|5000|4200|4600) \d+".*?</svg>\s*'
        r'(?:<details class="mapzoom">.*?</details>\s*)?'
        r'(?:<p class="note">(?P<closing>.*?)</p>)?',
        html, re.S)
    if not m:
        sys.exit("combined map card (intro note + (?:1700|3000|5000|4200|4600)-wide svg + closing note) not found in " + SRC)
    svg = re.search(r'<svg viewBox="0 0 (?:1700|3000|5000|4200|4600) \d+".*?</svg>', m.group(0), re.S).group(0)
    closing = m.group("closing") or ""
    # The app has no route cards "below" and the map is already enlarged.
    closing = closing.replace("details and fares in the route cards below",
                              "details and fares in the route cards at vanipy.com/tuju/")
    closing = re.sub(r"\s*Small print\?.*", "", closing)
    svg = re.sub(r'<a href="https?://[^"]*">(.*?)</a>', r'\1', svg, flags=re.S)
    return "", svg, closing


def extract_reading_notes(html):
    m = re.search(r"<!-- map-reading-notes:begin -->(.*?)<!-- map-reading-notes:end -->", html, re.S)
    if not m: sys.exit("map reading notes missing")
    # Keep navigation labels readable without dead online links in the offline APK.
    return re.sub(r'<a href="https?://[^"]*">(.*?)</a>', r'\1 (directions on vanipy.com/tuju/)', m.group(1).strip(), flags=re.S)


def extract_meter(html):
    m = re.search(r"<!-- journey-meter:begin[^>]*-->(?P<meter>.*?)<!-- journey-meter:end[^>]*-->",
                  html, re.S)
    if not m:
        sys.exit("journey-meter block not found in " + SRC)
    return m.group("meter").strip()


def extract_editor(html):
    m = re.search(r"<!-- layout-editor:begin[^>]*-->(?P<editor>.*?)<!-- layout-editor:end[^>]*-->",
                  html, re.S)
    if not m:
        sys.exit("layout-editor block not found in " + SRC)
    return m.group("editor").strip()


def extract_guideline(html):
    m = re.search(r"<!-- access-guideline:begin[^>]*-->(?P<g>.*?)<!-- access-guideline:end[^>]*-->",
                  html, re.S)
    if not m:
        return ""  # IDSW access guideline removed from the page in 0.2.33
    g = m.group("g").strip()
    # Offline app: keep the source reference as text instead of a dead link.
    g = re.sub(r'<a href="https://idsw\.dev/access-guideline/">(.*?)</a>',
               r'\1 (idsw.dev/access-guideline)', g)
    if re.search(r'(?:src|href)\s*=\s*"https?://', g):
        sys.exit("access-guideline block still carries an external URL")
    return g


def app_tabs(page, prefix):
    """Point the tab bar at the bundled files (prefix is "" or "../")."""
    m = re.search(r"<!-- tuju-tabs:begin -->.*?<!-- tuju-tabs:end -->", page, re.S)
    if not m:
        sys.exit("tab bar markers missing")
    targets = {"Home": "map.html", "Meter": "meter/index.html", "Review": "review/index.html"}
    t = re.sub(r'<a href="[^"]*"( aria-current="page")?>(Home|Meter|Review)</a>',
               lambda x: '<a href="%s%s"%s>%s</a>' % (prefix, targets[x.group(2)], x.group(1) or "", x.group(2)),
               m.group(0))
    return page.replace(m.group(0), t)


def render_sub(path, name):
    with open(os.path.normpath(path), encoding="utf-8") as f:
        page = f.read()
    page = app_tabs(page, "../")
    if re.search(r'(?:src|href)\s*=\s*"https?://', page):
        sys.exit(name + " page carries an external URL; the app asset must stay offline")
    return page


def render_review():
    return render_sub(REVIEW_SRC, "review")


def render_meter():
    return render_sub(METER_SRC, "meter")


def render():
    with open(os.path.normpath(SRC), encoding="utf-8") as f:
        page = f.read()
    intro, svg, closing = extract_card(page)
    # In the app the review page is a bundled asset file, not a directory.
    intro = intro.replace('href="review/"', 'href="review/index.html"')
    return app_tabs(PAGE.format(tabs=re.search(r'<!-- tuju-tabs:begin -->.*?<!-- tuju-tabs:end -->', page, re.S).group(0),
                       intro='',
                       svg=svg,
                       closing='<p class="note">%s</p>' % closing,
                       reading_notes='',
                       guideline=extract_guideline(page),
                       editor=extract_editor(page)), "")


def main():
    page = render()
    review = render_review()
    meter = render_meter()
    if "--check" in sys.argv:
        try:
            with open(OUT, encoding="utf-8") as f:
                current = f.read()
        except OSError:
            current = None
        if current != page:
            sys.exit("map.html is stale; run tools/build_map_asset.py")
        try:
            with open(REVIEW_OUT, encoding="utf-8") as f:
                current_review = f.read()
        except OSError:
            current_review = None
        if current_review != review:
            sys.exit("review/index.html asset is stale; run tools/build_map_asset.py")
        try:
            with open(METER_OUT, encoding="utf-8") as f:
                current_meter = f.read()
        except OSError:
            current_meter = None
        if current_meter != meter:
            sys.exit("meter/index.html asset is stale; run tools/build_map_asset.py")
        print("map.html, meter and review assets are up to date")
        return
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(page)
    print("wrote", os.path.relpath(OUT, ROOT), "(%d bytes)" % len(page))
    os.makedirs(os.path.dirname(REVIEW_OUT), exist_ok=True)
    with open(REVIEW_OUT, "w", encoding="utf-8") as f:
        f.write(review)
    print("wrote", os.path.relpath(REVIEW_OUT, ROOT), "(%d bytes)" % len(review))
    os.makedirs(os.path.dirname(METER_OUT), exist_ok=True)
    with open(METER_OUT, "w", encoding="utf-8") as f:
        f.write(meter)
    print("wrote", os.path.relpath(METER_OUT, ROOT), "(%d bytes)" % len(meter))


if __name__ == "__main__":
    main()
