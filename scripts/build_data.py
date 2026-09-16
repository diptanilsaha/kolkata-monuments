#!/usr/bin/env python3
"""Build ../monuments.json from the cached sources.

  Wikidata (heritage designations)   ─┐
  Wikidata (landmarks, hand-picked)  ─┼─► merge ─► date ─► era ─► category ─► JSON
  KMC graded list PDF (addresses)    ─┤
  English Wikipedia (prose + images) ─┘

Run fetch_sources.py first.  Hand corrections live in overrides.json.
"""
import collections
import difflib
import json
import math
import pathlib
import re
import urllib.parse

import blog_index
import kmc_register
from fetch_sources import wikipedia_extracts

HERE = pathlib.Path(__file__).parent
CACHE = HERE / "cache"
ROOT = HERE.parent
CENTRE = (22.5726, 88.3639)          # Lal Dighi / BBD Bagh — the city's origin point
MAX_KM = 25.0                        # the city plus its suburban ring

# ────────────────────────────── eras ──────────────────────────────
# A monument belongs to the era its fabric dates from, not the era it is used in.
ERAS = [
    ("Early Settlement", None, 1756,
     "Job Charnock's factory grows into a town on three villages: the old fort, the first churches, the first burial grounds — most of it swept away in the sack of 1756."),
    ("Company Raj", 1757, 1857,
     "After Plassey. The Palladian 'City of Palaces' of the East India Company, the Bengal Renaissance, and the merchant houses of the north."),
    ("Imperial Capital", 1858, 1911,
     "Crown rule. Calcutta as capital of British India — Gothic and Indo-Saracenic public works, museums, courts and colleges."),
    ("Late Raj & Art Deco", 1912, 1947,
     "The capital leaves for Delhi. Calcutta answers with the Victoria Memorial, Art Deco cinemas and the Howrah Bridge."),
    ("Independent India", 1948, None,
     "What the city has built, converted or memorialised since 1947."),
]
UNDATED = "Date Undetermined"
UNDATED_BLURB = "Listed heritage with no construction date on public record — most of them ordinary streets-corner buildings that outlived their builders' paperwork."

# ─────────────────────────── categories ───────────────────────────
# Checked in order against a series of haystacks; first hit wins.
CATEGORY_RULES = [
    ("Hospital & Medical",         r"hospital|medical|dispensary|asylum|infirmary|hospice|sanatorium|ayurvedic|homoeopathic"),
    ("Museum, Library & Archive",  r"museum|library|reading room|archive|art gallery|learned society|\bsociety\b|sangrahalay|saghrahalay|sangrahashala"),
    ("School, College & University", r"school|college|university|seminary|hostel|academy|vidyalaya|vidyapith|shikshalaya|shiksha|madrasa|education|institute\b"),
    ("Temple & Thakurbari",        r"hindu temple|jain temple|thakurbari|thakurbati|\btemple\b|mandir|kalibari|kali ?mandir|\bmath\b|monastery|ashram|rashmancha|pagoda|shiva|jiu\b"),
    ("Mosque & Imambara",          r"mosque|masjid|imambara|husayniyya|dargah"),
    ("Church & Chapel",            r"christian|church|cathedral|chapel|basilica|convent|mission"),
    ("Synagogue, Parsi & Chinese", r"synagogue|parsi|fire temple|chinese temple|gurdwara|sikh sangat"),
    ("Ghat & Riverfront",          r"riverfront|bathing ghat|burning ghat|\bghat\b|jetty"),
    ("Cemetery, Tomb & Crematorium", r"burial|cremation|crematorium|cemetery|graveyard|\btomb\b|mausoleum|\bgrave\b"),
    ("Theatre & Cinema",           r"theatre|theater|theatrical|cinema|movie|playhouse|opera|auditorium"),
    ("Club, Park & Sport",         r"park, waterbody|recreational|\bclub\b|\bpark\b|maidan|\bsquare\b|garden|waterbody|race course|turf|golf|stadium|\bground\b|sport|swimming|rowing|\bzoo\b|dighi|sarobar|tarag"),
    ("Government, Court & Fort",   r"\boffice\b|public institution|court|\bjail\b|prison|police|post office|government|municipal|secretariat|customs|legislature|assembly|vidhan sabha|currency|akashvani|\bmint\b|\bfort\b|arsenal|writers|\bbank\b|\bhall\b"),
    ("Memorial, Statue & Gate",    r"\bstatue\b|memorial|monument|cenotaph|obelisk|gateway|\bgate\b|\bcolumn\b|minar|dungeon"),
    ("Market, Shop & Hotel",       r"\bmarket\b|\bshop\b|bazaar|\bstore\b|bakery|restaurant|confectioner|caf[e\u00e9]|\bhotel\b|tea house|\bbank\b"),
    ("Bridge, Tower & Public Works", r"bridge|\btower\b|water tank|lighthouse|\bdock\b|\bport\b|railway|station|canal|waterworks|factory|chemical|industrial|\bmills?\b|foundry|printing|press and media|telegraph|power"),
    ("Rajbari, Mansion & House",   r"eminent personality|architectural style|moribund house|\bhouse\b|residence|\bpalace\b|rajbari|rajbati|villa|bhawan|bhavan|kutir|baganbari|apartment|mansions?\b|\bbuilding\b|\bhome\b"),
]
DEFAULT_CATEGORY = "Other Heritage"

