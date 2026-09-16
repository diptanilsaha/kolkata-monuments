# The Many Calcuttas — a city in layers

An interactive map of the heritage of Kolkata and its suburbs: 247 sites, each
plotted where it stands and coloured by the era that built it.

![The map](preview.jpg)

Inspired by [The many cities of Delhi](https://kaustubh-misra.github.io/delhi-monuments/)
([source](https://github.com/kaustubh-misra/delhi-monuments)), and built on the
work of Kolkata's heritage bloggers — above all Deepanjan Ghosh's
[The Concrete Paparazzi](https://double-dolphin.blogspot.com/).
Delhi's story is told through eighteen dynasties; Kolkata is a much younger city,
so this one is told through six phases of a single city's life — from Job
Charnock's burial ground to the Art Deco cinemas of Esplanade.

## Running it

It is a static site with no build step, but the JSON is loaded with `fetch`, so
it has to be served over HTTP rather than opened from the filesystem:

```sh
python3 -m http.server 8000
# then open http://localhost:8000
```

Deploy by pushing the repository root to GitHub Pages, Netlify or any static
host. If you do, set `og:image` in `index.html` to the absolute URL of
`preview.jpg` — relative Open Graph images are not resolved by most crawlers.

## What's on the map

| | |
|---|---|
| Sites | 247 |
| With a construction date | 229 |
| With a photograph | 181 |
| With a street address | 182 |
| Statutorily protected (ASI or state) | 17 |
| With a further-reading link | 69 |
| Coverage | ~25 km from Lal Dighi, plus Achipur at 27 km |

Two ways to slice it, switched in the sidebar:

- **By era** — Early Settlement (to 1756), Company Raj (1757–1857), Imperial
  Capital (1858–1911), Late Raj & Art Deco (1912–1947), Independent India
  (1948–), and the handful nobody recorded a date for.
- **By type** (the default) — sixteen categories, from *Temple & Thakurbari* to
  *Bridge, Tower & Public Works*.

The pin's colour follows whichever grouping is active; the glyph inside it
always says what the building is.

## Where the data comes from

| Source | What it gives |
|---|---|
| [KMC graded list of heritage buildings](https://wbhc.in/files/contents/graded_list_of_heritage_buildings_grade_i_iia_iib_final.pdf) (42-page PDF) | The statutory register — 762 entries, giving the scope of what counts as heritage here and a classification of each building |
| [Wikidata](https://query.wikidata.org/) | Coordinates, construction dates, architects, architectural styles, images |
| [English Wikipedia](https://en.wikipedia.org/w/api.php) | The descriptions and lead photographs |
| [Archaeological Survey of India](https://asi.nic.in/) | The official lists of Monuments of National Importance and State Protected Monuments in West Bengal, used to verify the protected sites and their numbers |
| West Bengal Heritage Commission / Indian Railways heritage inventory | Reached through their Wikidata heritage designations |
| [double-dolphin.blogspot.com](https://double-dolphin.blogspot.com/) | Deepanjan Ghosh's [heritage index](https://double-dolphin.blogspot.com/p/blog-page_27.html), linked as further reading from 39 sites |
| OpenStreetMap | Coordinates for sites Wikidata does not carry, and the basemap the site renders on |

A site is on the map if it carries a formal heritage designation *and* has a
published coordinate, or if it is a well-known Kolkata landmark that the
statutory lists happen to miss (Fort William, Belur Math, the Botanic Garden,
the old cinema halls). Those additions are listed by name in
`scripts/curated_landmarks.txt` so you can see exactly what was added by hand.

### On further reading

39 sites link to a post on Deepanjan Ghosh's blog, which is the best sustained
piece of writing on Kolkata's buildings anywhere online. The links are taken
from his own categorised [heritage index](https://double-dolphin.blogspot.com/p/blog-page_27.html),
which names 79 buildings, and every one was checked by hand before it went into
`scripts/blog_links.json`. Title similarity alone is not enough: the blog also
has posts on the Victoria Memorial in *Lucknow*, on Gillander House on *Clive
Street*, and on the Small Causes Court on *Bankshall Street*, none of which are
the monuments whose names they resemble. `blog_index.py` re-fetches the feed and
prints candidates for review; it never adds them itself.

### On the Dalhousie Square buildings

Sixty of the 79 buildings on that index are on this map, including most of the
mercantile palaces of Dalhousie Square — the Royal Exchange, McLeod House,
Temple Chambers, Standard Life Assurance, the Treasury Building, the Dead Letter
Office — along with the Ras Baris of Chetla, Basu Bati and the Neveh Shalome
synagogue.

They were the hardest to place. Most trade under a different name today, or
under none at all: the counting house is a government office, the hotel is a
bank, the name survives only in stone over a door that now belongs to something
else. Each was matched by working from its street address rather than the name
the blog knows it by, and the address was confirmed before the pin went in. A
handful are positioned to the street rather than the building, and say so in
their record.

Nineteen of the index's buildings are still off the map — Alliance Bank of
Simla, the Chartered Bank, Peliti's, the Army & Navy Stores, the United Service
Club, Posta Rajbari among them — because nothing found for them could be
confirmed, and a pin that cannot be confirmed is worse than no pin.

### Checked against the statutory lists

Both of the ASI's published lists for West Bengal were parsed and reconciled
against the map, entry by entry.

**Monuments of National Importance: eleven of the 147 fall within 25 km of Lal
Dighi, and all eleven are here** — the six in Kolkata district (Metcalfe Hall,
St. John's Church, the Currency Building, the Asiatic Society, and the Magen
David and Beth El synagogues), Sri Mayer Ghat, Clive's House at Dum Dum, the 26
Shiva temples at Khardah, Warren Hastings' House at Barasat, and the Danish
cemetery at Serampore.

**State Protected Monuments: six in range, all here** — South Park Street
cemetery, Henry Martyn's Pagoda at Serampore, the Gourchandra and Krishnachandra
temples at Chatra, and the three tombs in St. John's churchyard. The state list
carries the churchyard both as a group (S-WB-47) and as its three named tombs;
this map follows the tombs.

Each of the seventeen carries its official number in `monument_id` and its
designation in `protection`, both shown on the card. Protected monuments are
never dropped for want of a date — the designation is itself the evidence.

Reconciling the two lists also caught an error. Wikidata places the Beth El
Synagogue 610 m from where it stands; the ASI list and OpenStreetMap agree with
each other on Pollock Street, so the coordinate was corrected. Every other ASI
site now agrees with the ASI's own coordinate to within 70 m, except Sri Mayer
Ghat at 336 m, where the two sources differ over a stretch of riverbank.

### On dates

227 of 244 sites carry a year. A site with no date is not generally carried:
English Wikipedia, Wikidata, the KMC register and the heritage blogs were all
searched for every undated entry, and 118 that none of them could date were
dropped. Two things are exempt. Hand-added sites stay, because each was put on
the map deliberately and has an account behind it. So does anything
statutorily protected, national or state — no published source gives a year for
Warren Hastings' villa at Barasat, the twenty-six Shiva temples at Khardah or
the Gourchandra temple at Chatra, and all three plainly belong here.

Dating the undated is slow work done one site at a time, because the traps are
consistent. A firm's founding date is not its building's date — McLeod & Co.
dates from 1887, Turner Morrison from 1864, Shaw Wallace from 1886, and none of
those is when the house on Clive Street or Bankshall Street went up. A museum's
opening is not the building's either: the Alipore Jail museum opened in 2022,
the jail was built in 1906. Bulk text-matching produced a confident wrong answer
nearly every time it produced one at all, so every date here was read in context
and accepted or rejected by hand, and recorded in `scripts/overrides.json`.

Reconciling against the statutory lists also turned up dates the earlier passes
had missed: Admiral Watson died in Calcutta in 1757 and Begum Johnson in 1812,
which fixes both tombs in time even though neither list records a year.

## Rebuilding the dataset

```sh
cd scripts
python3 -m venv .venv && ./.venv/bin/pip install pdfplumber
./.venv/bin/python fetch_sources.py      # downloads into scripts/cache/
./.venv/bin/python build_data.py         # writes ../monuments.json and ../eras.json
```

| File | |
|---|---|
| `fetch_sources.py` | Downloads the SPARQL results, the KMC PDF and the Wikipedia extracts into `scripts/cache/` |
| `kmc_register.py` | Parses the PDF. It has no ruling lines and its cells are vertically centred, so rows are rebuilt by anchoring on the ward number and assigning each word to its nearest anchor |
| `blog_index.py` | Fetches the blog's post index and proposes further-reading candidates for review |
| `blog_links.json` | The reviewed monument → blog post links |
| `build_data.py` | Merges the sources, picks a date, derives era and category, writes the JSON |
| `curated_landmarks.txt` | Landmarks added by hand, one per line |
| `overrides.json` | Hand-checked corrections to dates, categories and descriptions |
| `manual_sites.json` | Sites added by hand, each recording where its coordinate came from |

## Layout

```
index.html        markup and metadata
styles.css        dark sidebar, info card, responsive layout
app.js            Leaflet map, clustering, layers, search, info card
monuments.json    the dataset
eras.json         era definitions used for the layer list
scripts/          the data pipeline
```

Built with [Leaflet](https://leafletjs.com/),
[Leaflet.markercluster](https://github.com/Leaflet/Leaflet.markercluster) and
[Fuse.js](https://fusejs.io/), over OpenStreetMap tiles. No API keys, no build
step, no framework.

## Licence and credit

Map data © OpenStreetMap contributors. Descriptions are from English Wikipedia
(CC BY-SA 4.0); photographs are from Wikimedia Commons under their individual
licences, linked from each site's Wikidata record. The KMC graded list is a
public document of the Kolkata Municipal Corporation. Further-reading links
point to posts by Deepanjan Ghosh at double-dolphin.blogspot.com; only their
titles and URLs are reproduced here.
