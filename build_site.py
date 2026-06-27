#!/usr/bin/env python3
"""Render the wiki into a static, browsable site under site/ for GitHub Pages.

- Renders index.md + everything in places/ and guides/ to styled HTML.
- Rewrites internal .md links to .html.
- Copies the map/ folder in and points its popups at the .html pages.
- Adds a Home · Map nav bar to every page.

Run locally with:  python3 build_map.py && python3 build_site.py
(The GitHub Actions workflow does this automatically on push.)

Requires: pip install markdown pyyaml
"""
import re, html, shutil
from pathlib import Path
import markdown, yaml

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"

CSS = """
*{box-sizing:border-box}
body{margin:0;background:#fdf2f7;font-family:'Nunito',system-ui,-apple-system,'Segoe UI',Helvetica,Arial,sans-serif;color:#2b2330;}
.nav{position:sticky;top:0;z-index:10;background:#c2185b;color:#fff;padding:10px 16px;display:flex;gap:18px;align-items:center;font-size:14px;font-family:'Fredoka','Nunito',system-ui,sans-serif;}
.nav a{color:#fff;text-decoration:none;font-weight:600;} .nav a:hover{color:#ffd9e8;}
.nav .brand{font-size:15px;} .nav .sp{flex:1;}
.wrap{max-width:860px;margin:0 auto;padding:24px;}
.card{background:#fff;border:1px solid #f3c6da;border-radius:12px;padding:28px 32px;margin-top:16px;box-shadow:0 2px 10px rgba(194,24,91,.06);}
h1,h2,h3{line-height:1.25;font-weight:600;color:#7a1144;font-family:'Fredoka','Nunito',system-ui,sans-serif;letter-spacing:.2px;} h1{font-size:28px;border-bottom:2px solid #f3c6da;padding-bottom:.3em;margin-top:0;}
h2{font-size:20px;border-bottom:1px solid #f3c6da;padding-bottom:.3em;margin-top:24px;} h3{font-size:16px;}
a{color:#c2185b;text-decoration:none;} a:hover{text-decoration:underline;}
code{background:#fce4ef;padding:.15em .4em;border-radius:6px;font-size:85%;}
pre{background:#fdf2f7;padding:14px;border-radius:8px;overflow:auto;} pre code{background:none;padding:0;}
ul{padding-left:1.4em;} li{margin:.2em 0;} hr{border:none;border-top:1px solid #f3c6da;margin:20px 0;} em{color:#8a6a78;}
.meta{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:6px 18px;background:#fdf2f7;border:1px solid #f3c6da;border-radius:8px;padding:14px 18px;margin-bottom:18px;font-size:13px;}
.meta .k{color:#8a6a78;} .meta .v{font-weight:600;}
.pills{margin:-2px 0 16px;} .pill{display:inline-block;background:#fce4ef;color:#c2185b;border-radius:999px;padding:2px 10px;font-size:12px;margin:2px 4px 2px 0;}
.title-row{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;}
.badge{font-size:12px;background:#ffe3f1;color:#b5176e;border-radius:999px;padding:2px 10px;}
.verify{background:#fff8c5;border:1px solid #eac54f;border-radius:8px;padding:10px 14px;margin:14px 0;font-size:13px;} .verify b{color:#7d4e00;}
blockquote{margin:0;padding:0 1em;color:#8a6a78;border-left:.25em solid #f3c6da;}
"""

EMOJI = {"playground":"🛝","museum":"🎨","restaurant":"🍴","library":"📚","class":"🎵",
         "indoor-play":"🏠","pool":"🏊","other":"📍","neighborhood":"📍"}

def split_fm(text):
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            raw = re.sub(r"\s+#.*", "", text[3:end])
            try: fm = yaml.safe_load(raw) or {}
            except Exception: fm = {}
            return fm, text[end+4:]
    return {}, text

def render_meta(fm):
    if fm.get("type") not in ("place", "event"): return ""
    order = [("category","Category"),("neighborhood","Neighborhood"),("borough","Borough"),
             ("cost","Cost"),("age_range","Ages"),("indoor","Indoor"),
             ("stroller_friendly","Stroller-friendly"),("nap_compatible","Nap-friendly"),
             ("changing_table","Changing table"),("parking","Parking")]
    rows = [f'<div><div class="k">{l}</div><div class="v">{html.escape(str(fm[k]))}</div></div>'
            for k,l in order if fm.get(k) not in (None,"",[])]
    grid = f'<div class="meta">{"".join(rows)}</div>' if rows else ""
    pills = ('<div class="pills">' + "".join(f'<span class="pill">{html.escape(str(t))}</span>'
             for t in fm["tags"]) + "</div>") if fm.get("tags") else ""
    verify = (f'<div class="verify"><b>⚠️ Verify before relying:</b> '
              + " · ".join(html.escape(str(v)) for v in fm["verify"]) + "</div>") if fm.get("verify") else ""
    return grid + pills + verify

def rewrite_links(body_html):
    return re.sub(r'href="([^":]+?)\.md(#[^"]*)?"', r'href="\1.html\2"', body_html)

def render(rel, prefix):
    fm, body = split_fm((ROOT / rel).read_text())
    title = fm.get("name") or fm.get("title") or rel
    head = ""
    if fm.get("type"):
        emoji = EMOJI.get(fm.get("category") or fm.get("type"), "")
        badge = f'<span class="badge">{html.escape(fm["type"])}</span>'
        head = f'<div class="title-row"><h1>{emoji} {html.escape(str(title))}</h1>{badge}</div>'
    body_html = rewrite_links(markdown.markdown(body, extensions=["extra","sane_lists","nl2br"]))
    nav = (f'<div class="nav"><a class="brand" href="{prefix}index.html">🗽 Toddler NYC</a>'
           f'<a href="{prefix}index.html">Home</a><a href="{prefix}map/map.html">🗺️ Map</a>'
           f'<span class="sp"></span><span style="color:#adbac7;font-size:12px">{html.escape(rel)}</span></div>')
    return (f'<!doctype html><html><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<link rel="stylesheet" href="{prefix}assets/fonts/fonts.css">'
            f'<title>{html.escape(str(title))} · Toddler NYC</title><style>{CSS}</style></head><body>'
            f'{nav}<div class="wrap"><div class="card">{head}{render_meta(fm)}{body_html}</div></div></body></html>')

def main():
    if SITE.exists(): shutil.rmtree(SITE)
    SITE.mkdir()
    pages = ["index.md"] + sorted(
        str(p.relative_to(ROOT)) for p in list((ROOT/"places").glob("*.md")) + list((ROOT/"guides").glob("*.md"))
        if p.name != "_template.md")
    for rel in pages:
        depth = rel.count("/")
        prefix = "../" * depth
        out = SITE / rel.replace(".md", ".html")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render(rel, prefix))
    # Copy vendored assets (fonts) and the map (with popups pointed at .html).
    shutil.copytree(ROOT/"assets", SITE/"assets")
    shutil.copytree(ROOT/"map", SITE/"map")
    pj = SITE/"map"/"places.js"
    pj.write_text(pj.read_text().replace('.md"', '.html"'))
    (SITE/".nojekyll").write_text("")  # serve files as-is, no Jekyll
    print(f"Built site/ with {len(pages)} pages + map.")

if __name__ == "__main__":
    main()
