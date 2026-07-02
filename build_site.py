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
:root{--ink:#18181b;--muted:#71717a;--faint:#a1a1aa;--line:#e4e4e7;--line-soft:#ececee;--bg:#f7f7f8;--card:#ffffff;--accent:#4f46e5;--accent-soft:#eef2ff;}
body{margin:0;background:var(--bg);font-family:'Inter',system-ui,-apple-system,'Segoe UI',Helvetica,Arial,sans-serif;color:var(--ink);font-size:15.5px;line-height:1.65;-webkit-font-smoothing:antialiased;}
.nav{position:sticky;top:0;z-index:10;background:rgba(255,255,255,.86);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);border-bottom:1px solid var(--line);color:var(--ink);padding:12px 20px;display:flex;gap:20px;align-items:center;font-size:13.5px;font-family:'Space Grotesk','Inter',system-ui,sans-serif;}
.nav a{color:var(--ink);text-decoration:none;font-weight:500;} .nav a:hover{color:var(--accent);}
.nav .brand{font-size:15px;font-weight:700;letter-spacing:-.01em;} .nav .sp{flex:1;}
.wrap{max-width:860px;margin:0 auto;padding:28px 24px 56px;}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:36px 40px;margin-top:16px;box-shadow:0 1px 2px rgba(0,0,0,.04);}
h1,h2,h3{line-height:1.25;color:var(--ink);font-family:'Space Grotesk','Inter',system-ui,sans-serif;}
h1{font-size:30px;font-weight:700;letter-spacing:-.02em;margin-top:0;margin-bottom:.5em;}
h2{font-size:20px;font-weight:600;letter-spacing:-.01em;border-bottom:1px solid var(--line-soft);padding-bottom:.35em;margin-top:36px;}
h3{font-size:13px;font-weight:600;letter-spacing:.05em;text-transform:uppercase;color:var(--muted);margin:22px 0 8px;}
a{color:var(--accent);text-decoration:none;} a:hover{text-decoration:underline;text-underline-offset:2px;}
code{background:#f4f4f5;color:#3f3f46;padding:.12em .4em;border-radius:6px;font-size:85%;}
pre{background:#fafafa;border:1px solid var(--line-soft);padding:14px;border-radius:10px;overflow:auto;} pre code{background:none;padding:0;}
ul{padding-left:1.35em;} li{margin:.25em 0;} hr{border:none;border-top:1px solid var(--line-soft);margin:28px 0;} em{color:var(--muted);}
.meta{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px 18px;background:#fafafa;border:1px solid var(--line-soft);border-radius:12px;padding:16px 20px;margin-bottom:20px;font-size:13px;}
.meta .k{color:var(--faint);font-size:11.5px;letter-spacing:.04em;text-transform:uppercase;} .meta .v{font-weight:600;}
.pills{margin:-2px 0 18px;} .pill{display:inline-block;background:#f4f4f5;color:#52525b;border-radius:999px;padding:3px 11px;font-size:12px;font-weight:500;margin:2px 5px 2px 0;}
.title-row{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;}
.badge{font-size:11.5px;font-weight:600;letter-spacing:.03em;text-transform:uppercase;background:var(--accent-soft);color:var(--accent);border-radius:999px;padding:3px 11px;}
.verify{background:#fffbeb;border:1px solid #fde68a;border-left:3px solid #f59e0b;border-radius:10px;padding:12px 16px;margin:16px 0;font-size:13px;} .verify b{color:#92400e;}
blockquote{margin:0;padding:0 1em;color:var(--muted);border-left:3px solid var(--line);}
.borough-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:14px;margin:20px 0;}
.bcard{display:block;background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px 18px;text-decoration:none;
  box-shadow:0 1px 2px rgba(0,0,0,.04);transition:transform .12s ease,box-shadow .12s ease,border-color .12s ease;}
.bcard:hover{transform:translateY(-2px);box-shadow:0 8px 24px rgba(24,24,27,.08);border-color:var(--accent);text-decoration:none;}
.bcard .bcard-emoji{font-size:26px;line-height:1;}
.bcard .bcard-name{font-family:'Space Grotesk','Inter',system-ui,sans-serif;font-weight:600;font-size:18px;color:var(--ink);margin-top:10px;letter-spacing:-.01em;}
.bcard .bcard-sub{font-size:12.5px;color:var(--muted);margin-top:4px;line-height:1.45;}
.map-embed{width:100%;height:420px;border:1px solid var(--line);border-radius:14px;margin:12px 0;background:#fafafa;}
"""

EMOJI = {"playground":"🛝","museum":"🎨","restaurant":"🍴","library":"📚","class":"🎵",
         "indoor-play":"🏠","pool":"🏊","other":"📍","neighborhood":"📍","borough":"🗽"}

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
           f'<span class="sp"></span><span style="color:#a1a1aa;font-size:12px">{html.escape(rel)}</span></div>')
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