# Wikidata instance-of values too vague to classify on — a "building" could be anything.
GENERIC_TYPES = re.compile(
    r"^(building|architectural structure|structure|real estate|place|human-made geographic feature|"
    r"tourist attraction|heritage building|historic building|cultural heritage|organization|"
    r"facility|site|landmark|complex|work)$", re.I)

# KMC criteria that describe *why* a building is listed rather than *what* it is.
WEAK_CRITERIA = re.compile(r"architectural style|eminent personality|moribund|landmark|related to establishment|freedom", re.I)

# Entries that carry a heritage tag but are not monuments of the city.
EXCLUDE_QIDS = {
    "Q75802510",   # a preserved steam locomotive
    "Q3348702",    # East Kolkata Wetlands — a Ramsar wetland, not a built monument
    "Q75738551",   # duplicate of Q986105, Howrah station
    "Q15265664",   # Wikidata coordinate error: this temple is in Tamil Nadu
}

STRONG_YEAR = r"(?:built|rebuilt|erected|constructed|completed|consecrated|opened|inaugurated|founded|established|commissioned|laid out|dates? back to)\b[^.]{0,70}?\b(1[5-9]\d{2}|20[0-2]\d)\b"
LOOSE_YEAR = r"\bin\s+(1[5-9]\d{2}|20[0-2]\d)\b"


def km_from_centre(lat, lng):
    return math.hypot((lat - CENTRE[0]) * 111.0,
                      (lng - CENTRE[1]) * 111.0 * math.cos(math.radians(CENTRE[0])))


def load_sparql(name):
    """Collapse the row-per-value SPARQL result into one record per item."""
    rows = json.loads((CACHE / name).read_text())["results"]["bindings"]
    multi = {"heritageLabel": "heritage", "typeLabel": "types",
             "styleLabel": "styles", "architectLabel": "architects"}
    single = {"image": "image", "article": "article", "inception": "inception",
              "itemDescription": "wd_description"}
    items = {}
    for row in rows:
        qid = row["item"]["value"].rsplit("/", 1)[-1]
        rec = items.setdefault(qid, {
            "qid": qid, "name": row["itemLabel"]["value"], "coord": row["coord"]["value"],
            "heritage": set(), "types": set(), "styles": set(), "architects": set(),
            "wd_description": "",
        })
        for key, field in multi.items():
            if key in row:
                rec[field].add(row[key]["value"])
        for key, field in single.items():
            if key in row:
                rec[field] = row[key]["value"]
    out = []
    for rec in items.values():
        lng, lat = map(float, re.match(r"Point\(([-\d.]+) ([-\d.]+)\)", rec.pop("coord")).groups())
        rec["lat"], rec["lng"] = round(lat, 6), round(lng, 6)
        rec["km"] = round(km_from_centre(lat, lng), 1)
        for field in ("heritage", "types", "styles", "architects"):
            rec[field] = sorted(rec[field])
        out.append(rec)
    return out


