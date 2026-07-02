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
body{margin:0;background:var(--bg);font-family:'Inter',system-ui,-apple-system,'Segoe UI',Helvetica,Arial,sans-serif;color:var(--ink);font-size:16px;line-height:1.65;-webkit-font-smoothing:antialiased;}
.nav{position:sticky;top:0;z-index:10;background:rgba(255,255,255,.86);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);border-bottom:1px solid var(--line);color:var(--ink);padding:12px 20px;display:flex;gap:20px;align-items:center;font-size:13.5px;font-family:'Space Grotesk','Inter',system-ui,sans-serif;}
.nav a{color:var(--ink);text-decoration:none;font-weight:500;} .nav a:hover{color:var(--accent);}
.nav .brand{font-size:15px;font-weight:700;letter-spacing:-.01em;} .nav .sp{flex:1;}
.wrap{max-width:1160px;margin:0 auto;padding:30px 28px 64px;}
.card{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:40px 52px;margin-top:16px;box-shadow:0 1px 2px rgba(0,0,0,.04);}
/* Keep flowing prose readable even in the wide card; let grids/tables/media span full width. */
.card > p, .card > ul, .card > ol, .card > blockquote{max-width:78ch;}
.card table{width:100%;border-collapse:collapse;margin:16px 0;font-size:14.5px;}
.card th,.card td{text-align:left;padding:8px 12px;border-bottom:1px solid var(--line-soft);}
.card th{font-family:'Space Grotesk','Inter',system-ui,sans-serif;font-weight:600;color:var(--muted);font-size:12.5px;letter-spacing:.03em;text-transform:uppercase;}
.card tr:hover td{background:#fafafa;}
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
.borough-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin:22px 0;}
.bcard{display:block;background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px 18px;text-decoration:none;
  box-shadow:0 1px 2px rgba(0,0,0,.04);transition:transform .12s ease,box-shadow .12s ease,border-color .12s ease;}
