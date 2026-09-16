#!/usr/bin/env python3
"""Further-reading links to Deepanjan Ghosh's Kolkata heritage blog,
double-dolphin.blogspot.com.

Only post titles and URLs are used; the writing stays on his site.

`blog_links.json` is the source of truth and every entry in it has been checked
by hand, because title similarity is not enough to establish that a post is
about a given building: the blog has a post on the Victoria Memorial in
*Lucknow*, one on Gillander House on *Clive Street*, and one on the Small Causes
Court on *Bankshall Street* — none of which are the Kolkata monuments whose
names they resemble.

Run this module directly to re-fetch the feed and propose candidates for any
monument that has no link yet; then add the good ones to blog_links.json.
"""
import html
import json
import pathlib
import re
import time
import urllib.request

HERE = pathlib.Path(__file__).parent
CACHE = HERE / "cache"
LINKS = HERE / "blog_links.json"

FEED = ("https://double-dolphin.blogspot.com/feeds/posts/summary"
        "?alt=json&max-results=100&start-index={start}")
# The author's own categorised index of Kolkata heritage buildings — far better
# for matching than post titles, because it names the buildings plainly.
HERITAGE_INDEX = "https://double-dolphin.blogspot.com/p/blog-page_27.html"
UA = {"User-Agent": "kolkata-monuments/1.0 (dataset build script)"}
CREDIT = "Deepanjan Ghosh — double-dolphin.blogspot.com"


def fetch_posts(refresh=False):
    dest = CACHE / "blog_posts.json"
    if dest.exists() and not refresh:
        return json.loads(dest.read_text())

    posts, start = [], 1
    while True:
        req = urllib.request.Request(FEED.format(start=start), headers=UA)
        feed = json.loads(urllib.request.urlopen(req, timeout=60).read())["feed"]
        entries = feed.get("entry", [])
        if not entries:
            break
        for entry in entries:
            posts.append({
                "title": entry["title"]["$t"],
                "url": next(l["href"] for l in entry["link"] if l["rel"] == "alternate"),
            })
        start += len(entries)
        total = int(feed.get("openSearch$totalResults", {}).get("$t", 0))
        if total and start > total:
            break
        time.sleep(0.5)

    CACHE.mkdir(exist_ok=True)
    dest.write_text(json.dumps(posts, indent=1, ensure_ascii=False))
    return posts


def fetch_heritage_index(refresh=False):
    """[{section, name, url}] from the blog's Kolkata heritage index page."""
    dest = CACHE / "dd_heritage_index.json"
    if dest.exists() and not refresh:
        return json.loads(dest.read_text())

    req = urllib.request.Request(HERITAGE_INDEX, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"})
    page = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
    start = page.find("post-body entry-content")
    body = page[start:page.find("post-footer", start)] if start > 0 else page
    body = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", body, flags=re.S)

    def clean(x):
        return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", x or ""))).strip()

    rows, section, seen = [], "General", set()
    # Headings are bold; entries are links. Walk them in document order.
    pattern = r'<b>(.*?)</b>|<a\s[^>]*href="([^"]+)"[^>]*>(.*?)</a>'
    for m in re.finditer(pattern, body, re.S | re.I):
        if m.group(1) is not None:
            heading = clean(m.group(1))
            if len(heading) > 3:
                section = heading
            continue
        url, label = m.group(2), clean(m.group(3))
        # The page still links to the old blogspot.in domain.
        url = url.replace("blogspot.in", "blogspot.com").replace("http://", "https://")
        if "double-dolphin.blogspot" in url and re.search(r"/20\d\d/", url) and label and url not in seen:
            seen.add(url)
            rows.append({"section": section, "name": label, "url": url})

    CACHE.mkdir(exist_ok=True)
    dest.write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    return rows


def load_links():
    """{qid: {title, url, credit}} for build_data.py."""
    if not LINKS.exists():
        return {}
    return {qid: {"title": v["title"], "url": v["url"], "credit": CREDIT}
            for qid, v in json.loads(LINKS.read_text()).items()}


# ───────────────────── candidate proposal (review aid) ─────────────────────

STOPWORDS = {"the", "of", "a", "an", "and", "in", "at", "to", "is", "was", "that",
             "kolkata", "calcutta", "forgotten", "history", "story", "part", "how",
             "why", "photo", "feature", "print"}


def keywords(text):
    return {w for w in re.sub(r"[^a-z0-9 ]", " ", text.lower()).split()
            if len(w) > 2 and w not in STOPWORDS}


def propose(monuments, posts, already):
    """Monuments whose distinctive words all appear in an index entry or post
    title. Candidates for a human to accept or reject, never a final answer."""
    indexed = [(keywords(p["title"]), p) for p in posts]
    for m in monuments:
        if m["id"] in already:
            continue
        want = keywords(m["name"])
        if len(want) < 2:
            continue
        for have, post in indexed:
            if want <= have:
                yield m, post
                break


if __name__ == "__main__":
    posts = fetch_posts()
    index = fetch_heritage_index()
    # Index entries carry the plain building name, so try them first.
    posts = [{"title": e["name"], "url": e["url"]} for e in index] + posts
    monuments = json.loads((HERE.parent / "monuments.json").read_text())
    already = load_links()
    print(f"{len(index)} index entries, {len(posts) - len(index)} posts, "
          f"{len(already)} links already reviewed\n")
    print("Unreviewed candidates (check each before adding to blog_links.json):")
    found = False
    for monument, post in propose(monuments, posts, already):
        found = True
        print(f"  {monument['id']:<12} {monument['name']}\n"
              f"               -> {post['title']}\n"
              f"                  {post['url']}")
    if not found:
        print("  (none)")