# ───────────────────────── address & ward ─────────────────────────
STOPWORDS = {"the", "of", "and", "at", "in", "s", "kolkata", "calcutta"}
WARD_RE = re.compile(r"Ward No\.?\s*(\d+)", re.I)


def load_details():
    """Wikidata's structured street address and KMC ward, per item."""
    path = CACHE / "wd_details.json"
    if not path.exists():
        return {}
    out = {}
    for row in json.loads(path.read_text())["results"]["bindings"]:
        qid = row["item"]["value"].rsplit("/", 1)[-1]
        rec = out.setdefault(qid, {})
        for key, field in (("addr", "addr"), ("houseno", "houseno"),
                           ("streetLabel", "street"), ("opened", "opened")):
            if key in row:
                rec[field] = row[key]["value"]
        if "adminLabel" in row:
            m = WARD_RE.search(row["adminLabel"]["value"])
            if m:
                rec["ward"] = m.group(1).zfill(3)
    return out


def tokens(name):
    return {w for w in re.sub(r"[^a-z0-9 ]", " ", name.lower()).split()
            if w and w not in STOPWORDS}


def match_register(items, register, details):
    """Find each item's row in the KMC graded list.

    Names in the register are written loosely — "MEDICAL COLLEGE" for what
    Wikidata calls "Medical College and Hospital, Kolkata", and several
    buildings share a name across the city. Searching the whole 762-row list by
    name alone produced confident wrong answers, so the search is confined to
    the item's own KMC ward, which cuts the candidates to a handful.
    """
    by_ward = {}
    for row in register:
        if row["name"]:
            by_ward.setdefault(row["ward"], []).append((tokens(row["name"]), row))

    for item in items:
        ward = (details.get(item["qid"]) or {}).get("ward")
        if not ward:
            continue
        want = tokens(item["name"])
        if not want:
            continue
        best, best_score = None, 0.0
        for have, row in by_ward.get(ward, []):
            if not have:
                continue
            overlap = len(want & have)
            if not overlap:
                continue
            # Reward covering the item's name; tolerate the register's extra words.
            score = overlap / len(want) + 0.35 * (overlap / len(have))
            if score > best_score:
                best, best_score = row, score
        if best and best_score >= 0.75:
            item["kmc"] = best


def address_for(item, details):
    """Wikidata's own address wins; the register is the fallback."""
    wd = details.get(item["qid"]) or {}
    if wd.get("addr"):
        return wd["addr"]
    if wd.get("street"):
        house = wd.get("houseno")
        return f"{house}, {wd['street']}" if house else wd["street"]
    kmc = (item.get("kmc") or {}).get("address", "")
    # Rows whose street name was lost in the PDF's column wrapping ("4 STREET").
    words = [w for w in re.sub(r"[^A-Za-z ]", " ", kmc).split() if len(w) > 2]
    if len(words) < 2:
        return None
    return kmc.title()


# ──────────────────────────── enrichment ──────────────────────────
def pick_year(item, extract, override):
    if "year" in override:
        return override["year"], "curated"
    inception = item.get("inception")
    if inception:
        m = re.match(r"(-?\d{1,4})-", inception)
        if m and -3000 < int(m.group(1)) <= 2030:
            return int(m.group(1)), "wikidata"
    if extract:
        for pattern in (STRONG_YEAR, LOOSE_YEAR):
            m = re.search(pattern, extract, re.I)
            if m:
                return int(m.group(1)), "wikipedia"
    return None, None