.bcard:hover{transform:translateY(-2px);box-shadow:0 8px 24px rgba(24,24,27,.08);border-color:var(--accent);text-decoration:none;}
.bcard .bcard-emoji{font-size:26px;line-height:1;}
.bcard .bcard-name{font-family:'Space Grotesk','Inter',system-ui,sans-serif;font-weight:600;font-size:18px;color:var(--ink);margin-top:10px;letter-spacing:-.01em;}
.bcard .bcard-sub{font-size:12.5px;color:var(--muted);margin-top:4px;line-height:1.45;}
.map-embed{width:100%;height:420px;border:1px solid var(--line);border-radius:14px;margin:12px 0;background:#fafafa;}
.db-controls{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:14px 0;}
.db-controls input,.db-controls select{font:inherit;font-size:14px;padding:9px 12px;border:1px solid var(--line);border-radius:10px;background:#fff;color:var(--ink);}
.db-controls input{flex:1;min-width:220px;}
.db-controls .count{color:var(--muted);font-size:13px;margin-left:auto;font-variant-numeric:tabular-nums;}
.db-wrap{overflow-x:auto;border:1px solid var(--line);border-radius:14px;}
table.db{width:100%;border-collapse:collapse;font-size:14px;}
table.db th,table.db td{text-align:left;padding:9px 13px;border-bottom:1px solid var(--line-soft);white-space:nowrap;}
table.db td.name{white-space:normal;font-weight:600;min-width:190px;}
table.db thead th{background:#fafafa;cursor:pointer;user-select:none;font-family:'Space Grotesk','Inter',sans-serif;font-size:11.5px;letter-spacing:.03em;text-transform:uppercase;color:var(--muted);}
table.db thead th:hover{color:var(--accent);}
table.db thead th .ar{opacity:.35;font-size:9px;margin-left:3px;}
table.db tbody tr:hover td{background:#f7f7fb;}
.db-empty{padding:20px;color:var(--muted);text-align:center;}
"""

EMOJI = {"playground":"🛝","museum":"🎨","restaurant":"🍴","library":"📚","class":"🎵",
         "indoor-play":"🏠","pool":"🏊","other":"📍","neighborhood":"📍","borough":"🗽","store":"🛍️"}

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
    nav = (f'<div class="nav"><a class="brand" href="{prefix}index.html">🗽 Toddler Guide NYC</a>'
           f'<a href="{prefix}index.html">Home</a><a href="{prefix}map/map.html">🗺️ Map</a>'
           f'<span class="sp"></span><span style="color:#a1a1aa;font-size:12px">{html.escape(rel)}</span></div>')
    return (f'<!doctype html><html><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<link rel="stylesheet" href="{prefix}assets/fonts/fonts.css">'
            f'<title>{html.escape(str(title))} · Toddler Guide NYC</title><style>{CSS}</style></head><body>'
            f'{nav}<div class="wrap"><div class="card">{head}{render_meta(fm)}{body_html}</div></div></body></html>')

COST_RANK = {"free":"0","$":"1","$$":"2","$$$":"3","reservation":"2.5"}

def build_db_table():
    """A searchable, sortable, filterable table of every place — the database view."""
    rows, boroughs, cats = [], set(), set()
    for p in sorted((ROOT/"places").glob("*.md")):
        if p.name == "_template.md": continue
        fm, _ = split_fm(p.read_text())
        if fm.get("type") not in ("place", "event"): continue
        name = fm.get("name") or p.stem
        cat = fm.get("category") or "other"
        nb = fm.get("neighborhood") or ""
        boro = fm.get("borough") or ""
        cost = str(fm.get("cost") or "")
        ind = {"true":"indoor","false":"outdoor","both":"both"}.get(str(fm.get("indoor")).lower(), "")
        ages = fm.get("age_range") or ""
        tags = fm.get("tags") or []
        walk = "🏠" if "walkable" in tags else ""
        emoji = EMOJI.get(cat, "📍")
        href = "places/" + p.stem + ".html"
        search = " ".join([str(name), str(nb), str(boro), str(cat)] + [str(t) for t in tags]).lower()
        boroughs.add(boro); cats.add(cat)
        rows.append(
          f'<tr data-search="{html.escape(search)}" data-borough="{html.escape(boro)}" data-category="{html.escape(cat)}">'
          f'<td class="name"><a href="{href}">{emoji} {html.escape(str(name))}</a></td>'
          f'<td>{html.escape(cat)}</td><td>{html.escape(str(nb))}</td><td>{html.escape(str(boro))}</td>'
          f'<td data-sort="{COST_RANK.get(cost,"9")}">{html.escape(cost)}</td>'
          f'<td>{ind}</td><td>{html.escape(str(ages))}</td><td>{walk}</td></tr>')
    boro_opts = "".join(f'<option value="{html.escape(b)}">{html.escape(b)}</option>' for b in sorted(boroughs) if b)
    cat_opts = "".join(f'<option value="{html.escape(c)}">{html.escape(c)}</option>' for c in sorted(cats) if c)
    heads = ["Place","Category","Neighborhood","Borough","Cost","Indoor","Ages","🏠"]
    thead = "".join(f'<th>{h}<span class="ar">▲▼</span></th>' for h in heads)
    controls = (f'<div class="db-controls">'
      f'<input id="dbq" type="search" placeholder="Search {len(rows)} places — name, neighborhood, tag…" aria-label="Search places">'
      f'<select id="dbb" aria-label="Borough"><option value="">All boroughs</option>{boro_opts}</select>'
      f'<select id="dbc" aria-label="Category"><option value="">All categories</option>{cat_opts}</select>'
      f'<span class="count" id="dbcount">{len(rows)} places</span></div>')
    table = (f'<div class="db-wrap"><table class="db" id="dbtable"><thead><tr>{thead}</tr></thead>'
      f'<tbody>{"".join(rows)}</tbody></table><div class="db-empty" id="dbempty" style="display:none">No matches — try clearing a filter.</div></div>')
    script = ("<script>(function(){var q=document.getElementById('dbq'),bb=document.getElementById('dbb'),"
      "cc=document.getElementById('dbc'),tbl=document.getElementById('dbtable'),"
      "rows=[].slice.call(tbl.tBodies[0].rows),cnt=document.getElementById('dbcount');"
      "function apply(){var s=(q.value||'').toLowerCase().trim(),b=bb.value,c=cc.value,n=0;"
      "rows.forEach(function(r){var ok=(!s||r.dataset.search.indexOf(s)>=0)&&(!b||r.dataset.borough===b)&&(!c||r.dataset.category===c);"
      "r.style.display=ok?'':'none';if(ok)n++;});cnt.textContent=n+' place'+(n===1?'':'s');"
      "document.getElementById('dbempty').style.display=n?'none':'';}"
      "[q,bb,cc].forEach(function(e){e.addEventListener('input',apply);e.addEventListener('change',apply);});"
      "var dir={};[].slice.call(tbl.tHead.rows[0].cells).forEach(function(th,i){th.addEventListener('click',function(){"
      "dir[i]=!dir[i];var d=dir[i]?1:-1,tb=tbl.tBodies[0];"
      "rows.slice().sort(function(a,b){var x=a.cells[i].dataset.sort||a.cells[i].textContent.trim().toLowerCase(),"
      "y=b.cells[i].dataset.sort||b.cells[i].textContent.trim().toLowerCase(),nx=parseFloat(x),ny=parseFloat(y);"
      "if(!isNaN(nx)&&!isNaN(ny))return (nx-ny)*d;return x<y?-d:x>y?d:0;})"
      ".forEach(function(r){tb.appendChild(r);});});});})();</script>")
    return controls + table + script

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
        html_str = render(rel, prefix)
        if rel == "index.md":
            html_str = html_str.replace("<p>[[DATABASE_TABLE]]</p>", build_db_table())
        out.write_text(html_str)
    # Copy vendored assets (fonts) and the map (with popups pointed at .html).
    shutil.copytree(ROOT/"assets", SITE/"assets")
    shutil.copytree(ROOT/"map", SITE/"map")
    pj = SITE/"map"/"places.js"
    pj.write_text(pj.read_text().replace('.md"', '.html"'))
    (SITE/".nojekyll").write_text("")  # serve files as-is, no Jekyll
    print(f"Built site/ with {len(pages)} pages + map.")

if __name__ == "__main__":
    main()
