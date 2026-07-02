# Toddler NYC Knowledge Base

A personal knowledge base of things to do with toddlers in New York City.
Claude helps maintain it by turning notes, links, and "we should check out X"
ideas into structured, cross-linked markdown pages.

## Structure

```
toddler-nyc/
  CLAUDE.md      # this file — schema and rules
  index.md       # master navigation, grouped by neighborhood, then category
  log.md         # append-only change log
  places/        # one markdown file per place or recurring activity
  guides/        # themed roundups (rainy-day, free, by-neighborhood, etc.)
  build_map.py   # regenerates map/places.js from place frontmatter
  build_boroughs.py  # regenerates map/boroughs.js (vector borough basemap)
  build_site.py  # renders the wiki into site/ for GitHub Pages
  map/           # interactive Leaflet maps (all + per-borough) + generated data
  site/          # GENERATED build output (git-ignored) — never edit by hand
  .github/workflows/pages.yml  # auto-build + deploy site to GitHub Pages on push
```

## Entry Types

- **place** — a fixed location: playground, museum, indoor play space,
  library, classroom, restaurant, store, pool, etc.
- **event** — something time-bound or recurring: a festival, a weekly story
  time, a seasonal pop-up.
- **guide** — a curated roundup that links to multiple places/events.
- **neighborhood** — an area overview linking to everything in it.

## File Naming

`{category}-{kebab-case-name}.md` in the appropriate folder.
- `places/playground-ancient-central-park.md`
- `places/museum-cmom.md`
- `places/indoor-play-kidville-ues.md`
- `guides/rainy-day.md`
- ASCII only, max 80 chars.

## Page Template (places & events)

```yaml
---
name: Children's Museum of Manhattan
type: place              # place | event | guide | neighborhood
category: museum         # playground | museum | indoor-play | library |
                         # class | restaurant | store | pool | outdoor | other
neighborhood: Upper West Side
borough: Manhattan       # Manhattan | Brooklyn | Queens | Bronx | Staten Island
age_range: "0-5"         # rough toddler-relevant range
cost: "$$"               # free | $ | $$ | $$$ | reservation
indoor: true             # true | false | both
stroller_friendly: true
nap_compatible: false    # can you swing by around nap, or is it a commit?
restroom: true
changing_table: true
tags: [hands-on, art, indoor, members]
visited: false
rating: null             # 1-5 once visited, else null
updated: 2026-06-27
verify:                  # volatile facts to confirm before relying on them
  - hours
  - admission price
---
One-line summary of why this place is good (or not) for a toddler.

## The Rundown
What it is, what a toddler actually does there, how long you'll last.

## Logistics
- **Getting there:** nearest subway, stroller/elevator notes
- **Cost:** admission, membership math, free hours/days if any
- **Food:** café on-site? can you bring snacks? nearby options
- **Facilities:** restrooms, changing tables, nursing space, stroller parking

## Tips
- Best time to go (crowds, nap timing)
- What to bring
- Pair with: nearby [place](places/...) for a fuller outing

## Relationships
- In [Upper West Side](places/neighborhood-uws.md)
- Listed in [Rainy-Day Guide](guides/rainy-day.md)

## Notes / Visit Log
- 2026-06-27 — first impressions, what worked, what didn't
```

## Behavioral Rules

- **Be honest about uncertainty.** Hours, prices, and open/closed status drift.
  Put anything volatile under `verify:` and don't state it as fact in prose.
  Prefer "stable" facts (what it is, where it is, what a toddler does there).
- **Cross-link both ways.** When linking place A → guide B, make sure B links
  back to A. Same for neighborhood pages.
- **Tags drive guides.** When adding a place, check whether it belongs in any
  existing guide (rainy-day, free, etc.) and add it there too.
- **Log every change** to `log.md` with an ISO 8601 timestamp.
- **One entity per file.** When unsure, make a new page rather than overloading.
- `confidence`-style epistemics aren't needed here — but never invent specifics
  (an address, a price) to fill a field. Leave it blank or under `verify:`.

## Adding an Entry — workflow

When asked to "add X":
1. Create `places/{category}-{slug}.md` from the template.
2. Fill in what's reliably known; route volatile facts to `verify:`.
3. Set `lat`/`lng` (approximate is fine — flag it) so it appears on the map.
4. Add it to `index.md` under its category and neighborhood.
5. Add it to any relevant guide(s), with reciprocal links.
6. Run `python3 build_map.py` to refresh `map/places.js`.
7. Append a line to `log.md`.

## The Map

Four Leaflet maps share one engine (`map/map.js` + `map/map.css`):
`map.html` (all NYC) and `manhattan.html` / `brooklyn.html` / `queens.html`
(borough-filtered), with a borough switcher. Each reads two generated JS files
(loaded as `<script>`, not fetch, so they work over file://):

- `map/places.js` — pins, from place frontmatter via `build_map.py`. Markers are
  colored by `category`; only places with numeric `lat`/`lng` appear.
- `map/boroughs.js` — a simplified **vector borough basemap** via
  `build_boroughs.py`. The map draws borough outlines itself, so it needs **no
  external map tiles** and always shows an outline.

Never edit `places.js` / `boroughs.js` by hand. Regenerate after changes:

    python3 build_map.py        # after any place add/move/delete
    python3 build_boroughs.py   # only to refresh borough geometry (rare)

## The Website (GitHub Pages)

`build_site.py` renders `index.md`, `places/`, and `guides/` into `site/` as a
styled, clickable website (place pages get a metadata card + tags + verify
callout; every page gets a Home · Map nav). It rewrites internal `.md` links to
`.html` and copies the map in. `site/` is git-ignored build output — never edit
it by hand; edit the markdown and rebuild. The Actions workflow at
`.github/workflows/pages.yml` runs `build_map.py` + `build_site.py` and deploys
to Pages on every push to `main`.

## Log Format

```
- 2026-06-27T14:30:00Z | ADD | places/museum-cmom.md (Children's Museum of Manhattan)
- 2026-06-27T14:35:00Z | UPDATE | places/playground-ancient.md — added visit notes, rating 4
- 2026-06-27T14:40:00Z | GUIDE | guides/rainy-day.md — added CMOM
```
