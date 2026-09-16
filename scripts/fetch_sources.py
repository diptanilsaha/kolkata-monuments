#!/usr/bin/env python3
"""Download the raw sources used to build the Kolkata monuments dataset.

Sources
-------
1. Wikidata Query Service  - coordinates, heritage grades, inception dates, images
2. Kolkata Municipal Corporation graded list of heritage buildings (PDF, wbhc.in)
3. English Wikipedia       - intro extracts and lead images

Everything lands in ./cache/ so the build step can run offline.
"""
import json
import pathlib
import sys
import time
import urllib.parse
import urllib.request

CACHE = pathlib.Path(__file__).parent / "cache"
CACHE.mkdir(exist_ok=True)

UA = "kolkata-monuments/1.0 (https://github.com/; dataset build script)"
CENTRE = (22.5726, 88.3639)  # BBD Bagh / Dalhousie Square

WDQS = "https://query.wikidata.org/sparql"
KMC_PDF = (
    "https://wbhc.in/files/contents/"
    "graded_list_of_heritage_buildings_grade_i_iia_iib_final.pdf"
)

# Everything carrying a formal heritage designation within 32 km of the centre.
Q_HERITAGE = """
SELECT ?item ?itemLabel ?itemDescription ?coord ?heritageLabel ?inception ?typeLabel
       ?styleLabel ?architectLabel ?image ?commons ?article WHERE {
  SERVICE wikibase:around {
    ?item wdt:P625 ?coord .
    bd:serviceParam wikibase:center "Point(%f %f)"^^geo:wktLiteral .
    bd:serviceParam wikibase:radius "32" .
  }
  ?item wdt:P1435 ?heritage .
  OPTIONAL { ?item wdt:P571 ?inception }
  OPTIONAL { ?item wdt:P31 ?type }
  OPTIONAL { ?item wdt:P149 ?style }
  OPTIONAL { ?item wdt:P84 ?architect }
  OPTIONAL { ?item wdt:P18 ?image }
  OPTIONAL { ?item wdt:P373 ?commons }
  OPTIONAL { ?article schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
}""" % (CENTRE[1], CENTRE[0])

# Street address, KMC ward and opening date for everything already selected.
# P131 ("Ward No. 44, Kolkata Municipal Corporation") is what lets a monument be
# matched against the right slice of the graded list.
Q_DETAILS = """
SELECT ?item ?addr ?houseno ?streetLabel ?adminLabel ?opened WHERE {
  SERVICE wikibase:around {
    ?item wdt:P625 ?coord .
    bd:serviceParam wikibase:center "Point(%f %f)"^^geo:wktLiteral .
    bd:serviceParam wikibase:radius "32" .
  }
  { ?item wdt:P1435 [] } UNION { ?item wdt:P669 [] }
  OPTIONAL { ?item wdt:P6375 ?addr }
  OPTIONAL { ?item wdt:P670 ?houseno }
  OPTIONAL { ?item wdt:P669 ?street }
  OPTIONAL { ?item wdt:P131 ?admin }
  OPTIONAL { ?item wdt:P1619 ?opened }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
}""" % (CENTRE[1], CENTRE[0])

# Landmark-shaped things with an English Wikipedia article, used to hand-pick the
# well-known sites that never made it onto the statutory lists.
LANDMARK_CLASSES = (
    "wd:Q16970 wd:Q34627 wd:Q32815 wd:Q842402 wd:Q44539 wd:Q33506 wd:Q24354 "
    "wd:Q41176 wd:Q4989906 wd:Q5003624 wd:Q39614 wd:Q12518 wd:Q811979 wd:Q1080794 "
    "wd:Q7315155 wd:Q2072450 wd:Q3947 wd:Q751876 wd:Q207694 wd:Q7075 wd:Q3918 "
    "wd:Q9842 wd:Q11707 wd:Q22698 wd:Q174782 wd:Q2385804 wd:Q17715832 wd:Q1329623 "
    "wd:Q43229 wd:Q57660343 wd:Q1076486 wd:Q483110 wd:Q655686 wd:Q19844914 "
    "wd:Q57659536 wd:Q23413 wd:Q1244442 wd:Q1060829 wd:Q133311 wd:Q16560 wd:Q2087181"
)

