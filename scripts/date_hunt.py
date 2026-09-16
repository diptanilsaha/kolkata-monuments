#!/usr/bin/env python3
"""Look up undated sites on Wikipedia and pull candidate construction dates.

Prints candidates for review; it never writes anything. Accepted answers go into
overrides.json by hand, because bulk matching here is wrong far more often than
it is right.
"""
import json, pathlib, re, sys, time, urllib.parse, urllib.request

HERE = pathlib.Path(__file__).parent
CACHE = HERE / "cache"
UA = {"User-Agent": "kolkata-monuments/1.0 (diptanil.dev@gmail.com)"}
API = "https://en.wikipedia.org/w/api.php?"

BUILD = (r"built|rebuilt|erected|constructed|completed|consecrated|opened|inaugurated|founded|"
         r"established|laid out|set up|dates? (?:back )?(?:to|from)|commissioned|excavated|"
         r"foundation stone")
YEAR = re.compile(rf"(?:{BUILD})\b[^.]{{0,80}}?\b(1[5-9]\d{{2}}|20[0-2]\d)\b", re.I)

STOP = {"the", "of", "and", "a", "an", "in", "at", "kolkata", "calcutta"}


def get(params, tries=5):
    for i in range(tries):
        try:
            return json.loads(urllib.request.urlopen(
                urllib.request.Request(API + urllib.parse.urlencode(params), headers=UA), timeout=60).read())
        except Exception:
            time.sleep(3 * (i + 1))
    return {}


def cached(name, fn):
    path = CACHE / name
    if path.exists():
        return json.loads(path.read_text())
    data = fn()
    path.write_text(json.dumps(data, ensure_ascii=False))
    return data


def tokens(s):
    return {w for w in re.sub(r"[^a-z0-9 ]", " ", s.lower()).split() if w and w not in STOP}


def search(name):
    """Best-matching article titles for a site name."""
    out = []
    for q in (f"{name} Kolkata", name):
        d = get({"action": "query", "format": "json", "list": "search",
                 "srsearch": q, "srlimit": 6})
        for r in d.get("query", {}).get("search", []):
            if r["title"] not in out:
                out.append(r["title"])
        time.sleep(0.4)
        if out:
            break
    return out


def article(title):
    d = get({"action": "query", "format": "json", "redirects": 1,
             "prop": "extracts", "explaintext": 1, "titles": title})
    pages = d.get("query", {}).get("pages", {})
    if not pages:
        return ""
    return next(iter(pages.values())).get("extract", "")


def main(lo, hi):
    mon = json.loads((HERE.parent / "monuments.json").read_text())
    undated = [m for m in mon if not m["year"]]
    undated.sort(key=lambda m: m["name"])
    batch = undated[lo:hi]
    print(f"# undated {lo}–{min(hi, len(undated))} of {len(undated)}\n", flush=True)

    for m in batch:
        want = tokens(m["name"])
        titles = cached(f"wsearch_{m['id']}.json", lambda: search(m["name"]))
        pick = None
        for t in titles:
            # require real overlap between the article title and the site name
            if len(want & tokens(t)) >= max(1, len(want) // 2):
                pick = t
                break
        print(f"== {m['name']}  [{m['category']}]")
        if not pick:
            print(f"   NO MATCHING ARTICLE   (candidates: {', '.join(titles[:3]) or 'none'})\n", flush=True)
            continue
        txt = cached(f"wtext_{m['id']}.json", lambda: {"title": pick, "text": article(pick)})["text"]
        hits = list(YEAR.finditer(txt))[:3]
        print(f"   article: {pick}")
        for ym in hits:
            ctx = re.sub(r"\s+", " ", txt[max(0, ym.start() - 90): ym.end() + 35]).strip()
            print(f"   {ym.group(1)}: …{ctx}…")
        if not hits:
            print("   (article found, no construction year in it)")
        print(flush=True)
        time.sleep(0.5)


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]))
