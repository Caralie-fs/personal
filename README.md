# Toddler NYC 🗽🧸

A personal knowledge base of things to do with toddlers in New York City.

Playgrounds, museums, indoor play spaces, story times, classes, kid-friendly
restaurants — organized so I can quickly find "where can we go *right now*"
based on weather, neighborhood, nap schedule, and budget.

## How it works

This is a flat markdown wiki. Each **place** or **event** is one file in
`places/`. Themed **guides** (rainy-day, free, by-neighborhood) live in
`guides/`. Everything is indexed in [`index.md`](index.md).

```
toddler-nyc/
  README.md        # this file
  CLAUDE.md        # schema + rules for adding entries
  index.md         # master navigation
  log.md           # change log
  places/          # one file per place/activity
    _template.md   # copy this to start a new entry
  guides/          # themed roundups
  build_map.py     # regenerates the map data from place frontmatter
  map/             # interactive map — open map/map.html
```

## The map

Open [`map/map.html`](map/map.html) (all NYC) or the per-borough maps
[`manhattan.html`](map/manhattan.html) / [`brooklyn.html`](map/brooklyn.html) /
[`queens.html`](map/queens.html) / [`bronx.html`](map/bronx.html) / [`staten-island.html`](map/staten-island.html) — a borough switcher links between them. Every
place is pinned and colored by category, with filters and links back to each
page. After adding or moving a place, regenerate the data:

```bash
python3 build_map.py
```

The basemap is a **vector borough outline** (`map/boroughs.js`) drawn by Leaflet
itself — **no external map tiles**, so the map always shows an outline and works
fully offline. Leaflet is vendored under `map/vendor/`. The fonts (**Space Grotesk** for headings,
**Inter** for body — a clean, modern pairing) are vendored
under `assets/fonts/`, so styling works offline too — no font-CDN dependency.

## Browsable website (GitHub Pages)

The repo builds into a styled, clickable website — every page rendered with a
metadata card, tags, and a Home · Map nav bar.

Build it locally:

```bash
pip install markdown pyyaml
python3 build_map.py     # refresh map data
python3 build_site.py    # render everything into site/
# open site/index.html
```

`site/` is git-ignored — it's a build artifact. To **host it**, the included
GitHub Actions workflow (`.github/workflows/pages.yml`) rebuilds and deploys on
every push to `main`. One-time setup:

1. Push the repo to GitHub.
2. Go to **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. Push to `main` (or run the workflow manually). Your site appears at
   `https://<username>.github.io/<repo>/`.

After that, adding a place + pushing is all it takes — the site rebuilds itself.

## Adding a place

```bash
cp places/_template.md places/playground-pier-25.md
# fill in the frontmatter + notes, then add it to index.md
```

Or just tell Claude: *"add Pier 25 playground"* and it'll create the page,
fill what it knows, flag what to verify, and update the index.

## Conventions

- **Verify the volatile stuff yourself.** Hours, prices, and "is it still
  open" change constantly — entries mark these as `verify:` until confirmed.
- `visited: true` once you've actually been; add a personal `rating:` 1–5.
- Tag liberally — tags are how the guides get built.