Q_LANDMARKS = """
SELECT ?item ?itemLabel ?itemDescription ?coord ?typeLabel ?inception ?styleLabel
       ?architectLabel ?image ?article WHERE {
  SERVICE wikibase:around {
    ?item wdt:P625 ?coord .
    bd:serviceParam wikibase:center "Point(%f %f)"^^geo:wktLiteral .
    bd:serviceParam wikibase:radius "25" .
  }
  ?article schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> .
  ?item wdt:P31 ?type .
  VALUES ?class { %s }
  ?type wdt:P279* ?class .
  OPTIONAL { ?item wdt:P571 ?inception }
  OPTIONAL { ?item wdt:P149 ?style }
  OPTIONAL { ?item wdt:P84 ?architect }
  OPTIONAL { ?item wdt:P18 ?image }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
}""" % (CENTRE[1], CENTRE[0], LANDMARK_CLASSES)


def get(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


def sparql(query, name):
    dest = CACHE / name
    if dest.exists():
        print(f"  {name}: cached")
        return json.loads(dest.read_text())
    print(f"  {name}: querying Wikidata …")
    url = WDQS + "?" + urllib.parse.urlencode({"query": query})
    raw = get(url, headers={"Accept": "application/sparql-results+json"})
    dest.write_bytes(raw)
    return json.loads(raw)


def wikipedia_extracts(titles):
    """Intro paragraph + lead image for each article title."""
    dest = CACHE / "wikipedia.json"
    cached = json.loads(dest.read_text()) if dest.exists() else {}
    todo = [t for t in titles if not cached.get(t)]
    print(f"  wikipedia.json: {len(cached)} cached, {len(todo)} to fetch")
    for i in range(0, len(todo), 20):
        batch = todo[i : i + 20]
        params = {
            "action": "query", "format": "json", "redirects": 1,
            "prop": "extracts|pageimages", "exintro": 1, "explaintext": 1,
            "piprop": "original", "titles": "|".join(batch),
        }
        for attempt in range(5):      # the API rate-limits bursts; back off and retry
            try:
                doc = json.loads(get("https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(params)))
                break
            except Exception as exc:
                print(f"    batch {i} attempt {attempt + 1}: {exc}", file=sys.stderr)
                time.sleep(3 * (attempt + 1))
        else:
            continue
        query = doc.get("query", {})
        alias = {n["from"]: n["to"] for n in query.get("normalized", [])}
        alias.update({r["from"]: r["to"] for r in query.get("redirects", [])})
        resolved = {}
        for page in query.get("pages", {}).values():
            if "extract" in page:
                resolved[page["title"]] = {
                    "extract": page["extract"],
                    "image": page.get("original", {}).get("source"),
                }
        for title in batch:
            target = alias.get(title, title)
            cached[title] = resolved.get(target) or resolved.get(title) or None
        time.sleep(1.0)
    dest.write_text(json.dumps(cached, indent=1, ensure_ascii=False))
    return cached


def kmc_pdf():
    dest = CACHE / "wbhc.pdf"
    if not dest.exists():
        print("  wbhc.pdf: downloading …")
        dest.write_bytes(get(KMC_PDF))
    else:
        print("  wbhc.pdf: cached")
    return dest


def main():
    print("Fetching sources into", CACHE)
    sparql(Q_HERITAGE, "wd_heritage.json")
    sparql(Q_LANDMARKS, "wd_notable.json")
    sparql(Q_DETAILS, "wd_details.json")
    kmc_pdf()
    print("Done. Run build_data.py next.")


if __name__ == "__main__":
    main()