def era_for(year):
    if year is None:
        return UNDATED
    for label, lo, hi, _ in ERAS:
        if (lo is None or year >= lo) and (hi is None or year <= hi):
            return label
    return UNDATED


def category_for(item):
    """Ask the most reliable evidence first, the vaguest last."""
    criteria = (item.get("kmc") or {}).get("criteria", "")
    specific_types = [t for t in item.get("types", []) if not GENERIC_TYPES.match(t)]
    haystacks = [
        " ".join(specific_types),                            # Wikidata instance-of
        "" if WEAK_CRITERIA.search(criteria) else criteria,  # KMC's own classification
        item["name"],
        item.get("wd_description", ""),
        criteria,                                            # the vague criteria, last
    ]
    for hay in haystacks:
        hay = hay.lower().strip()
        if not hay:
            continue
        for label, pattern in CATEGORY_RULES:
            if re.search(pattern, hay):
                return label
    return DEFAULT_CATEGORY


def thumbnail(url, width=900):
    """Commons originals can be 20 MB; ask the file-path endpoint for a resized copy."""
    if not url:
        return None
    url = url.replace("http://", "https://")
    m = re.search(r"Special:FilePath/(.+)$", url)
    if not m:
        m = re.search(r"/wikipedia/commons/(?:thumb/)?[0-9a-f]/[0-9a-f]{2}/([^/]+)$", url)
        if not m:
            return url                       # a local (non-Commons) upload: leave it alone
    name = m.group(1).split("?")[0]
    return f"https://commons.wikimedia.org/wiki/Special:FilePath/{name}?width={width}"


def trim(text, limit=540):
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    cut = text[:limit]
    stop = max(cut.rfind(". "), cut.rfind("; "))
    return cut[: stop + 1] if stop > limit * 0.5 else cut.rstrip() + "…"


# Column wrapping in the PDF sometimes clips a criteria cell mid-phrase.
TRUNCATED = re.compile(r"/\s*$|\(incl\.?\s*$|\band\s*$", re.I)
# Location-column text worth quoting: it tells you where to stand.
LOCATING = re.compile(r"^(over|near|between|opposite|behind|adjacent|beside|next to|"
                      r"junction|corner|on |at |in front|off )", re.I)
ALIAS = re.compile(r"^popularly known as\s*", re.I)


ABBREVIATION = re.compile(r"^[A-Za-z](\.[A-Za-z])*\.?$")


def title_case(text):
    """Capitalise the register's shouted text without mangling B.T. Road,
    87A or Tolly's, all of which str.title() gets wrong."""
    def fix(word):
        if any(c.isdigit() for c in word) or ABBREVIATION.match(word.strip("(),")):
            return word.upper()
        return word[:1].upper() + word[1:].lower()
    return " ".join(fix(w) for w in text.split())


def describe(item, extract):
    """Wikipedia prose where it exists; otherwise say plainly what the record holds."""
    if extract:
        return trim(extract)

    bits = []
    kmc = item.get("kmc") or {}
    criteria = kmc.get("criteria", "")
    if criteria and not WEAK_CRITERIA.search(criteria) and not TRUNCATED.search(criteria):
        bits.append("Listed on the Kolkata Municipal Corporation's graded list under "
                    + title_case(criteria).replace("Incl.", "incl.") + ".")
    elif item.get("wd_description"):
        desc = item["wd_description"]
        bits.append(desc[0].upper() + desc[1:].rstrip(".") + ".")

    # The register's location column is often the only way to find an unmarked
    # building: "between 87A Cossipore Road & 87C Cossipore Road", and so on.
    where = (kmc.get("location") or "").strip().rstrip(",.")
    if where:
        if ALIAS.match(where):
            bits.append("Also recorded as " + title_case(ALIAS.sub("", where)) + ".")
        elif LOCATING.match(where):
            titled = title_case(where)
            bits.append("The register places it " + titled[0].lower() + titled[1:] + ".")

    if not bits:
        bits.append("A protected heritage structure in the Kolkata metropolitan area. "
                    "No published account of it has been indexed yet.")
    return " ".join(bits)


def main():
    overrides = json.loads((HERE / "overrides.json").read_text())
    curated = {l.strip() for l in (HERE / "curated_landmarks.txt").read_text().splitlines()
               if l.strip() and not l.startswith("#")}

    heritage = load_sparql("wd_heritage.json")
    landmarks = load_sparql("wd_notable.json")
    listed = {i["qid"] for i in heritage}
    extras = [i for i in landmarks if i["name"] in curated and i["qid"] not in listed]

    unmatched = curated - {i["name"] for i in extras} - {i["name"] for i in heritage}
    if unmatched:
        print("  ! curated names not found on Wikidata:", sorted(unmatched))

    items = [i for i in heritage + extras
             if i["km"] <= MAX_KM and i["qid"] not in EXCLUDE_QIDS]

    details = load_details()
    match_register(items, kmc_register.parse(), details)

    blog_links = blog_index.load_links()

    titles = {i["qid"]: urllib.parse.unquote(i["article"].rsplit("/", 1)[-1]).replace("_", " ")
              for i in items if i.get("article")}
    wiki = wikipedia_extracts(sorted(set(titles.values())))

    monuments = []
    for item in items:
        override = overrides.get(item["qid"], {})
        page = wiki.get(titles.get(item["qid"])) or {}
        extract = page.get("extract")
        year, year_source = pick_year(item, extract, override)
        kmc = item.get("kmc") or {}

        monuments.append({
            "id": item["qid"],
            "name": override.get("name", item["name"]),
            "lat": item["lat"],
            "lng": item["lng"],
            "era": override.get("era") or era_for(year),
            "year": year,
            "built": override.get("built") or (str(year) if year else "Date not recorded"),
            "category": override.get("category") or category_for(item),
            "description": override.get("description") or describe(item, extract),
            "styles": item["styles"],
            "architects": item["architects"],
            "address": address_for(item, details),
            "km_from_centre": item["km"],
            "image": thumbnail(override.get("image") or page.get("image") or item.get("image")),
            "wikipedia": item.get("article"),
            "wikidata": f"https://www.wikidata.org/wiki/{item['qid']}",
            "further_reading": blog_links.get(item["qid"]),
            "date_source": year_source,
        })

    monuments.sort(key=lambda m: (m["year"] is None, m["year"] or 0, m["name"]))
    (ROOT / "monuments.json").write_text(json.dumps(monuments, indent=1, ensure_ascii=False) + "\n")

    eras = [{"name": n, "from": lo, "to": hi, "blurb": b} for n, lo, hi, b in ERAS]
    eras.append({"name": UNDATED, "from": None, "to": None, "blurb": UNDATED_BLURB})
    (ROOT / "eras.json").write_text(json.dumps(eras, indent=1, ensure_ascii=False) + "\n")

    print(f"\n{len(monuments)} monuments -> ../monuments.json")
    for era in [e[0] for e in ERAS] + [UNDATED]:
        print(f"  {sum(1 for m in monuments if m['era'] == era):4}  {era}")
    print()
    for cat, n in collections.Counter(m["category"] for m in monuments).most_common():
        print(f"  {n:4}  {cat}")
    print("\nimage:", sum(1 for m in monuments if m["image"]),
          "| further reading:", sum(1 for m in monuments if m["further_reading"]),
          "| wikipedia:", sum(1 for m in monuments if m["wikipedia"]),
          "| address:", sum(1 for m in monuments if m["address"]),
          "| dated:", sum(1 for m in monuments if m["year"]))


if __name__ == "__main__":
    main()
